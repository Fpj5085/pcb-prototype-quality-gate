#!/usr/bin/env python3
"""Replay every sanitized offline evaluation fixture without EDA access."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
ENGINE_DIR = REPO / "src" / "review"
sys.path.insert(0, str(ENGINE_DIR))

from prototype_review import (  # noqa: E402
    InputValidationError,
    Review,
    emit_outputs,
    read_json,
    sanitize_public_value,
    validate_design,
    validate_profiles,
)


def finding_map(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {finding["id"]: finding for finding in result["findings"]}


def compare_expected(result: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    actual = finding_map(result)
    if result.get("rating") != expected.get("rating"):
        errors.append(f"rating: expected {expected.get('rating')!r}, got {result.get('rating')!r}")
    if "counts" in expected and result.get("counts") != expected["counts"]:
        errors.append(f"counts: expected {expected['counts']!r}, got {result.get('counts')!r}")
    for requirement in expected.get("requiredFindings", []):
        finding_id = requirement["id"]
        finding = actual.get(finding_id)
        if finding is None:
            errors.append(f"required finding missing: {finding_id}")
            continue
        for field in ("severity", "confidence", "ruleFamily"):
            if field in requirement and finding.get(field) != requirement[field]:
                errors.append(
                    f"{finding_id}.{field}: expected {requirement[field]!r}, got {finding.get(field)!r}"
                )
    for finding_id in expected.get("forbiddenFindings", []):
        if finding_id in actual:
            errors.append(f"forbidden finding present: {finding_id}")
    forbidden_severities = set(expected.get("forbiddenSeverities", []))
    if forbidden_severities:
        bad = sorted(finding["id"] for finding in result["findings"] if finding["severity"] in forbidden_severities)
        if bad:
            errors.append(f"findings use forbidden severities {sorted(forbidden_severities)}: {bad}")
    if "findingIdsExact" in expected:
        expected_ids = set(expected["findingIdsExact"])
        actual_ids = set(actual)
        if expected_ids != actual_ids:
            errors.append(
                f"findingIdsExact mismatch: missing={sorted(expected_ids - actual_ids)}, "
                f"unexpected={sorted(actual_ids - expected_ids)}"
            )
    benchmark = expected.get("benchmark")
    if benchmark:
        matches = 0
        for family, candidate_ids in benchmark.get("requiredFamilyMatches", {}).items():
            present = sorted(set(candidate_ids) & set(actual))
            if present:
                matches += 1
            else:
                errors.append(f"benchmark family not detected: {family}")
        expected_matches = benchmark.get("expectedMatchedFamilies")
        if expected_matches is not None and matches != expected_matches:
            errors.append(f"benchmark matches: expected {expected_matches}, got {matches}")
    return errors


def discover_cases(evals_root: Path, requested: list[str]) -> list[Path]:
    manifests = sorted(evals_root.glob("*/manifest.json"))
    if requested:
        selected = {name for name in requested}
        manifests = [path for path in manifests if path.parent.name in selected]
        missing = sorted(selected - {path.parent.name for path in manifests})
        if missing:
            raise InputValidationError(f"unknown eval case(s): {', '.join(missing)}")
    if not manifests:
        raise InputValidationError(f"no eval manifests found under {evals_root}")
    return manifests


def case_local_path(case_dir: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise InputValidationError(f"{label} must be a non-empty relative path")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise InputValidationError(f"{label} must stay inside its eval directory")
    path = (case_dir / relative).resolve()
    try:
        path.relative_to(case_dir.resolve())
    except ValueError as exc:
        raise InputValidationError(f"{label} must stay inside its eval directory") from exc
    return path


def run_case(manifest_path: Path, profiles: dict[str, Any], write_root: Path | None) -> dict[str, Any]:
    manifest = read_json(manifest_path)
    case_dir = manifest_path.parent
    if manifest.get("schema") != "jlceda-eval-manifest/1.0":
        raise InputValidationError(f"{manifest_path}: unsupported eval manifest schema")
    case_id = manifest.get("id")
    if case_id != case_dir.name:
        raise InputValidationError(f"{manifest_path}: manifest id must match directory name")
    input_path = case_local_path(case_dir, manifest.get("input"), f"{case_id}.input")
    expected_path = case_local_path(case_dir, manifest.get("expected"), f"{case_id}.expected")
    design = validate_design(read_json(input_path))
    expected = read_json(expected_path)
    if expected.get("schema") != "jlceda-eval-expected/1.0":
        raise InputValidationError(f"{expected_path}: unsupported eval expectation schema")
    result = Review(design, profiles).run()
    errors = compare_expected(result, expected)
    if write_root is not None:
        emit_outputs(design, result, write_root / case_id)
    return {
        "id": case_id,
        "status": "pass" if not errors else "fail",
        "rating": result["rating"],
        "counts": result["counts"],
        "errors": errors,
        "execution": manifest.get("execution", {}),
    }


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Replay sanitized JLCEDA Prototype review evals")
    parser.add_argument("--evals", type=Path, default=REPO / "evals")
    parser.add_argument("--profiles", type=Path, default=ENGINE_DIR / "component-profiles.json")
    parser.add_argument("--case", action="append", default=[], help="case directory name; repeatable")
    parser.add_argument("--write-results", type=Path, help="optional directory for generated review artifacts")
    args = parser.parse_args(argv)
    try:
        profiles = validate_profiles(read_json(args.profiles))
        manifests = discover_cases(args.evals, args.case)
        cases = [run_case(path, profiles, args.write_results) for path in manifests]
    except (OSError, json.JSONDecodeError, InputValidationError, KeyError, TypeError, ValueError) as exc:
        print(
            json.dumps({"error": type(exc).__name__, "message": sanitize_public_value(str(exc))}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 2
    summary = {
        "schema": "jlceda-eval-replay-result/1.0",
        "status": "pass" if all(case["status"] == "pass" for case in cases) else "fail",
        "cases": cases,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
