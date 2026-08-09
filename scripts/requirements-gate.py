#!/usr/bin/env python3
"""Run the offline fail-closed requirements gate: needs JSON -> hardware contract JSON.

Usage:
    python scripts/requirements-gate.py --input <requirements.json> --output <contract.json> [--now <ISO8601>]

The gate never guesses: schema-invalid input or physical contradictions exit
non-zero without writing an output file. ``--now`` fixes ``generatedAt`` for
reproducible output; when omitted the current UTC time is used.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SPEC_DIR = REPO / "src" / "spec"
sys.path.insert(0, str(SPEC_DIR))

from requirements_gate import (  # noqa: E402
    ContractViolationError,
    RequirementsInputError,
    gate_requirements_to_contract,
    read_json,
    write_json,
)


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="requirements-input JSON document")
    parser.add_argument("--output", required=True, type=Path, help="hardware-contract JSON output path")
    parser.add_argument("--now", help="ISO 8601 timestamp for deterministic generatedAt")
    args = parser.parse_args(argv)
    try:
        requirements = read_json(args.input)
        contract = gate_requirements_to_contract(requirements, now=args.now)
        write_json(args.output, contract)
    except (OSError, json.JSONDecodeError, RequirementsInputError, ContractViolationError, KeyError, TypeError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "rejected", "error": type(exc).__name__, "message": str(exc)},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    print(
        json.dumps(
            {
                "status": contract["status"],
                "components": len(contract["components"]),
                "signals": len(contract["signals"]),
                "unresolved": len(contract["unresolved"]),
                "output": str(args.output),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
