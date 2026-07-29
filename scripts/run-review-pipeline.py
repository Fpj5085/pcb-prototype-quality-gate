#!/usr/bin/env python3
"""Run the adapter-neutral review pipeline without EDA access or mutation.

The pipeline establishes a stable handoff between a Draft/live adapter and the
independent review core. It can optionally create the currently supported
immutable local-bypass preview, but it never approves, executes, saves or
reloads an EDA design.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
REVIEW_DIR = REPO / "src" / "review"
REPAIR_DIR = REPO / "src" / "repair"
sys.path.insert(0, str(REVIEW_DIR))
sys.path.insert(0, str(REPAIR_DIR))

from local_bypass_plan import RepairPlanError, build_plan  # noqa: E402
from prototype_review import (  # noqa: E402
    InputValidationError,
    Review,
    emit_outputs,
    normalize_raw_input,
    read_json,
    sanitize_public_value,
    validate_design,
    validate_profiles,
    write_json,
)
from readonly_adapter_contract import (  # noqa: E402
    AdapterContractError,
    adapter_summary,
    validate_adapter_envelope,
)
from readonly_adapter_health import health_summary, validate_health_probe  # noqa: E402


PIPELINE_SCHEMA = "pcb-prototype-quality-gate-pipeline-run/1.1"


def _relative_or_name(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def run_pipeline(
    input_path: Path,
    profiles_path: Path,
    output_dir: Path,
    *,
    repair_evidence_path: Path | None = None,
    goal: str | None = None,
    adapter_evidence_path: Path | None = None,
    health_evidence_path: Path | None = None,
) -> dict[str, Any]:
    """Run adapter health gate, validation, normalization, review and planning."""
    raw = read_json(input_path)
    adapter = None
    health = None
    if health_evidence_path is not None:
        health = validate_health_probe(read_json(health_evidence_path))
    if adapter_evidence_path is not None:
        adapter = validate_adapter_envelope(read_json(adapter_evidence_path))
        if adapter["normalizedDesign"] != raw:
            raise AdapterContractError("--input must exactly equal adapter normalizedDesign")
    design = validate_design(normalize_raw_input(raw, input_path.resolve()))
    profiles = validate_profiles(read_json(profiles_path))
    result = Review(design, profiles).run()

    output_dir.mkdir(parents=True, exist_ok=True)
    review_dir = output_dir / "review"
    emit_outputs(design, result, review_dir)
    write_json(output_dir / "normalized-input.json", sanitize_public_value(design))

    run: dict[str, Any] = {
        "schema": PIPELINE_SCHEMA,
        "status": "reviewed",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "trustBoundary": {
            "draftGenerator": "external-adapter",
            "currentStateReadback": "validated-readonly-envelope" if adapter is not None else "input-file-supplied",
            "independentReview": "local-review-engine",
            "edaAccess": False,
            "edaWrites": 0,
            "approval": "not-requested",
            "environmentHealth": "validated-read-only" if health is not None else "not-probed",
        },
        "inputs": {
            "design": _relative_or_name(input_path, REPO),
            "profiles": _relative_or_name(profiles_path, REPO),
            **({"adapterEvidence": _relative_or_name(adapter_evidence_path, REPO), "adapter": adapter_summary(adapter)} if adapter is not None else {}),
            **({"healthEvidence": _relative_or_name(health_evidence_path, REPO), "health": health_summary(health)} if health is not None else {}),
        },
        "review": {
            "rating": result["rating"],
            "engineeringForecastRating": result.get("engineeringForecastRating"),
            "counts": result["counts"],
            "output": "review",
        },
        "repair": {"status": "not-requested"},
    }

    if repair_evidence_path is not None or goal is not None:
        if repair_evidence_path is None or not isinstance(goal, str) or not goal.strip():
            raise RepairPlanError("--repair-evidence and --goal must be supplied together")
        evidence = read_json(repair_evidence_path)
        plan = build_plan(result, evidence, goal)
        write_json(output_dir / "repair-plan.json", plan)
        run["status"] = "plan-ready"
        run["repair"] = {
            "status": "immutable-preview",
            "repairType": plan["repairType"],
            "planId": plan["planId"],
            "output": "repair-plan.json",
            "approval": "required-before-adapter-execution",
            "execution": "not-executed",
        }

    write_json(output_dir / "pipeline-run.json", sanitize_public_value(run))
    return run


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--profiles", type=Path, default=REVIEW_DIR / "component-profiles.json")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repair-evidence", type=Path)
    parser.add_argument("--goal")
    parser.add_argument("--adapter-evidence", type=Path, help="validated read-only adapter envelope; must contain the exact --input JSON")
    parser.add_argument("--health-evidence", type=Path, help="validated external adapter health receipt; ready is required")
    args = parser.parse_args(argv)
    try:
        run = run_pipeline(
            args.input,
            args.profiles,
            args.output,
            repair_evidence_path=args.repair_evidence,
            goal=args.goal,
            adapter_evidence_path=args.adapter_evidence,
            health_evidence_path=args.health_evidence,
        )
    except (OSError, json.JSONDecodeError, InputValidationError, RepairPlanError, KeyError, TypeError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "rejected", "error": type(exc).__name__, "message": sanitize_public_value(str(exc))},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps({"status": run["status"], "rating": run["review"]["rating"], "output": sanitize_public_value(str(args.output))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
