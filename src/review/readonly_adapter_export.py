#!/usr/bin/env python3
"""Assemble a fail-closed read-only adapter envelope from explicit evidence files.

This module is deliberately offline. It does not discover EDA windows, call a
Gateway, or infer any target/state facts. A live environment adapter must first
capture those facts and write the sanitized capture JSON consumed here.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from prototype_review import sanitize_public_value
from readonly_adapter_contract import (
    AdapterContractError,
    normalized_design_sha256,
    validate_adapter_envelope,
)


ADAPTER_SCHEMA = "pcb-prototype-quality-gate-readonly-adapter/1.0"


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AdapterContractError(f"{label} must be an object")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AdapterContractError(f"{label} must be a non-empty string")
    return value


def _strict_keys(value: dict[str, Any], required: set[str], label: str) -> None:
    missing = sorted(required - set(value))
    extra = sorted(set(value) - required)
    if missing or extra:
        raise AdapterContractError(f"{label} keys mismatch; missing={missing}, extra={extra}")


def _adapter(name: str, version: str) -> dict[str, Any]:
    return {
        "name": _text(name, "adapter.name"),
        "version": _text(version, "adapter.version"),
        "readOnly": True,
        "edaWrites": 0,
    }


def _capture_without_design_digest(capture: Any) -> dict[str, Any]:
    """Validate and copy capture facts while reserving the derived design digest."""
    source = _object(capture, "capture")
    _strict_keys(source, {"capturedAt", "target", "state", "persistence"}, "capture")
    target = _object(source["target"], "capture.target")
    _strict_keys(target, {"projectKeySha256", "schematicKeySha256", "pcbKeySha256"}, "capture.target")
    state = _object(source["state"], "capture.state")
    _strict_keys(state, {"schematicStateSha256", "pcbStateSha256"}, "capture.state")
    persistence = _object(source["persistence"], "capture.persistence")
    _strict_keys(persistence, {"savedReloaded", "independentReadback", "targetStable"}, "capture.persistence")
    return {
        "capturedAt": _text(source["capturedAt"], "capture.capturedAt"),
        "target": deepcopy(target),
        "state": {
            "schematicStateSha256": state["schematicStateSha256"],
            "pcbStateSha256": state["pcbStateSha256"],
        },
        "persistence": deepcopy(persistence),
    }


def build_complete_envelope(
    design: Any,
    capture: Any,
    *,
    adapter_name: str,
    adapter_version: str,
) -> dict[str, Any]:
    """Build and validate a complete envelope from explicit read-only evidence."""
    sanitized_design = sanitize_public_value(deepcopy(design))
    normalized_design = _object(sanitized_design, "normalizedDesign")
    captured = _capture_without_design_digest(capture)
    captured["state"]["normalizedDesignSha256"] = normalized_design_sha256(normalized_design)
    envelope = {
        "schema": ADAPTER_SCHEMA,
        "status": "complete",
        "adapter": _adapter(adapter_name, adapter_version),
        "capture": captured,
        "normalizedDesign": normalized_design,
        "errors": [],
    }
    return validate_adapter_envelope(envelope)


def build_failure_envelope(
    status: str,
    error_class: str,
    message: str,
    *,
    adapter_name: str,
    adapter_version: str,
) -> dict[str, Any]:
    """Build and validate a failed/unknown envelope without partial evidence."""
    if status not in {"failed", "unknown"}:
        raise AdapterContractError("failure status must be failed or unknown")
    envelope = {
        "schema": ADAPTER_SCHEMA,
        "status": status,
        "adapter": _adapter(adapter_name, adapter_version),
        "capture": None,
        "normalizedDesign": None,
        "errors": [{"class": _text(error_class, "errors[0].class"), "message": _text(message, "errors[0].message")}],
    }
    return validate_adapter_envelope(envelope, require_complete=False)
