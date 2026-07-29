#!/usr/bin/env python3
"""Validate a sanitized, read-only EDA adapter evidence envelope."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any


ADAPTER_SCHEMA = "pcb-prototype-quality-gate-readonly-adapter/1.0"
HEX64 = re.compile(r"^[a-f0-9]{64}$")
ERROR_CLASSES = {
    "adapter_unavailable",
    "no_window",
    "target_ambiguous",
    "target_drift",
    "timeout_unknown",
    "upstream_5xx",
    "malformed_response",
    "incomplete_evidence",
    "digest_mismatch",
    "unsupported_document",
    "internal_error",
}


class AdapterContractError(ValueError):
    """Raised when an adapter envelope cannot be trusted for review."""


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AdapterContractError(f"{label} must be an object")
    return value


def _exact_keys(value: dict[str, Any], required: set[str], label: str) -> None:
    missing = sorted(required - set(value))
    extra = sorted(set(value) - required)
    if missing or extra:
        raise AdapterContractError(f"{label} keys mismatch; missing={missing}, extra={extra}")


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AdapterContractError(f"{label} must be a non-empty string")
    return value


def _hex64(value: Any, label: str) -> str:
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        raise AdapterContractError(f"{label} must be a lowercase SHA-256 hex digest")
    return value


def _utc_timestamp(value: Any, label: str) -> str:
    text = _text(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AdapterContractError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise AdapterContractError(f"{label} must include a timezone")
    return text


def normalized_design_sha256(design: Any) -> str:
    try:
        payload = json.dumps(
            design,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AdapterContractError("normalizedDesign is not canonical JSON") from exc
    return hashlib.sha256(payload).hexdigest()


def _validate_error_rows(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise AdapterContractError("errors must be an array")
    rows: list[dict[str, str]] = []
    for index, raw in enumerate(value):
        row = _object(raw, f"errors[{index}]")
        _exact_keys(row, {"class", "message"}, f"errors[{index}]")
        error_class = _text(row["class"], f"errors[{index}].class")
        if error_class not in ERROR_CLASSES:
            raise AdapterContractError(f"errors[{index}].class is unsupported")
        rows.append({"class": error_class, "message": _text(row["message"], f"errors[{index}].message")})
    return rows


def validate_adapter_envelope(value: Any, *, require_complete: bool = True) -> dict[str, Any]:
    envelope = _object(value, "adapterEnvelope")
    _exact_keys(envelope, {"schema", "status", "adapter", "capture", "normalizedDesign", "errors"}, "adapterEnvelope")
    if envelope["schema"] != ADAPTER_SCHEMA:
        raise AdapterContractError(f"adapterEnvelope.schema must be {ADAPTER_SCHEMA}")
    if envelope["status"] not in {"complete", "failed", "unknown"}:
        raise AdapterContractError("adapterEnvelope.status must be complete, failed or unknown")

    adapter = _object(envelope["adapter"], "adapter")
    _exact_keys(adapter, {"name", "version", "readOnly", "edaWrites"}, "adapter")
    _text(adapter["name"], "adapter.name")
    _text(adapter["version"], "adapter.version")
    if adapter["readOnly"] is not True:
        raise AdapterContractError("adapter.readOnly must be true")
    if type(adapter["edaWrites"]) is not int or adapter["edaWrites"] != 0:
        raise AdapterContractError("adapter.edaWrites must be integer zero")

    errors = _validate_error_rows(envelope["errors"])
    status = envelope["status"]
    if status != "complete":
        if not errors:
            raise AdapterContractError("failed or unknown adapter envelope must include a classified error")
        if envelope["capture"] is not None:
            raise AdapterContractError("failed or unknown adapter envelope must not include partial capture evidence")
        if envelope["normalizedDesign"] is not None:
            raise AdapterContractError("failed or unknown adapter envelope must not include normalizedDesign")
        if require_complete:
            raise AdapterContractError(f"adapter evidence status is {status}: {errors[0]['class']}")
        return envelope
    if errors:
        raise AdapterContractError("complete adapter envelope must have no errors")

    capture = _object(envelope["capture"], "capture")
    _exact_keys(capture, {"capturedAt", "target", "state", "persistence"}, "capture")
    _utc_timestamp(capture["capturedAt"], "capture.capturedAt")

    target = _object(capture["target"], "capture.target")
    _exact_keys(target, {"projectKeySha256", "schematicKeySha256", "pcbKeySha256"}, "capture.target")
    for key in ("projectKeySha256", "schematicKeySha256", "pcbKeySha256"):
        _hex64(target[key], f"capture.target.{key}")

    state = _object(capture["state"], "capture.state")
    _exact_keys(state, {"schematicStateSha256", "pcbStateSha256", "normalizedDesignSha256"}, "capture.state")
    for key in ("schematicStateSha256", "pcbStateSha256", "normalizedDesignSha256"):
        _hex64(state[key], f"capture.state.{key}")

    persistence = _object(capture["persistence"], "capture.persistence")
    _exact_keys(persistence, {"savedReloaded", "independentReadback", "targetStable"}, "capture.persistence")
    for key in ("savedReloaded", "independentReadback", "targetStable"):
        if persistence[key] is not True:
            raise AdapterContractError(f"capture.persistence.{key} must be true")

    design = _object(envelope["normalizedDesign"], "normalizedDesign")
    actual_design_sha = normalized_design_sha256(design)
    if state["normalizedDesignSha256"] != actual_design_sha:
        raise AdapterContractError("capture.state.normalizedDesignSha256 does not match normalizedDesign")
    checks = _object(design.get("checks"), "normalizedDesign.checks")
    if checks.get("savedReloaded") is not True:
        raise AdapterContractError("normalizedDesign.checks.savedReloaded must agree with persistence evidence")
    return envelope


def adapter_summary(envelope: dict[str, Any]) -> dict[str, Any]:
    """Return the public-safe binding fields for a pipeline receipt."""
    return {
        "schema": envelope["schema"],
        "status": envelope["status"],
        "adapter": dict(envelope["adapter"]),
        "capturedAt": envelope["capture"]["capturedAt"],
        "target": dict(envelope["capture"]["target"]),
        "state": dict(envelope["capture"]["state"]),
        "persistence": dict(envelope["capture"]["persistence"]),
    }
