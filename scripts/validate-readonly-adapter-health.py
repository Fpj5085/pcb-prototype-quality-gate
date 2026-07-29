#!/usr/bin/env python3
"""Validate an external read-only adapter health-probe receipt offline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REVIEW_DIR = REPO / "src" / "review"
sys.path.insert(0, str(REVIEW_DIR))

from prototype_review import read_json, sanitize_public_value  # noqa: E402
from readonly_adapter_health import HealthContractError, health_summary, validate_health_probe  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--allow-blocked", action="store_true", help="validate for diagnostics without clearing the gate")
    args = parser.parse_args(argv)
    try:
        receipt = validate_health_probe(read_json(args.input), require_ready=not args.allow_blocked)
    except (OSError, json.JSONDecodeError, HealthContractError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "rejected", "error": type(exc).__name__, "message": sanitize_public_value(str(exc))}, ensure_ascii=False))
        return 2
    print(json.dumps({"status": "ready" if receipt["status"] == "ready" else "diagnostic-only", "summary": health_summary(receipt)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
