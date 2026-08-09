#!/usr/bin/env python3
"""Offline fail-closed requirements gate: ordinary-language needs to a structured hardware contract.

This is the most upstream step of the automatic design loop. It accepts a JSON
"requirements input" (user needs plus available materials), validates it
against `schemas/requirements-input.schema.json` using a small standard-library
JSON Schema subset validator, and converts it into a `hardware-contract` shaped
document with `status` equal to ``requirements-complete`` or
``requirements-incomplete``.

Fail-closed principles enforced here:

- schema-invalid input raises `RequirementsInputError`; nothing is coerced;
- physical contradictions (inverted voltage ranges, nominal voltage outside the
  declared range, duplicate/conflicting voltage domains, a module current
  demand above its own rating, total module current above the supply capacity,
  a module/interface referencing a voltage domain the power input does not
  declare) raise `ContractViolationError`;
- missing information never becomes "zero" or a default: every required fact
  that cannot be expressed is registered as a human-readable entry in the
  ``unresolved`` list;
- every emitted component/signal/power-domain is ``approved: false`` until a
  human confirms it;
- this module generates no executable or manufacturable content and performs
  no EDA access.

Only the Python standard library is used; no third-party package is imported
to perform validation.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIREMENTS_INPUT_KIND = "jlceda-requirements-input/1.0"
HARDWARE_CONTRACT_KIND = "hardware-contract"
HARDWARE_CONTRACT_SCHEMA_VERSION = "1.0.0"
STATUS_COMPLETE = "requirements-complete"
STATUS_INCOMPLETE = "requirements-incomplete"

DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "requirements-input.schema.json"
DEFAULT_HARDWARE_CONTRACT_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "hardware-contract.schema.json"

# JSON Schema keywords this validator knows how to enforce. Any other keyword
# in a schema node is treated as unsupported and rejected so nothing is
# silently ignored (fail-closed validation).
_SUPPORTED_SCHEMA_KEYWORDS = frozenset({
    # Annotation keywords that carry no validation semantics; accepted but not enforced.
    "$schema",
    "$id",
    "title",
    "description",
    "default",
    "examples",
    "format",  # annotation-only in JSON Schema unless format-assertion is enabled
    # Constraint keywords this validator actually enforces.
    "type",
    "const",
    "enum",
    "properties",
    "required",
    "additionalProperties",
    "items",
    "minLength",
    "maxLength",
    "pattern",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "minItems",
    "maxItems",
    "uniqueItems",
})

_JSON_TYPES = frozenset({"null", "boolean", "object", "array", "number", "integer", "string"})


class RequirementsInputError(ValueError):
    """Raised when the requirements input does not conform to its schema."""


class ContractViolationError(ValueError):
    """Raised when requirements facts are physically contradictory."""


def _reject_nonstandard_json_constant(value: str) -> Any:
    raise RequirementsInputError(f"non-standard JSON numeric constant is not allowed: {value}")


def read_json(path: Path) -> Any:
    return json.loads(
        Path(path).read_text(encoding="utf-8-sig"),
        parse_constant=_reject_nonstandard_json_constant,
    )


def write_json(path: Path, value: Any) -> None:
    """Write JSON atomically: a temp file in the same directory, then os.replace.

    A failed write never leaves a partial output file at the destination.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    descriptor, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    raise RequirementsInputError(f"value {value!r} is not representable in JSON")


def _type_matches(actual: str, allowed: list[str]) -> bool:
    # JSON Schema treats "number" as also matching integers.
    return actual in allowed or (actual == "integer" and "number" in allowed)


def _is_numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_against_schema(value: Any, schema: Any, path: str) -> None:
    """Recursively validate ``value`` against a JSON Schema subset, fail-closed.

    Raises `RequirementsInputError` on the first violation. Unsupported schema
    keywords are rejected rather than ignored.
    """
    if not isinstance(schema, dict):
        raise RequirementsInputError(f"{path}: invalid schema node (expected object)")
    unknown = sorted(set(schema) - _SUPPORTED_SCHEMA_KEYWORDS)
    if unknown:
        raise RequirementsInputError(f"{path}: unsupported schema keyword(s): {', '.join(unknown)}")

    if "type" in schema:
        raw = schema["type"]
        allowed = [raw] if isinstance(raw, str) else list(raw)
        for entry in allowed:
            if entry not in _JSON_TYPES:
                raise RequirementsInputError(f"{path}: invalid schema type {entry!r}")
        actual = _json_type(value)
        if not _type_matches(actual, allowed):
            raise RequirementsInputError(
                f"{path}: expected type {raw!r}, got {actual!r} ({value!r})"
            )

    if "const" in schema and value != schema["const"]:
        raise RequirementsInputError(f"{path}: expected constant {schema['const']!r}, got {value!r}")

    if "enum" in schema and value not in schema["enum"]:
        raise RequirementsInputError(f"{path}: value {value!r} is not one of {schema['enum']!r}")

    if isinstance(value, dict):
        properties = schema.get("properties")
        for required_key in schema.get("required", []):
            if required_key not in value:
                raise RequirementsInputError(f"{path}: missing required property {required_key!r}")
        if properties is not None:
            if not isinstance(properties, dict):
                raise RequirementsInputError(f"{path}: schema properties must be an object")
            for key, sub in properties.items():
                if key in value:
                    _validate_against_schema(value[key], sub, f"{path}.{key}")
        additional = schema.get("additionalProperties")
        if additional is False:
            extra = [key for key in value if properties is None or key not in properties]
            if extra:
                raise RequirementsInputError(
                    f"{path}: additional properties are not allowed: {extra!r}"
                )
        elif isinstance(additional, dict):
            for key, item in value.items():
                if properties is None or key not in properties:
                    _validate_against_schema(item, additional, f"{path}.{key}")

    if isinstance(value, list):
        if "items" in schema:
            for index, item in enumerate(value):
                _validate_against_schema(item, schema["items"], f"{path}[{index}]")
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise RequirementsInputError(f"{path}: expected at least {schema['minItems']} items, got {len(value)}")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise RequirementsInputError(f"{path}: expected at most {schema['maxItems']} items, got {len(value)}")
        if schema.get("uniqueItems") is True:
            seen: list[Any] = []
            for item in value:
                if item in seen:
                    raise RequirementsInputError(f"{path}: items must be unique, duplicate {item!r}")
                seen.append(item)

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise RequirementsInputError(f"{path}: string shorter than minLength {schema['minLength']}")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise RequirementsInputError(f"{path}: string longer than maxLength {schema['maxLength']}")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise RequirementsInputError(f"{path}: string does not match pattern {schema['pattern']!r}")

    if _is_numeric(value):
        number = float(value)
        if not math.isfinite(number):
            raise RequirementsInputError(f"{path}: value must be a finite JSON number, got {value!r}")
        if "minimum" in schema and number < schema["minimum"]:
            raise RequirementsInputError(f"{path}: value {number:g} must be >= {schema['minimum']:g}")
        if "maximum" in schema and number > schema["maximum"]:
            raise RequirementsInputError(f"{path}: value {number:g} must be <= {schema['maximum']:g}")
        if "exclusiveMinimum" in schema and number <= schema["exclusiveMinimum"]:
            raise RequirementsInputError(f"{path}: value {number:g} must be > {schema['exclusiveMinimum']:g}")
        if "exclusiveMaximum" in schema and number >= schema["exclusiveMaximum"]:
            raise RequirementsInputError(f"{path}: value {number:g} must be < {schema['exclusiveMaximum']:g}")


def load_input_schema(path: Path | None = None) -> dict[str, Any]:
    """Load the requirements-input JSON Schema (default repository schema)."""
    schema_path = Path(path) if path is not None else DEFAULT_SCHEMA_PATH
    if not schema_path.is_file():
        raise RequirementsInputError(f"requirements-input schema not found: {schema_path}")
    try:
        return json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RequirementsInputError(f"could not read requirements-input schema: {exc}") from exc


def validate_requirements_input(value: Any, schema_path: Path | None = None) -> dict[str, Any]:
    """Validate ``value`` against the requirements-input schema, fail-closed.

    Returns the (unchanged) validated mapping on success; raises
    `RequirementsInputError` otherwise.
    """
    schema = load_input_schema(schema_path)
    _validate_against_schema(value, schema, "requirements")
    if not isinstance(value, dict):
        raise RequirementsInputError("requirements input must be a JSON object")
    return value


def load_hardware_contract_schema(path: Path | None = None) -> dict[str, Any]:
    """Load the hardware-contract JSON Schema used for the output self-check."""
    schema_path = Path(path) if path is not None else DEFAULT_HARDWARE_CONTRACT_SCHEMA_PATH
    if not schema_path.is_file():
        raise RequirementsInputError(f"hardware-contract schema not found: {schema_path}")
    try:
        return json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RequirementsInputError(f"could not read hardware-contract schema: {exc}") from exc


def _self_check_output_contract(contract: dict[str, Any], schema_path: Path | None = None) -> None:
    """Validate the gate output against the public hardware-contract schema, fail-closed.

    Uses the same lightweight validator as the input. If the schema ever gains a
    keyword this validator does not support, the check refuses loudly rather
    than skipping the affected sub-schema.
    """
    schema = load_hardware_contract_schema(schema_path)
    try:
        _validate_against_schema(contract, schema, "contract")
    except RequirementsInputError as exc:
        raise RequirementsInputError(f"gate output failed hardware-contract self-check: {exc}") from exc


def _canonical_json(value: dict[str, Any]) -> bytes:
    """Stable canonical bytes used for sourceSnapshot, placeholder identity and tests."""
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _source_snapshot(value: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(value)).hexdigest()


def _placeholder_project_uuid(value: dict[str, Any]) -> str:
    """Deterministic placeholder identity derived from the input content.

    The real project UUID is assigned when the design opens in the EDA; this
    placeholder keeps the hardware contract valid and reproducible without
    pretending to know the real project identity.
    """
    digest = hashlib.sha256(_canonical_json(value)).hexdigest()
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"jlceda:requirements:{digest}"))


def _coerce_now(now: Any) -> str:
    """Normalize ``now`` to a stable ISO 8601 string, fail-closed."""
    if now is None:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(now, datetime):
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        return now.isoformat()
    if isinstance(now, str):
        try:
            datetime.fromisoformat(now)
        except ValueError as exc:
            raise RequirementsInputError(f"now must be an ISO 8601 datetime, got {now!r}") from exc
        return now
    raise RequirementsInputError(
        f"now must be an ISO 8601 datetime string or a datetime instance, got {type(now).__name__}"
    )


def _module_key(module: dict[str, Any], index: int) -> str:
    return module.get("id") or module.get("name") or f"模块#{index + 1}"


def _material_key(material: dict[str, Any], index: int) -> str:
    return material.get("partNumber") or material.get("forModule") or f"材料#{index + 1}"


def _declared_domain_names(power: dict[str, Any]) -> list[str]:
    domains = power.get("voltageDomains")
    if not isinstance(domains, list):
        return []
    return [domain.get("name") for domain in domains if isinstance(domain, dict) and domain.get("name") is not None]


def _resolve_module_target(
    target: str | None, modules: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Match a material ``forModule`` reference by module id first, then display name."""
    if target is None:
        return None
    for module in modules:
        if module.get("id") == target:
            return module
    for module in modules:
        if module.get("name") == target:
            return module
    return None


def _check_contradictions(data: dict[str, Any]) -> None:
    """Reject physically contradictory requirements facts, fail-closed."""
    power = data.get("powerInput")
    power = power if isinstance(power, dict) else {}

    minimum_v = power.get("minVoltageV")
    maximum_v = power.get("maxVoltageV")
    nominal_v = power.get("nominalVoltageV")
    if minimum_v is not None and maximum_v is not None and maximum_v < minimum_v:
        raise ContractViolationError(
            f"powerInput.maxVoltageV ({maximum_v:g}V) must be >= minVoltageV ({minimum_v:g}V): 电压范围倒置"
        )
    if nominal_v is not None:
        if minimum_v is not None and nominal_v < minimum_v:
            raise ContractViolationError(
                f"powerInput.nominalVoltageV ({nominal_v:g}V) is below minVoltageV ({minimum_v:g}V)"
            )
        if maximum_v is not None and nominal_v > maximum_v:
            raise ContractViolationError(
                f"powerInput.nominalVoltageV ({nominal_v:g}V) is above maxVoltageV ({maximum_v:g}V)"
            )

    domains = power.get("voltageDomains")
    seen_domains: dict[str, dict[str, Any]] = {}
    if isinstance(domains, list):
        for index, domain in enumerate(domains):
            if not isinstance(domain, dict):
                raise RequirementsInputError(f"powerInput.voltageDomains[{index}] must be a JSON object")
            name = domain.get("name")
            if name is None:
                continue
            dmin = domain.get("minVoltageV")
            dmax = domain.get("maxVoltageV")
            dnom = domain.get("nominalVoltageV")
            if dmin is not None and dmax is not None and dmax < dmin:
                raise ContractViolationError(
                    f"powerInput.voltageDomains[{index}] maxVoltageV ({dmax:g}V) must be >= minVoltageV ({dmin:g}V)"
                )
            if dnom is not None:
                if dmin is not None and dnom < dmin:
                    raise ContractViolationError(f"voltage domain {name!r} nominal voltage is below its minimum")
                if dmax is not None and dnom > dmax:
                    raise ContractViolationError(f"voltage domain {name!r} nominal voltage is above its maximum")
            if name in seen_domains:
                previous = seen_domains[name]
                if (
                    previous.get("nominalVoltageV") != domain.get("nominalVoltageV")
                    or previous.get("minVoltageV") != domain.get("minVoltageV")
                    or previous.get("maxVoltageV") != domain.get("maxVoltageV")
                    or previous.get("maxCurrentA") != domain.get("maxCurrentA")
                ):
                    raise ContractViolationError(
                        f"voltage domain {name!r} is declared twice with conflicting definitions: 电压域冲突"
                    )
            else:
                seen_domains[name] = domain

    declared_names = list(seen_domains)

    modules = data.get("functionModules")
    if isinstance(modules, list):
        capacity = power.get("maxCurrentA")
        for index, module in enumerate(modules):
            if not isinstance(module, dict):
                raise RequirementsInputError(f"functionModules[{index}] must be a JSON object")
            key = _module_key(module, index)
            domain = module.get("voltageDomain")
            if domain is not None and declared_names and domain not in declared_names:
                raise ContractViolationError(
                    f"module {key!r} references voltage domain {domain!r} which the power input does not declare: 电压域冲突"
                )
            need = module.get("maxCurrentA")
            rated = module.get("ratedCurrentA")
            if need is not None and rated is not None and need > rated:
                raise ContractViolationError(
                    f"module {key!r} requires {need:g}A which exceeds its rated limit {rated:g}A: 电流需求超模块规格上限"
                )
            if need is not None and domain is not None and domain in seen_domains:
                domain_budget = seen_domains[domain].get("maxCurrentA")
                if domain_budget is not None and need > domain_budget:
                    raise ContractViolationError(
                        f"module {key!r} requires {need:g}A which exceeds voltage domain {domain!r} capacity ({domain_budget:g}A): 电流需求超电压域上限"
                    )
        if capacity is not None:
            known_total = sum(
                float(module["maxCurrentA"])
                for module in modules
                if isinstance(module, dict) and module.get("maxCurrentA") is not None
            )
            if known_total > capacity:
                raise ContractViolationError(
                    f"sum of module current requirements ({known_total:g}A) exceeds power capacity ({capacity:g}A)"
                )

    interfaces = data.get("interfaceRequirements")
    if isinstance(interfaces, list):
        for index, iface in enumerate(interfaces):
            if not isinstance(iface, dict):
                raise RequirementsInputError(f"interfaceRequirements[{index}] must be a JSON object")
            domain = iface.get("voltageDomain")
            if domain is not None and declared_names and domain not in declared_names:
                raise ContractViolationError(
                    f"interface {iface.get('name') or f'#{index + 1}'!r} references voltage domain {domain!r} which the power input does not declare: 电压域冲突"
                )
            signals = iface.get("signals")
            if isinstance(signals, list):
                for signal in signals:
                    if isinstance(signal, dict) and signal.get("voltageDomain") is not None:
                        signal_domain = signal["voltageDomain"]
                        if declared_names and signal_domain not in declared_names:
                            raise ContractViolationError(
                                f"signal {signal.get('name') or '?'!r} references voltage domain {signal_domain!r} which the power input does not declare: 电压域冲突"
                            )

    materials = data.get("providedMaterials")
    if isinstance(materials, list):
        for index, material in enumerate(materials):
            if not isinstance(material, dict):
                raise RequirementsInputError(f"providedMaterials[{index}] must be a JSON object")
            target = material.get("forModule")
            linked = _resolve_module_target(target, modules or []) if target is not None else None
            if linked is None:
                continue
            for field in ("manufacturerId", "supplierId", "footprintUuid"):
                module_value = linked.get(field)
                material_value = material.get(field)
                if module_value is not None and material_value is not None and module_value != material_value:
                    raise ContractViolationError(
                        f"material {_material_key(material, index)!r} and module {target!r} disagree on {field}"
                    )


def _uses_named_domains(power: dict[str, Any]) -> bool:
    domains = power.get("voltageDomains")
    return isinstance(domains, list) and bool(domains)


def _unresolved_for_power(power: dict[str, Any], unresolved: list[str]) -> None:
    if not power:
        unresolved.append("power:缺少电源输入规格(powerInput)")
        unresolved.append("power:缺少标称输入电压(nominalVoltageV)")
        unresolved.append("power:缺少最低输入电压(minVoltageV)")
        unresolved.append("power:缺少最高输入电压(maxVoltageV)")
        unresolved.append("power:缺少电源最大电流(maxCurrentA)")
        return
    if not _uses_named_domains(power):
        if power.get("nominalVoltageV") is None:
            unresolved.append("power:缺少标称输入电压(nominalVoltageV)")
        if power.get("minVoltageV") is None:
            unresolved.append("power:缺少最低输入电压(minVoltageV)")
        if power.get("maxVoltageV") is None:
            unresolved.append("power:缺少最高输入电压(maxVoltageV)")
    # The system current budget is always a required fact, even when named
    # voltage domains carry their own per-domain current.
    if power.get("maxCurrentA") is None:
        unresolved.append("power:缺少电源最大电流(maxCurrentA)")


def gate_requirements_to_contract(requirements: Any, now: Any = None) -> dict[str, Any]:
    """Convert validated requirements facts into a fail-closed hardware contract.

    Returns a hardware-contract shaped mapping with status
    ``requirements-complete`` (when ``unresolved`` is empty) or
    ``requirements-incomplete``. Raises `RequirementsInputError` for
    schema-invalid input and `ContractViolationError` for physical
    contradictions; it never fills defaults or treats missing facts as none.
    """
    data = validate_requirements_input(requirements)
    _check_contradictions(data)
    generated_at = _coerce_now(now)
    unresolved: list[str] = []

    def _add_unresolved(entry: str) -> None:
        unresolved.append(entry)

    description = data.get("description")
    if description is None:
        _add_unresolved("goal:缺少目标描述(description)")

    power = data.get("powerInput")
    power = power if isinstance(power, dict) else {}
    _unresolved_for_power(power, unresolved)

    modules = data.get("functionModules")
    module_list = modules if isinstance(modules, list) else []
    if not module_list:
        _add_unresolved("modules:缺少功能模块清单(functionModules)")

    interfaces = data.get("interfaceRequirements")
    if interfaces is None:
        _add_unresolved("interfaces:缺少接口需求(interfaceRequirements)")

    criteria = data.get("acceptanceCriteria")
    if not criteria:
        _add_unresolved("goal:缺少最小成功标准(acceptanceCriteria)")

    materials = data.get("providedMaterials")
    material_list = materials if isinstance(materials, list) else []

    modules_by_key: dict[str, dict[str, Any]] = {}
    for index, module in enumerate(module_list):
        if not isinstance(module, dict):
            raise RequirementsInputError(f"functionModules[{index}] must be a JSON object")
        modules_by_key[_module_key(module, index)] = module

    # ---- resolve materials to module keys (by id first, then by display name) ----
    material_groups: dict[str, list[dict[str, Any]]] = {}
    unattached_materials: list[tuple[int, dict[str, Any]]] = []
    for index, material in enumerate(material_list):
        if not isinstance(material, dict):
            raise RequirementsInputError(f"providedMaterials[{index}] must be a JSON object")
        target = material.get("forModule")
        linked = _resolve_module_target(target, module_list) if target is not None else None
        if linked is None:
            unattached_materials.append((index, material))
            if target is not None:
                _add_unresolved(f"material:{_material_key(material, index)}:forModule 引用不存在的模块 {target!r}")
            continue
        for module_key, module in modules_by_key.items():
            if module is linked:
                material_groups.setdefault(module_key, []).append(material)
                break

    # ---- named voltage domains declared by the power input (for module checks) ----
    declared_domains: dict[str, dict[str, Any]] = {}
    raw_domains = power.get("voltageDomains")
    if isinstance(raw_domains, list):
        for item in raw_domains:
            if isinstance(item, dict) and item.get("name") is not None:
                declared_domains[item["name"]] = item

    # ---- components (one entry per function module) ----
    components: list[dict[str, Any]] = []
    constraints: list[dict[str, Any]] = []
    for index, module in enumerate(module_list):
        key = _module_key(module, index)
        if module.get("name") is None and module.get("preferredPart") is None:
            _add_unresolved(f"component:{key}:缺少模块名称/型号(name)")
        if module.get("role") is None:
            _add_unresolved(f"component:{key}:缺少模块角色(role)")
        if module.get("voltageDomain") is None:
            _add_unresolved(f"component:{key}:缺少电压域(voltageDomain)")
        else:
            # Independently registered: the module's own missing current and its
            # referenced domain's missing current are two separate facts.
            referenced_domain = module.get("voltageDomain")
            if referenced_domain in declared_domains and declared_domains[referenced_domain].get("maxCurrentA") is None:
                _add_unresolved(f"powerDomain:{referenced_domain}:缺少最大电流(maxCurrentA)")
        if module.get("requiredSignals") is None:
            _add_unresolved(f"component:{key}:缺少所需信号数(requiredSignals)")
        if module.get("maxCurrentA") is None:
            _add_unresolved(f"module:{key}:缺少额定电流maxCurrentA")
        elif module.get("ratedCurrentA") is None:
            _add_unresolved(f"component:{key}:缺少器件规格电流上限(ratedCurrentA)")
        resolved_evidence = {
            field: module.get(field)
            for field in ("manufacturerId", "supplierId", "footprintUuid")
        }
        for material in material_groups.get(key, []):
            for field in ("manufacturerId", "supplierId", "footprintUuid"):
                if resolved_evidence[field] is None and material.get(field) is not None:
                    resolved_evidence[field] = material[field]
        for field, label in (
            ("manufacturerId", "制造商ID"),
            ("supplierId", "供应商ID"),
            ("footprintUuid", "封装证据"),
        ):
            if resolved_evidence[field] is None:
                _add_unresolved(f"component:{key}:缺少{label}({field})")
        name = module.get("preferredPart") or module.get("name")
        if name is None:
            for material in material_groups.get(key, []):
                if material.get("partNumber"):
                    name = material["partNumber"]
                    break
        components.append({
            "designator": module.get("designator"),
            "name": name,
            "manufacturerId": resolved_evidence["manufacturerId"],
            "supplierId": resolved_evidence["supplierId"],
            "footprintUuid": resolved_evidence["footprintUuid"],
            "approved": False,
        })
        if module.get("role") is not None:
            constraints.append({
                "kind": "module-role",
                "module": key,
                "role": module["role"],
                "approved": False,
            })
        if module.get("requiredSignals") is not None:
            constraints.append({
                "kind": "required-signals",
                "module": key,
                "count": module["requiredSignals"],
                "approved": False,
            })

    # ---- materials that are not attached to a module become their own components ----
    for index, material in unattached_materials:
        name = material.get("partNumber")
        if name is None:
            _add_unresolved(f"material:{_material_key(material, index)}:缺少器件型号(partNumber)")
        for field, label in (
            ("manufacturerId", "制造商ID"),
            ("supplierId", "供应商ID"),
            ("footprintUuid", "封装证据"),
        ):
            if material.get(field) is None:
                _add_unresolved(f"material:{_material_key(material, index)}:缺少{label}({field})")
        components.append({
            "designator": None,
            "name": name,
            "manufacturerId": material.get("manufacturerId"),
            "supplierId": material.get("supplierId"),
            "footprintUuid": material.get("footprintUuid"),
            "approved": False,
        })

    # ---- power domains ----
    power_domains: list[dict[str, Any]] = []
    domains = power.get("voltageDomains")
    if isinstance(domains, list) and domains:
        emitted_domains: set[tuple[Any, ...]] = set()
        for index, domain in enumerate(domains):
            if not isinstance(domain, dict):
                raise RequirementsInputError(f"powerInput.voltageDomains[{index}] must be a JSON object")
            name = domain.get("name")
            label = name if name is not None else f"#{index + 1}"
            if name is None:
                _add_unresolved(f"powerDomain:{label}:缺少域名称(name)")
            if domain.get("nominalVoltageV") is None:
                _add_unresolved(f"powerDomain:{label}:缺少标称电压(nominalVoltageV)")
            if domain.get("minVoltageV") is None:
                _add_unresolved(f"powerDomain:{label}:缺少最低电压(minVoltageV)")
            if domain.get("maxVoltageV") is None:
                _add_unresolved(f"powerDomain:{label}:缺少最高电压(maxVoltageV)")
            duplicate_key = (
                name,
                domain.get("nominalVoltageV"),
                domain.get("minVoltageV"),
                domain.get("maxVoltageV"),
                domain.get("maxCurrentA"),
            )
            if duplicate_key in emitted_domains:
                continue  # exact duplicate already rejected when conflicting; emit once
            emitted_domains.add(duplicate_key)
            power_domains.append({
                "name": name,
                "nominalVoltageV": domain.get("nominalVoltageV"),
                "minVoltageV": domain.get("minVoltageV"),
                "maxVoltageV": domain.get("maxVoltageV"),
                "maxCurrentA": domain.get("maxCurrentA"),
                "approved": False,
            })
    elif power:
        name = power.get("domainName")
        if name is None:
            _add_unresolved("power:缺少电源域名称(domainName)")
        power_domains.append({
            "name": name,
            "nominalVoltageV": power.get("nominalVoltageV"),
            "minVoltageV": power.get("minVoltageV"),
            "maxVoltageV": power.get("maxVoltageV"),
            "maxCurrentA": power.get("maxCurrentA"),
            "approved": False,
        })

    capacity = power.get("maxCurrentA")
    if capacity is not None:
        constraints.append({"kind": "power-budget", "maxCurrentA": capacity, "approved": False})

    if criteria:
        constraints.append({"kind": "acceptance-criteria", "criteria": list(criteria), "approved": False})

    mechanical = data.get("mechanical")
    if isinstance(mechanical, dict) and mechanical:
        constraints.append({
            "kind": "mechanical",
            "boardSizeMm": mechanical.get("boardSizeMm"),
            "connectorPositions": mechanical.get("connectorPositions"),
            "notes": mechanical.get("notes"),
            "approved": False,
        })

    # ---- signals from interface requirements ----
    signals: list[dict[str, Any]] = []
    interface_summaries: list[dict[str, Any]] = []
    if interfaces is not None:
        for index, iface in enumerate(interfaces):
            if not isinstance(iface, dict):
                raise RequirementsInputError(f"interfaceRequirements[{index}] must be a JSON object")
            key = iface.get("name") or f"接口#{index + 1}"
            if iface.get("name") is None:
                _add_unresolved(f"interface:{key}:缺少接口名称(name)")
            if iface.get("direction") is None:
                _add_unresolved(f"interface:{key}:缺少信号方向(direction)")
            if iface.get("voltageDomain") is None:
                _add_unresolved(f"interface:{key}:缺少电压域(voltageDomain)")
            raw_signals = iface.get("signals")
            if not isinstance(raw_signals, list) or not raw_signals:
                _add_unresolved(f"interface:{key}:缺少信号清单(signals)")
                emitted_names: list[str] = []
            else:
                emitted_names = []
                for signal in raw_signals:
                    if not isinstance(signal, dict):
                        raise RequirementsInputError(
                            f"interfaceRequirements[{index}].signals item must be a JSON object"
                        )
                    name = signal.get("name")
                    if name is None:
                        _add_unresolved(f"signal:{key}:缺少信号名(name)")
                        continue
                    mcu_pin = signal.get("mcuPin")
                    direction = signal.get("direction")
                    if direction is None:
                        direction = iface.get("direction")
                    voltage_domain = signal.get("voltageDomain")
                    if voltage_domain is None:
                        voltage_domain = iface.get("voltageDomain")
                    if mcu_pin is None:
                        _add_unresolved(f"signal:{name}:缺少MCU管脚(mcuPin)")
                    if direction is None:
                        _add_unresolved(f"signal:{name}:缺少方向(direction)")
                    if voltage_domain is None:
                        _add_unresolved(f"signal:{name}:缺少电压域(voltageDomain)")
                    emitted_names.append(name)
                    signals.append({
                        "name": name,
                        "mcuPin": mcu_pin,
                        "direction": direction,
                        "activeLevel": signal.get("activeLevel"),
                        "voltageDomain": voltage_domain,
                        "approved": False,
                    })
            interface_summaries.append({
                "name": iface.get("name"),
                "direction": iface.get("direction"),
                "voltageDomain": iface.get("voltageDomain"),
                "signals": emitted_names,
            })

    sorted_unresolved = sorted(set(unresolved))
    status = STATUS_COMPLETE if not sorted_unresolved else STATUS_INCOMPLETE
    contract = {
        "schemaVersion": HARDWARE_CONTRACT_SCHEMA_VERSION,
        "kind": HARDWARE_CONTRACT_KIND,
        "status": status,
        "generatedAt": generated_at,
        "sourceSnapshot": _source_snapshot(data),
        "board": {
            "projectUuid": _placeholder_project_uuid(data),
            "projectName": description,
            "boardName": description,
            "schematicUuid": None,
            "pcbUuid": None,
        },
        "components": components,
        "signals": signals,
        "interfaces": interface_summaries,
        "powerDomains": power_domains,
        "constraints": constraints,
        "approvals": {
            "componentSelection": False,
            "pinMap": False,
            "electricalRules": False,
            "firmwareBinding": False,
        },
        "unresolved": sorted_unresolved,
    }
    _self_check_output_contract(contract)
    return contract
