import copy
import json
import subprocess
import sys
from tests import ArchivedTemporaryDirectory
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src" / "repair"))
from local_bypass_plan import RepairPlanError, build_plan  # noqa: E402


def evidence():
    return {
        "components": [
            {"ref": "J2", "x": 10.0, "y": 0.0, "nets": ["+5V", "GND"]},
            {"ref": "C1", "x": -10.0, "y": 0.0, "nets": ["+5V", "GND"], "capacitanceUf": 10.0},
        ],
        "checks": {"schematicErrors": 0, "schematicWarnings": 0, "schematicWarningDetailsAvailable": True, "pcbDrcFindings": 0, "unroutedNets": 0, "containment": True, "savedReloaded": True},
        "decouplingRequirements": [{"targetRef": "J2", "supplyNet": "+5V", "returnNet": "GND", "minCapacitanceUf": 0.08, "maxCapacitanceUf": 0.22, "maxDistanceMm": 7, "severity": "blocker"}],
    }


def review():
    return {"findings": [{"id": "TRACE_PASS:+5V", "severity": "pass"}, {"id": "DECOUPLING_DISTANCE:J2:+5V", "severity": "blocker", "confidence": "high"}]}


class LocalBypassPlanTests(unittest.TestCase):
    def test_builds_deterministic_locked_plan(self):
        first = build_plan(review(), evidence(), "在J2附近增加本地旁路电容")
        second = build_plan(review(), evidence(), "在J2附近增加本地旁路电容")
        self.assertEqual(first, second)
        self.assertEqual(first["repairType"], "ADD_LOCAL_BYPASS_CAP")
        self.assertEqual(first["componentLock"]["mpn"], "CL21B104KBCNNNC")
        self.assertEqual(first["connectionIntent"], {"1": "+5V", "2": "GND"})
        self.assertTrue(first["planId"].startswith("sha256:"))

    def test_each_critical_check_is_required(self):
        for name in ("schematicErrors", "schematicWarnings", "schematicWarningDetailsAvailable", "pcbDrcFindings", "unroutedNets", "containment", "savedReloaded"):
            case = evidence(); del case["checks"][name]
            with self.subTest(name=name), self.assertRaises(RepairPlanError):
                build_plan(review(), case, "修正")

    def test_explicit_failed_gate_is_rejected(self):
        for name, bad in (("schematicErrors", 1), ("pcbDrcFindings", 1), ("unroutedNets", 1), ("containment", False), ("savedReloaded", False)):
            case = evidence(); case["checks"][name] = bad
            with self.subTest(name=name), self.assertRaises(RepairPlanError):
                build_plan(review(), case, "修正")

    def test_multiple_or_unknown_findings_are_rejected(self):
        multi = review(); multi["findings"].append({"id": "OTHER", "severity": "advisory", "confidence": "high"})
        with self.assertRaises(RepairPlanError): build_plan(multi, evidence(), "修正")
        unknown = {"findings": [{"id": "OTHER", "severity": "blocker", "confidence": "high"}]}
        with self.assertRaises(RepairPlanError): build_plan(unknown, evidence(), "修正")

    def test_uncertain_target_or_network_is_rejected(self):
        missing = evidence(); missing["components"] = missing["components"][1:]
        with self.assertRaises(RepairPlanError): build_plan(review(), missing, "修正")
        wrong = evidence(); wrong["components"][0]["nets"] = ["+5V"]
        with self.assertRaises(RepairPlanError): build_plan(review(), wrong, "修正")

    def test_existing_qualified_bypass_is_rejected(self):
        case = evidence(); case["components"].append({"ref": "C2", "x": 11.0, "y": 0.0, "nets": ["+5V", "GND"], "capacitanceUf": 0.1})
        with self.assertRaisesRegex(RepairPlanError, "already exists"):
            build_plan(review(), case, "修正")

    def test_cli_writes_plan_and_rejects_bad_input_without_traceback(self):
        with ArchivedTemporaryDirectory() as name:
            root = Path(name); rp = root / "review.json"; ep = root / "evidence.json"; out = root / "plan.json"
            rp.write_text(json.dumps(review()), encoding="utf-8"); ep.write_text(json.dumps(evidence()), encoding="utf-8")
            ok = subprocess.run([sys.executable, str(REPO / "scripts" / "plan-local-bypass.py"), "--review", str(rp), "--evidence", str(ep), "--goal", "修正J2旁路", "--output", str(out)], text=True, encoding="utf-8", capture_output=True)
            self.assertEqual(ok.returncode, 0, ok.stderr); self.assertTrue(out.is_file())
            bad = evidence(); del bad["checks"]["savedReloaded"]; ep.write_text(json.dumps(bad), encoding="utf-8")
            rejected = subprocess.run([sys.executable, str(REPO / "scripts" / "plan-local-bypass.py"), "--review", str(rp), "--evidence", str(ep), "--goal", "修正", "--output", str(out)], text=True, encoding="utf-8", capture_output=True)
            self.assertEqual(rejected.returncode, 2); self.assertNotIn("Traceback", rejected.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)

