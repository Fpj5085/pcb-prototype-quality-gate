#!/usr/bin/env python3
"""Fail-closed mapping from one decoupling finding to one immutable repair plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path


class RepairPlanError(ValueError):
    pass


PART = {
    "manufacturer": "Samsung Electro-Mechanics",
    "mpn": "CL21B104KBCNNNC",
    "value": "100nF",
    "capacitanceUf": 0.1,
    "dielectric": "X7R",
    "voltageRating": "50V",
    "package": "C0805",
    "supplier": "LCSC",
    "supplierPartNumber": "C1711",
    "pinToPad": {"1": "1", "2": "2"},
}

REQUIRED_CHECKS = {
    "schematicErrors": 0,
    "pcbDrcFindings": 0,
    "unroutedNets": 0,
    "containment": True,
    "savedReloaded": True,
}


def _fail(message: str) -> None:
    raise RepairPlanError(message)


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        _fail(f"{name} must be a finite number")
    return float(value)


def _validate_checks(evidence: dict) -> None:
    checks = evidence.get("checks")
    if not isinstance(checks, dict):
        _fail("evidence.checks is required")
    for name, expected in REQUIRED_CHECKS.items():
        if name not in checks:
            _fail(f"evidence.checks.{name} is required")
        actual = checks[name]
        if type(actual) is not type(expected) or actual != expected:
            _fail(f"evidence.checks.{name} must be {expected!r}")
    if "schematicWarnings" not in checks or type(checks["schematicWarnings"]) is not int:
        _fail("evidence.checks.schematicWarnings must be an explicit integer")
    if checks["schematicWarnings"] != 0:
        _fail("schematic warnings must be resolved before automatic repair")
    if checks.get("schematicWarningDetailsAvailable") is not True:
        _fail("schematic warning details must be available")


def _matching_requirement(evidence: dict, target: str, supply: str) -> dict:
    requirements = evidence.get("decouplingRequirements")
    if not isinstance(requirements, list):
        _fail("decouplingRequirements is required")
    matches = [r for r in requirements if isinstance(r, dict) and r.get("targetRef") == target and r.get("supplyNet") == supply]
    if len(matches) != 1:
        _fail("exactly one matching decoupling requirement is required")
    req = matches[0]
    if req.get("returnNet") != "GND":
        _fail("return network must be explicitly GND")
    low = _number(req.get("minCapacitanceUf"), "minCapacitanceUf")
    high = _number(req.get("maxCapacitanceUf"), "maxCapacitanceUf")
    distance = _number(req.get("maxDistanceMm"), "maxDistanceMm")
    if not (0 < low <= PART["capacitanceUf"] <= high and 0 < distance <= 20):
        _fail("locked capacitor or distance is outside the requirement")
    return {**req, "minCapacitanceUf": low, "maxCapacitanceUf": high, "maxDistanceMm": distance}


def _component_map(evidence: dict) -> dict[str, dict]:
    components = evidence.get("components")
    if not isinstance(components, list):
        _fail("evidence.components is required")
    result: dict[str, dict] = {}
    for component in components:
        if not isinstance(component, dict) or not isinstance(component.get("ref"), str):
            _fail("each component requires a ref")
        if component["ref"] in result:
            _fail("component refs must be unique")
        result[component["ref"]] = component
    return result


def _reject_existing_bypass(components: dict[str, dict], target: dict, supply: str, return_net: str, max_distance: float) -> None:
    tx = _number(target.get("x"), "target.x")
    ty = _number(target.get("y"), "target.y")
    for component in components.values():
        nets = component.get("nets")
        cap = component.get("capacitanceUf")
        if not isinstance(nets, list) or supply not in nets or return_net not in nets or cap is None:
            continue
        capacitance = _number(cap, f"{component['ref']}.capacitanceUf")
        if not (0.08 <= capacitance <= 0.22):
            continue
        distance = math.hypot(_number(component.get("x"), f"{component['ref']}.x") - tx, _number(component.get("y"), f"{component['ref']}.y") - ty)
        if distance <= max_distance:
            _fail(f"a qualifying local bypass already exists at {component['ref']}")


def build_plan(review: dict, evidence: dict, goal: str) -> dict:
    if not isinstance(review, dict) or not isinstance(evidence, dict):
        _fail("review and evidence must be objects")
    if not isinstance(goal, str) or not goal.strip():
        _fail("ordinary-language goal is required")
    _validate_checks(evidence)

    findings = review.get("findings")
    if not isinstance(findings, list):
        _fail("review.findings is required")
    unresolved = [f for f in findings if isinstance(f, dict) and f.get("severity") != "pass"]
    if len(unresolved) != 1:
        _fail("exactly one unresolved finding is required")
    finding = unresolved[0]
    finding_id = finding.get("id")
    if not isinstance(finding_id, str) or not finding_id.startswith("DECOUPLING_DISTANCE:"):
        _fail("the only supported finding is DECOUPLING_DISTANCE")
    if finding.get("severity") != "blocker" or finding.get("confidence") != "high":
        _fail("the decoupling finding must be a high-confidence blocker")
    fields = finding_id.split(":")
    if len(fields) != 3 or not fields[1] or not fields[2]:
        _fail("decoupling finding ID is malformed")
    target_ref, supply_net = fields[1], fields[2]

    components = _component_map(evidence)
    target = components.get(target_ref)
    if target is None:
        _fail("target component is absent from evidence")
    if not isinstance(target.get("nets"), list) or supply_net not in target["nets"] or "GND" not in target["nets"]:
        _fail("target supply/return networks are uncertain")
    req = _matching_requirement(evidence, target_ref, supply_net)
    _reject_existing_bypass(components, target, supply_net, req["returnNet"], req["maxDistanceMm"])

    body = {
        "schema": "pcb-prototype-quality-gate-repair-plan/1.0",
        "status": "immutable-preview",
        "repairType": "ADD_LOCAL_BYPASS_CAP",
        "sourceFinding": finding_id,
        "ordinaryLanguageGoal": goal.strip(),
        "target": {"componentRef": target_ref, "supplyNet": supply_net, "returnNet": req["returnNet"]},
        "componentLock": dict(PART),
        "placementConstraint": {"referenceComponent": target_ref, "maxDistanceMm": req["maxDistanceMm"], "requireShortSupplyReturnLoop": True},
        "connectionIntent": {"1": supply_net, "2": req["returnNet"]},
        "adapterBinding": {"requiredAtExecution": True, "publicPlanContainsPrivateIds": False},
        "executionPolicy": {"additionOnly": True, "singleSchematicMutation": True, "singlePcbMutation": True, "receiptOwnedRollbackOnly": True},
        "revalidationGates": [
            "schematic_identity_and_pin_to_pad",
            "schematic_erc_zero",
            "pcb_connectivity_complete",
            "pcb_containment_true",
            "pcb_strict_drc_zero",
            "save_close_reload_verified",
            "fresh_review_closes_source_finding",
        ],
    }
    plan_id = "sha256:" + hashlib.sha256(_canonical(body)).hexdigest()
    return {**body, "planId": plan_id}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build one fail-closed local-bypass repair plan")
    parser.add_argument("--review", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        review = json.loads(Path(args.review).read_text(encoding="utf-8-sig"))
        evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8-sig"))
        plan = build_plan(review, evidence, args.goal)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "planned", "repairType": plan["repairType"], "planId": plan["planId"], "output": output.name}, ensure_ascii=False))
        return 0
    except (OSError, json.JSONDecodeError, RepairPlanError) as exc:
        print(json.dumps({"status": "rejected", "error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

