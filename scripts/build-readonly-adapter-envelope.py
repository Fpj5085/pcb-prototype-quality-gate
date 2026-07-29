#!/usr/bin/env python3
"""Build a sanitized read-only adapter envelope from explicit offline evidence.

This command is an exporter boundary, not an EDA adapter. It only combines a
normalized design and a separately captured, sanitized read-only capture. It
never contacts EDA, performs mutation, saves, reloads, or selects a window.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REVIEW_DIR = REPO / "src" / "review"
sys.path.insert(0, str(REVIEW_DIR))

from prototype_review import read_json, sanitize_public_value, write_json  # noqa: E402
from readonly_adapter_export import (  # noqa: E402
    AdapterContractError,
    build_complete_envelope,
    build_failure_envelope,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", choices=["complete", "failed", "unknown"], default="complete")
    parser.add_argument("--design", type=Path, help="normalized design JSON; required for complete")
    parser.add_argument("--capture", type=Path, help="sanitized capture facts JSON; required for complete")
    parser.add_argument("--error-class", help="allow-listed failure class; required for failed/unknown")
    parser.add_argument("--message", help="failure message; required for failed/unknown")
    parser.add_argument("--adapter-name", required=True)
    parser.add_argument("--adapter-version", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.status == "complete":
            if args.design is None or args.capture is None:
                raise AdapterContractError("--design and --capture are required for complete status")
            envelope = build_complete_envelope(
                read_json(args.design),
                read_json(args.capture),
                adapter_name=args.adapter_name,
                adapter_version=args.adapter_version,
            )
        else:
            if not args.error_class or not args.message:
                raise AdapterContractError("--error-class and --message are required for failed or unknown status")
            envelope = build_failure_envelope(
                args.status,
                args.error_class,
                args.message,
                adapter_name=args.adapter_name,
                adapter_version=args.adapter_version,
            )
        write_json(args.output, sanitize_public_value(envelope))
    except (OSError, json.JSONDecodeError, AdapterContractError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "rejected", "error": type(exc).__name__, "message": sanitize_public_value(str(exc))}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"status": "written", "output": sanitize_public_value(str(args.output))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
