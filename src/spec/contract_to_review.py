#!/usr/bin/env python3
"""Offline converter: fail-closed requirements-gate hardware-contract -> prototype review input.

This module projects a ``hardware-contract`` document produced by the
fail-closed requirements gate (`src/spec/requirements_gate.py`) into a
``jlceda-prototype-review-input/1.0`` object that the independent review engine
(`src/review/prototype_review.py`) can consume, closing the offline chain
"Chinese requirements -> spec -> independent review -> rating".

Fail-closed principles enforced here:

- the input must be a hardware-contract shaped JSON object (the gate output);
  anything else raises `ContractInputError` and nothing is coerced;
- information the contract does not express is either omitted from the review
  input or registered in the human-readable conversion log
  (`contract_to_review_issues`); it is never invented (no guessed coordinates,
  nets, currents, widths, packages or roles);
- the only allowed heuristics are strictly bounded: `value` is derived from a
  component name only when the name "looks like a value" (no Chinese role
  words), and `capacitanceUf` is parsed only from a name shaped exactly
  ``{number}{uF|nF|pF|F}``;
- the produced review input is re-validated with the review engine's own
  `validate_design` before being returned; a converter bug that produced an
  un-reviewable object fails loudly as `ContractInputError`;
- no timestamps are ever emitted. ``now`` is accepted for API compatibility
  with the gate only and never affects the output; ``options`` is reserved and
  currently has no effect.

Component mapping (per ``contract.components`` item):

- ``ref``     <- designator (non-empty string; null/empty entries are skipped
                 and logged, never emitted);
- ``mpn``     <- manufacturerId (only when present and non-null);
- ``value``   <- derived from ``name`` only when the name looks like a value
                 (never guessed; otherwise omitted);
- ``capacitanceUf`` <- parsed from ``name`` only for ``{number}{uF|nF|pF|F}``
                 shaped names (the single allowed heuristic);
- ``nets``    <- only when the designator matches a ``mechanical.connectorPositions``
                 name AND at least one named power domain exists: the device is
                 then a positioned interface connector and is projected onto every
                 named power-domain net (the documented task convention; all other
                 devices get no ``nets`` and are logged);
- ``x``/``y`` <- parsed from the matching ``connectorPositions`` entry's
                 ``"(x, y)"`` positionMm string; unparseable positions are
                 omitted and logged;
- ``package`` is never emitted: ``footprintUuid`` is an evidence UUID, not a
  footprint name (not guessed); ``profile`` and ``critical`` are never emitted.

Net mapping (per ``contract.powerDomains`` item):

- one review net per named power domain (declaration order; duplicate names
  raise `ContractInputError`), ``role`` mapped as ``GND``/``Ground`` ->
  ``high_current_return``, nominal voltage > 0 -> ``power``, nominal voltage == 0
  (non-GND) -> ``signal``, unknown nominal voltage -> role omitted (never
  defaulted);
- ``designCurrentA`` <- domain ``maxCurrentA`` when present (omitted and logged
  when null); ``minWidthMm`` is never emitted (the contract carries no trace
  width information).

``checks`` is a fixed, honest object: all six prototype gates are declared with
``savedReloaded: false`` because an offline conversion carries no real
save/reload persistence evidence; ``requirementsComplete`` mirrors
``contract.status`` (an extra key the review engine ignores). ``fixtureMetadata``
and ``sourceEvidence`` are fixed offline-synthesis declarations and never embed
private paths, UUIDs or identities.

Only the Python standard library is used; no third-party package is imported.
"""

from __future__ import annotations

import math
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# The review engine lives in src/review; expose it on sys.path the same way the
# repository's own scripts do, so this module is importable both from scripts
# and from the test suite without any packaging step.
_REVIEW_DIR = Path(__file__).resolve().parents[1] / "review"
if str(_REVIEW_DIR) not in sys.path:
    sys.path.insert(0, str(_REVIEW_DIR))

from prototype_review import InputValidationError, validate_design  # noqa: E402

REVIEW_INPUT_SCHEMA = "jlceda-prototype-review-input/1.0"
CONVERTER_VERSION = "contract-to-review-input/1.0"

# Top-level keys the hardware-contract schema marks as required; a contract is
# only accepted when it satisfies this shape (fail-closed: a non-contract object
# is rejected loudly instead of being partially interpreted).
_CONTRACT_REQUIRED_TOP_LEVEL = (
    "schemaVersion",
    "kind",
    "status",
    "generatedAt",
    "sourceSnapshot",
    "board",
    "components",
    "signals",
    "interfaces",
    "powerDomains",
    "constraints",
    "approvals",
    "unresolved",
)

_HARDWARE_CONTRACT_KIND = "hardware-contract"
_REQUIREMENTS_COMPLETE_STATUS = "requirements-complete"

_GND_NET_NAMES = ("GND", "Ground")

# Chinese role words that disqualify a component name from being treated as a
# plain value; "等角色词" (role words and similar) per the task specification.
_VALUE_ROLE_WORDS = (
    "连接器",
    "模块",
    "驱动",
    "稳压",
    "电容",
    "电阻",
    "电感",
    "插座",
    "接口",
    "按键",
    "开关",
    "主控",
    "传感器",
    "天线",
    "晶振",
)

# Full-match value-shaped capacitance names only: {digits}[.{digits}] then a
# unit. Anything else (Chinese text, trailing words, bare designators) is not
# parsed (never guessed).
_CAPACITANCE_RE = re.compile(r"^([0-9]+(?:\.[0-9]+)?)\s*(uF|nF|pF|F)$", re.IGNORECASE)
_CAPACITANCE_EXPONENT = {"uf": 0, "nf": -3, "pf": -6, "f": 6}

# Documented connector position format: "(x, y)" with optional sign/space; only
# plain decimal numbers are accepted. Unparseable strings are omitted, never
# coerced.
_POSITION_RE = re.compile(r"^\s*\(\s*(-?[0-9]+(?:\.[0-9]+)?)\s*,\s*(-?[0-9]+(?:\.[0-9]+)?)\s*\)\s*$")

_CJK_AND_SPACE_RE = re.compile(r"[一-鿿\s]+")


class ContractInputError(ValueError):
    """Raised when the input is not a usable fail-closed hardware contract."""


def _optional_string(value: Any, label: str) -> str | None:
    """Accept a string or null; any other type is a hard error (fail-closed)."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ContractInputError(f"{label} must be a JSON string or null, got {type(value).__name__}")
    return value


def _optional_number(value: Any, label: str) -> float | None:
    """Accept a finite JSON number or null; booleans/strings are hard errors."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractInputError(f"{label} must be a finite JSON number or null, got {type(value).__name__}")
    number = float(value)
    if not math.isfinite(number):
        raise ContractInputError(f"{label} must be a finite JSON number or null")
    return number


def _validate_contract_shape(contract: Any) -> None:
    """Reject anything that is not a hardware-contract shaped JSON object."""
    if not isinstance(contract, dict):
        raise ContractInputError("contract must be a JSON object (hardware-contract)")
    for key in _CONTRACT_REQUIRED_TOP_LEVEL:
        if key not in contract:
            raise ContractInputError(f"contract is missing required key {key!r} (hardware-contract schema)")
    if contract.get("kind") != _HARDWARE_CONTRACT_KIND:
        raise ContractInputError(
            f"contract.kind must be {_HARDWARE_CONTRACT_KIND!r}, got {contract.get('kind')!r}"
        )
    for key in ("schemaVersion", "generatedAt", "sourceSnapshot", "status"):
        if not isinstance(contract.get(key), str):
            raise ContractInputError(f"contract.{key} must be a JSON string")
    for key in ("board", "approvals"):
        if not isinstance(contract.get(key), dict):
            raise ContractInputError(f"contract.{key} must be a JSON object")
    for key in ("components", "signals", "interfaces", "powerDomains", "constraints", "unresolved"):
        if not isinstance(contract.get(key), list):
            raise ContractInputError(f"contract.{key} must be a JSON array")
    components = contract["components"]
    if not components:
        raise ContractInputError("contract.components must not be empty")
    for index, item in enumerate(components):
        if not isinstance(item, dict):
            raise ContractInputError(f"contract.components[{index}] must be a JSON object")
    for index, item in enumerate(contract["powerDomains"]):
        if not isinstance(item, dict):
            raise ContractInputError(f"contract.powerDomains[{index}] must be a JSON object")
    for index, item in enumerate(contract["constraints"]):
        if not isinstance(item, dict):
            raise ContractInputError(f"contract.constraints[{index}] must be a JSON object")


def _validate_option_values(options: Any, now: Any) -> None:
    """Validate the reserved API-compatible parameters without using them."""
    if options is not None and not isinstance(options, dict):
        raise ContractInputError("options must be a JSON object or None")
    if now is None or isinstance(now, datetime):
        return
    if isinstance(now, str):
        try:
            datetime.fromisoformat(now)
        except ValueError as exc:
            raise ContractInputError(f"now must be an ISO 8601 datetime, got {now!r}") from exc
        return
    raise ContractInputError(
        f"now must be an ISO 8601 datetime string, a datetime instance, or None, got {type(now).__name__}"
    )


def _parse_position_mm(value: Any) -> tuple[float, float] | None:
    """Parse a "(x, y)" positionMm string into numeric coordinates.

    Returns None when the value is not a string or does not match the documented
    format; nothing is coerced.
    """
    if not isinstance(value, str):
        return None
    match = _POSITION_RE.match(value)
    if match is None:
        return None
    return (float(match.group(1)), float(match.group(2)))


def _collect_positions(contract: dict[str, Any], issues: list[str]) -> dict[str, tuple[float, float]]:
    """Collect parseable ``(name -> (x, y))`` positions from mechanical constraints.

    Positions with a missing name or an unparseable positionMm are logged and
    ignored; duplicate names with identical coordinates are deduplicated, while
    duplicate names with conflicting coordinates are a hard error (the converter
    must not silently pick one).
    """
    positions: dict[str, tuple[float, float]] = {}
    for index, constraint in enumerate(contract["constraints"]):
        if constraint.get("kind") != "mechanical":
            continue
        raw = constraint.get("connectorPositions")
        if raw is None:
            continue
        if not isinstance(raw, list):
            raise ContractInputError(
                f"contract.constraints[{index}].connectorPositions must be a JSON array or null"
            )
        for entry_index, entry in enumerate(raw):
            if not isinstance(entry, dict):
                raise ContractInputError(
                    f"contract.constraints[{index}].connectorPositions[{entry_index}] must be a JSON object"
                )
            name = entry.get("name")
            if not isinstance(name, str) or not name.strip():
                issues.append(
                    f"mechanical:connectorPositions[{index}][{entry_index}]:缺少名称(name),已忽略"
                )
                continue
            parsed = _parse_position_mm(entry.get("positionMm"))
            if parsed is None:
                issues.append(
                    f"mechanical:connectorPositions:{name}:坐标无法解析(positionMm={entry.get('positionMm')!r}),已忽略"
                )
                continue
            if name in positions:
                if positions[name] != parsed:
                    raise ContractInputError(
                        f"contract.mechanical.connectorPositions name {name!r} declared twice with conflicting coordinates"
                    )
                continue
            positions[name] = parsed
    return positions


def _net_role(name: str, nominal_voltage_v: float | None) -> str | None:
    """Map a power-domain name/voltage to a review net role, never guessing."""
    if name in _GND_NET_NAMES:
        return "high_current_return"
    if nominal_voltage_v is not None:
        if nominal_voltage_v > 0:
            return "power"
        if nominal_voltage_v == 0:
            return "signal"
    return None


def _derive_value(name: str | None) -> str | None:
    """Derive a review ``value`` from a component name only when it looks like one.

    The name must contain no Chinese role words and must keep a non-empty
    remainder after Chinese characters and whitespace are removed. Anything
    uncertain is omitted (never guessed).
    """
    if not isinstance(name, str):
        return None
    if any(word in name for word in _VALUE_ROLE_WORDS):
        return None
    remainder = _CJK_AND_SPACE_RE.sub("", name)
    if not remainder:
        return None
    return name


def _parse_capacitance_uf(name: str | None) -> float | None:
    """Parse a capacitance in microfarads from a value-shaped name only.

    The only allowed heuristic: the whole name must match
    ``{number}{uF|nF|pF|F}`` (case-insensitive). Anything else returns None.
    """
    if not isinstance(name, str):
        return None
    match = _CAPACITANCE_RE.fullmatch(name.strip())
    if match is None:
        return None
    digits = match.group(1)
    exponent = _CAPACITANCE_EXPONENT[match.group(2).lower()]
    # Build the float from its decimal representation so "100nF" parses to the
    # exact double of 0.1 instead of accumulating multiplication noise.
    return float(f"{digits}e{exponent}")


def _component_label(component: dict[str, Any], index: int) -> str:
    return component.get("name") or f"组件#{index + 1}"


def _build_design(contract: dict[str, Any], issues: list[str]) -> dict[str, Any]:
    board = contract.get("board") or {}
    design_name = board.get("projectName") or board.get("boardName")
    if not (isinstance(design_name, str) and design_name.strip()):
        design_name = "未命名设计(离线硬件需求)"
        issues.append("design:缺少设计名称(board.projectName/boardName),使用占位名")

    positions = _collect_positions(contract, issues)

    # ---- nets from powerDomains ----
    net_rows: list[dict[str, Any]] = []
    domain_names: list[str] = []
    for index, domain in enumerate(contract["powerDomains"]):
        name = _optional_string(domain.get("name"), f"contract.powerDomains[{index}].name")
        if not name:
            issues.append(f"powerDomain:#{index + 1}:缺少域名,未生成对应net")
            continue
        if name in domain_names:
            raise ContractInputError(f"contract.powerDomains declares net name {name!r} more than once")
        nominal_voltage_v = _optional_number(
            domain.get("nominalVoltageV"), f"contract.powerDomains[{index}].nominalVoltageV"
        )
        max_current_a = _optional_number(
            domain.get("maxCurrentA"), f"contract.powerDomains[{index}].maxCurrentA"
        )
        if max_current_a is None:
            issues.append(f"powerDomain:{name}:缺少最大电流(maxCurrentA),designCurrentA已省略")
        row: dict[str, Any] = {"name": name}
        role = _net_role(name, nominal_voltage_v)
        if role is not None:
            row["role"] = role
        if max_current_a is not None:
            row["designCurrentA"] = max_current_a
        net_rows.append(row)
        domain_names.append(name)

    # ---- components ----
    review_components: list[dict[str, Any]] = []
    consumed_positions: set[str] = set()
    emitted_refs: set[str] = set()
    for index, component in enumerate(contract["components"]):
        label = _component_label(component, index)
        designator = _optional_string(
            component.get("designator"), f"contract.components[{index}].designator"
        )
        if not designator:
            issues.append(f"component:{label}:缺少设计位号(designator),已省略该条目")
            continue
        if designator in emitted_refs:
            raise ContractInputError(f"contract.components duplicate designator: {designator!r}")
        emitted_refs.add(designator)
        name = _optional_string(component.get("name"), f"contract.components[{index}].name")
        manufacturer_id = _optional_string(
            component.get("manufacturerId"), f"contract.components[{index}].manufacturerId"
        )

        row: dict[str, Any] = {"ref": designator}
        if manufacturer_id:
            row["mpn"] = manufacturer_id
        value = _derive_value(name)
        if value is not None:
            row["value"] = value
        capacitance_uf = _parse_capacitance_uf(name)
        if capacitance_uf is not None:
            row["capacitanceUf"] = capacitance_uf

        position = positions.get(designator)
        if position is not None:
            consumed_positions.add(designator)
            row["x"], row["y"] = position
            if domain_names:
                row["nets"] = list(domain_names)
            else:
                issues.append(
                    f"component:{designator}:缺少可用的电源域网络(未命名powerDomains),nets已省略"
                )
        else:
            issues.append(f"component:{designator}:缺少可用的机械坐标(connectorPositions),已省略")
            issues.append(f"component:{designator}:缺少器件级网络连接信息(nets),已省略")
        review_components.append(row)

    for position_name in sorted(set(positions) - consumed_positions):
        issues.append(
            f"mechanical:connectorPositions:{position_name}:未匹配到组件(designator),已忽略"
        )

    checks: dict[str, Any] = {
        "schematicErrors": 0,
        "schematicWarnings": 0,
        "pcbDrcFindings": 0,
        "unroutedNets": 0,
        "containment": True,
        "savedReloaded": False,
        "requirementsComplete": contract.get("status") == _REQUIREMENTS_COMPLETE_STATUS,
    }
    fixture_metadata = {
        "liveEdaVerified": False,
        "persistenceEvidenceIncluded": False,
        "notForManufacturing": True,
        "source": "requirements-gate-offline",
        "converter": CONVERTER_VERSION,
        "executionStatus": (
            "offline; synthesized from the requirements gate hardware contract; "
            "no live EDA access and no save/reload persistence evidence"
        ),
    }
    return {
        "schema": REVIEW_INPUT_SCHEMA,
        "designName": design_name,
        "components": review_components,
        "nets": net_rows,
        "checks": checks,
        "fixtureMetadata": fixture_metadata,
        "sourceEvidence": ["requirements gate hardware-contract (offline, synthesized)"],
    }


def _convert(contract: Any, options: Any, now: Any) -> tuple[dict[str, Any], list[str]]:
    """Validate, convert, and re-validate the produced review input, fail-closed."""
    _validate_contract_shape(contract)
    _validate_option_values(options, now)
    issues: list[str] = []
    design = _build_design(contract, issues)
    try:
        validate_design(design)
    except InputValidationError as exc:
        raise ContractInputError(
            f"converter output failed the review engine's own validation: {exc}"
        ) from exc
    return design, issues


def contract_to_review_input(contract: Any, *, options: Any = None, now: Any = None) -> dict[str, Any]:
    """Convert a requirements-gate hardware contract into a prototype review input.

    Returns only the ``jlceda-prototype-review-input/1.0`` mapping. The
    human-readable conversion log (skipped/unmapped/omitted items) is available
    separately through :func:`contract_to_review_issues`; both functions are pure
    and deterministic given the same contract, so calling either one never
    mutates the input or depends on call order.

    ``options`` is reserved for future tuning and currently has no effect (it
    must be a JSON object or None). ``now`` is accepted for API compatibility
    with the requirements gate but never affects the output: no timestamps are
    emitted.

    Raises `ContractInputError` when ``contract`` is not a hardware-contract
    shaped object (including an empty ``components`` array) or when the produced
    review input would not pass the review engine's own `validate_design`.
    """
    design, _issues = _convert(contract, options, now)
    return design


def contract_to_review_issues(contract: Any, *, options: Any = None, now: Any = None) -> list[str]:
    """Return the human-readable conversion log for a hardware contract.

    One entry per skipped/unmapped/omitted fact, e.g.
    ``"component:J1:缺少器件级网络连接信息(nets),已省略"``. Raises
    `ContractInputError` for the same invalid inputs as
    :func:`contract_to_review_input`.
    """
    _design, issues = _convert(contract, options, now)
    return issues
