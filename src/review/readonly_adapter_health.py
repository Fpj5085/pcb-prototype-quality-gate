#!/usr/bin/env python3
"""Validate an offline health-probe receipt for a read-only environment adapter.

This module never performs a network request and never talks to EDA. It only
validates an explicit probe receipt produced by an external environment
adapter. A non-ready receipt is diagnostic only and must not be used as live
readback evidence.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any


HEALTH_SCHEMA = "pcb-prototype-quality-gate-readonly-adapter-health/1.0"
HEALTH_STATUSES = {"ready", "blocked", "unknown"}
HEALTH_ERROR_CLASSES = {
    "adapter_unavailable",
    "upstream_5xx",
    "timeout_unknown",
    "malformed_response",
    "no_window",
    "target_ambiguous",
    "read_only_violation",
    "unexpected_write_count",
    "protocol_mismatch",
    "internal_error",
}


class HealthContractError(ValueError):
    """Raised when a health receipt cannot establish a safe read-only channel."""


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HealthContractError(f"{label} must be an object")
    return value


def _exact_keys(value: dict[str, Any], required: set[str], label: str) -> None:
    missing = sorted(required - set(value))
    extra = sorted(set(value) - required)
    if missing or extra:
        raise HealthContractError(f"{label} keys mismatch; missing={missing}, extra={extra}")


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HealthContractError(f"{label} must be a non-empty string")
    return value


def _timestamp(value: Any, label: str) -> str:
    text = _text(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HealthContractError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise HealthContractError(f"{label} must include a timezone")
    return text


def _errors(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise HealthContractError("errors must be an array")
    rows: list[dict[str, str]] = []
    for index, raw in enumerate(value):
        row = _object(raw, f"errors[{index}]")
        _exact_keys(row, {"class", "message"}, f"errors[{index}]")
        error_class = _text(row["class"], f"errors[{index}].class")
        if error_class not in HEALTH_ERROR_CLASSES:
            raise HealthContractError(f"errors[{index}].class is unsupported")
        rows.append({"class": error_class, "message": _text(row["message"], f"errors[{index}].message")})
    return rows


def validate_health_probe(value: Any, *, require_ready: bool = True) -> dict[str, Any]:
    """Validate a probe receipt; ready is the only state that clears the gate."""
    receipt = _object(value, "healthProbe")
    _exact_keys(receipt, {"schema", "status", "adapter", "probe", "errors"}, "healthProbe")
    if receipt["schema"] != HEALTH_SCHEMA:
        raise HealthContractError(f"healthProbe.schema must be {HEALTH_SCHEMA}")
    status = receipt["status"]
    if status not in HEALTH_STATUSES:
        raise HealthContractError("healthProbe.status must be ready, blocked or unknown")

    adapter = _object(receipt["adapter"], "adapter")
    _exact_keys(adapter, {"name", "version", "readOnly", "edaWrites"}, "adapter")
    _text(adapter["name"], "adapter.name")
    _text(adapter["version"], "adapter.version")
    if adapter["readOnly"] is not True:
        raise HealthContractError("adapter.readOnly must be true")
    if type(adapter["edaWrites"]) is not int or adapter["edaWrites"] != 0:
        raise HealthContractError("adapter.edaWrites must be integer zero")

    errors = _errors(receipt["errors"])
    probe = _object(receipt["probe"], "probe")
    _exact_keys(probe, {"probedAt", "transport", "session", "response"}, "probe")
    _timestamp(probe["probedAt"], "probe.probedAt")

    transport = _object(probe["transport"], "probe.transport")
    _exact_keys(transport, {"ok", "httpStatus", "contentType"}, "probe.transport")
    if type(transport["ok"]) is not bool:
        raise HealthContractError("probe.transport.ok must be boolean")
    status_code = transport["httpStatus"]
    if status_code is not None and (type(status_code) is not int or not 100 <= status_code <= 599):
        raise HealthContractError("probe.transport.httpStatus must be null or an HTTP status integer")
    content_type = transport["contentType"]
    if content_type is not None and not isinstance(content_type, str):
        raise HealthContractError("probe.transport.contentType must be null or a string")

    session = _object(probe["session"], "probe.session")
    _exact_keys(session, {"windowCount", "uniqueTarget", "readOnly", "edaWrites"}, "probe.session")
    if type(session["windowCount"]) is not int or session["windowCount"] < 0:
        raise HealthContractError("probe.session.windowCount must be a non-negative integer")
    for key in ("uniqueTarget", "readOnly"):
        if type(session[key]) is not bool:
            raise HealthContractError(f"probe.session.{key} must be boolean")
    if type(session["edaWrites"]) is not int or session["edaWrites"] < 0:
        raise HealthContractError("probe.session.edaWrites must be a non-negative integer")

    response = _object(probe["response"], "probe.response")
    _exact_keys(response, {"jsonObject", "protocolValid"}, "probe.response")
    for key in ("jsonObject", "protocolValid"):
        if type(response[key]) is not bool:
            raise HealthContractError(f"probe.response.{key} must be boolean")

    if status == "ready":
        if errors:
            raise HealthContractError("ready health probe must have no errors")
        if transport["ok"] is not True or status_code != 200:
            raise HealthContractError("ready health probe requires a successful HTTP 200 transport")
        if session != {"windowCount": 1, "uniqueTarget": True, "readOnly": True, "edaWrites": 0}:
            raise HealthContractError("ready health probe requires one unique read-only zero-write target")
        if response != {"jsonObject": True, "protocolValid": True}:
            raise HealthContractError("ready health probe requires a valid JSON protocol response")
        return deepcopy(receipt)

    if not errors:
        raise HealthContractError("blocked or unknown health probe must include a classified error")
    if require_ready:
        raise HealthContractError(f"adapter health is {status}: {errors[0]['class']}")
    return deepcopy(receipt)


def health_summary(receipt: dict[str, Any]) -> dict[str, Any]:
    """Return only safe gate fields for a pipeline receipt."""
    probe = receipt["probe"]
    return {
        "schema": receipt["schema"],
        "status": receipt["status"],
        "adapter": dict(receipt["adapter"]),
        "probedAt": probe["probedAt"],
        "transport": dict(probe["transport"]),
        "session": dict(probe["session"]),
        "response": dict(probe["response"]),
        "errors": deepcopy(receipt["errors"]),
    }
