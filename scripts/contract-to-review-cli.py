#!/usr/bin/env python3
"""Convert a requirements-gate hardware contract into prototype-review input (offline).

Usage:
    python scripts/contract-to-review-cli.py --contract <contract.json> --output <review-input.json> [--issues-output <issues.txt>]

The converter never guesses: information the hardware contract does not express
is either omitted from the review input or registered in the conversion log
(written to ``--issues-output`` when requested). On any validation failure the
CLI exits 2 and writes no output file; both writes are atomic (temp file in the
same directory, then ``os.replace``), matching the requirements-gate style.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SPEC_DIR = REPO / "src" / "spec"
REVIEW_DIR = REPO / "src" / "review"
for _directory in (SPEC_DIR, REVIEW_DIR):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from contract_to_review import (  # noqa: E402
    ContractInputError,
    contract_to_review_input,
    contract_to_review_issues,
)


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _atomic_write(path: Path, payload: str) -> None:
    """Write text atomically: a temp file in the same directory, then os.replace.

    A failed write never leaves a partial output file at the destination.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
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


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True, type=Path, help="hardware-contract JSON document (requirements-gate output)")
    parser.add_argument("--output", required=True, type=Path, help="prototype-review-input JSON output path")
    parser.add_argument("--issues-output", type=Path, help="optional plain-text conversion log output path")
    args = parser.parse_args(argv)

    try:
        contract = read_json(args.contract)
        review_input = contract_to_review_input(contract)
        issues = contract_to_review_issues(contract)
        # Serialize everything up front so a serialization failure cannot leave a
        # Write the main --output first so an output-write failure leaves no
        # orphaned auxiliary issues file behind; the issues log is written only
        # after the primary output succeeds.
        output_payload = json.dumps(review_input, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        issues_payload = "".join(line + "\n" for line in issues)
        _atomic_write(args.output, output_payload)
        if args.issues_output:
            _atomic_write(args.issues_output, issues_payload)
    except (OSError, json.JSONDecodeError, ContractInputError, KeyError, TypeError, ValueError) as exc:
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
                "status": "converted",
                "components": len(review_input["components"]),
                "nets": len(review_input["nets"]),
                "issues": len(issues),
                "output": str(args.output),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
