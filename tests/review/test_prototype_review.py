import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = REPO / "src" / "review"
FIXTURES = HERE / "fixtures"
sys.path.insert(0, str(ROOT))

from prototype_review import (  # noqa: E402
    Review,
    RATING_FIX_FIRST,
    RATING_SUITABLE,
    RATING_UNSUITABLE,
    normalize_raw_input,
)


class PrototypeReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = json.loads((ROOT / "component-profiles.json").read_text(encoding="utf-8"))
        cls.safe = json.loads((FIXTURES / "synthetic-safe-input.json").read_text(encoding="utf-8"))

    def review(self, design):
        return Review(copy.deepcopy(design), self.profiles).run()

    def ids(self, result):
        return {f["id"] for f in result["findings"]}

    def test_current_car_black_box_hits_required_families(self):
        path = FIXTURES / "car-adversarial-input.json"
        design = json.loads(path.read_text(encoding="utf-8"))
        result = self.review(design)
        ids = self.ids(result)
        expected_prefixes = [
            "POWER_HEADROOM:U_REG", "PACKAGE_UNSUPPORTED:U_REG", "FUSE_HOLD:F_INPUT", "HBRIDGE_THERMAL:U_DRIVER",
            "TRACE_CAPACITY:VIN_IN", "BULK_CAP:U_DRIVER:VIN_PROT", "DECOUPLING_DISTANCE:U_DRIVER:VIN_PROT",
            "LEVEL_MARGIN:SENSOR_ECHO", "DEBUG_SIGNALS", "TESTPOINTS", "SILKSCREEN",
        ]
        for expected in expected_prefixes:
            self.assertIn(expected, ids)
        self.assertEqual(result["rating"], RATING_UNSUITABLE)
        self.assertEqual(design["checks"]["pcbDrcFindings"], 0)

    def test_synthetic_safe_fixture_has_no_current_design_names_and_passes(self):
        text = (FIXTURES / "synthetic-safe-input.json").read_text(encoding="utf-8")
        for forbidden in ["L293D", "AMS1117", "STM32F030", "HC-SR04", "MF-MSMF050"]:
            self.assertNotIn(forbidden, text)
        result = self.review(self.safe)
        self.assertEqual(result["rating"], RATING_SUITABLE)
        self.assertEqual(result["counts"]["blocker"], 0)
        self.assertEqual(result["counts"]["advisory"], 0)
        self.assertEqual(result["engineeringForecastRating"], RATING_SUITABLE)
        self.assertEqual(result["evidenceCompleteness"]["status"], "complete")
        self.assertTrue(result["evidenceCompleteness"]["allRequiredEvidencePresentAndValid"])
        self.assertTrue(result["evidenceCompleteness"]["allPrototypeGatesPassed"])

    def test_empty_checks_fail_closed_with_six_stable_incomplete_findings(self):
        d = copy.deepcopy(self.safe)
        d["checks"] = {}
        result = self.review(d)
        expected = {
            "EVIDENCE_INCOMPLETE:SCHEMATIC_ERRORS",
            "EVIDENCE_INCOMPLETE:SCHEMATIC_WARNINGS",
            "EVIDENCE_INCOMPLETE:PCB_DRC",
            "EVIDENCE_INCOMPLETE:UNROUTED",
            "EVIDENCE_INCOMPLETE:CONTAINMENT",
            "EVIDENCE_INCOMPLETE:PERSISTENCE",
        }
        self.assertTrue(expected.issubset(self.ids(result)))
        self.assertEqual(result["rating"], RATING_FIX_FIRST)
        self.assertEqual(result["engineeringForecastRating"], RATING_SUITABLE)
        self.assertEqual(result["counts"]["blocker"], 0)
        self.assertEqual(result["evidenceCompleteness"]["status"], "incomplete")
        self.assertEqual(
            set(result["evidenceCompleteness"]["missingFields"]),
            {"schematicErrors", "schematicWarnings", "pcbDrcFindings", "unroutedNets", "containment", "savedReloaded"},
        )

    def test_each_required_gate_missing_degrades_strict_rating(self):
        finding_ids = {
            "schematicErrors": "EVIDENCE_INCOMPLETE:SCHEMATIC_ERRORS",
            "schematicWarnings": "EVIDENCE_INCOMPLETE:SCHEMATIC_WARNINGS",
            "pcbDrcFindings": "EVIDENCE_INCOMPLETE:PCB_DRC",
            "unroutedNets": "EVIDENCE_INCOMPLETE:UNROUTED",
            "containment": "EVIDENCE_INCOMPLETE:CONTAINMENT",
            "savedReloaded": "EVIDENCE_INCOMPLETE:PERSISTENCE",
        }
        for field, finding_id in finding_ids.items():
            with self.subTest(field=field):
                d = copy.deepcopy(self.safe)
                del d["checks"][field]
                result = self.review(d)
                self.assertEqual(result["rating"], RATING_FIX_FIRST)
                self.assertIn(finding_id, self.ids(result))
                self.assertEqual(result["evidenceCompleteness"]["missingFields"], [field])
                self.assertFalse(result["evidenceCompleteness"]["allPrototypeGatesPassed"])

    def test_invalid_gate_types_and_values_are_not_coerced_to_pass(self):
        cases = [
            ("schematicErrors", "0", "EVIDENCE_INCOMPLETE:SCHEMATIC_ERRORS"),
            ("schematicErrors", False, "EVIDENCE_INCOMPLETE:SCHEMATIC_ERRORS"),
            ("schematicWarnings", 0.0, "EVIDENCE_INCOMPLETE:SCHEMATIC_WARNINGS"),
            ("pcbDrcFindings", -1, "EVIDENCE_INCOMPLETE:PCB_DRC"),
            ("unroutedNets", True, "EVIDENCE_INCOMPLETE:UNROUTED"),
            ("containment", 1, "EVIDENCE_INCOMPLETE:CONTAINMENT"),
            ("savedReloaded", "true", "EVIDENCE_INCOMPLETE:PERSISTENCE"),
        ]
        for field, value, finding_id in cases:
            with self.subTest(field=field, value=value):
                d = copy.deepcopy(self.safe)
                d["checks"][field] = value
                result = self.review(d)
                self.assertEqual(result["rating"], RATING_FIX_FIRST)
                self.assertIn(finding_id, self.ids(result))
                self.assertEqual(result["evidenceCompleteness"]["invalidFields"], [field])

    def test_explicit_gate_failures_remain_blockers(self):
        cases = [
            ("schematicErrors", 1, "SCHEMATIC_ERRORS"),
            ("pcbDrcFindings", 1, "PCB_DRC"),
            ("unroutedNets", 1, "UNROUTED"),
            ("containment", False, "CONTAINMENT"),
            ("savedReloaded", False, "PERSISTENCE"),
        ]
        for field, value, finding_id in cases:
            with self.subTest(field=field):
                d = copy.deepcopy(self.safe)
                d["checks"][field] = value
                result = self.review(d)
                self.assertEqual(result["rating"], RATING_UNSUITABLE)
                self.assertIn(finding_id, self.ids(result))
                finding = next(item for item in result["findings"] if item["id"] == finding_id)
                self.assertEqual(finding["severity"], "blocker")
                self.assertEqual(result["evidenceCompleteness"]["status"], "complete")
                self.assertFalse(result["evidenceCompleteness"]["allPrototypeGatesPassed"])

    def test_nonzero_schematic_warnings_require_supported_disposition(self):
        d = copy.deepcopy(self.safe)
        d["checks"].update({"schematicWarnings": 2, "schematicWarningDetailsAvailable": True})
        unresolved = self.review(d)
        self.assertEqual(unresolved["rating"], RATING_FIX_FIRST)
        self.assertIn("SCHEMATIC_WARNINGS", self.ids(unresolved))
        self.assertEqual(unresolved["evidenceCompleteness"]["gates"]["schematicWarnings"], "unexplained")

        d["checks"]["schematicWarningDisposition"] = "explained_and_accepted"
        accepted = self.review(d)
        self.assertEqual(accepted["rating"], RATING_SUITABLE)
        self.assertNotIn("SCHEMATIC_WARNINGS", self.ids(accepted))
        self.assertEqual(accepted["evidenceCompleteness"]["gates"]["schematicWarnings"], "explained")

    def test_live_and_persistence_metadata_conflicts_degrade_strict_rating(self):
        d = copy.deepcopy(self.safe)
        d["fixtureMetadata"] = {"liveEdaVerified": False, "persistenceEvidenceIncluded": False}
        result = self.review(d)
        self.assertEqual(result["rating"], RATING_FIX_FIRST)
        self.assertEqual(result["engineeringForecastRating"], RATING_SUITABLE)
        self.assertIn("EVIDENCE_CONFLICT:LIVE_EDA", self.ids(result))
        self.assertIn("EVIDENCE_CONFLICT:PERSISTENCE", self.ids(result))
        self.assertEqual(result["evidenceCompleteness"]["status"], "conflicting")
        self.assertEqual(len(result["evidenceCompleteness"]["contradictions"]), 2)

    def test_drc_zero_without_save_reload_evidence_is_not_suitable(self):
        d = copy.deepcopy(self.safe)
        self.assertEqual(d["checks"]["pcbDrcFindings"], 0)
        del d["checks"]["savedReloaded"]
        result = self.review(d)
        self.assertEqual(result["rating"], RATING_FIX_FIRST)
        self.assertIn("EVIDENCE_INCOMPLETE:PERSISTENCE", self.ids(result))

    def test_public_rating_enum_is_stable(self):
        self.assertEqual(
            {RATING_UNSUITABLE, RATING_FIX_FIRST, RATING_SUITABLE},
            {"not_suitable_for_prototype", "suitable_after_corrections", "suitable_for_low_risk_prototype"},
        )

    def test_raw_normalization_preserves_missing_gate_evidence(self):
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            (temp / "schematic.json").write_text("{}", encoding="utf-8")
            (temp / "pcb.json").write_text(
                json.dumps({"components": [], "wires": [], "vias": [], "polygons": []}), encoding="utf-8"
            )
            spec = {
                "rawEvidence": {"schematic": "schematic.json", "pcb": "pcb.json"},
                "designContext": {"designName": "raw missing gates", "checks": {}},
            }
            normalized = normalize_raw_input(spec, temp / "spec.json")
            self.assertEqual(normalized["checks"], {})
            result = self.review(normalized)
            self.assertEqual(result["rating"], RATING_FIX_FIRST)
            self.assertEqual(len(result["evidenceCompleteness"]["missingFields"]), 6)

    def test_dropout_exact_boundary_passes_and_below_fails(self):
        d = copy.deepcopy(self.safe)
        d["powerPaths"][0]["sourceMinV"] = 5.3
        r = self.review(d)
        self.assertNotIn("POWER_HEADROOM:PWR_A", self.ids(r))
        d["powerPaths"][0]["sourceMinV"] = 5.299
        self.assertIn("POWER_HEADROOM:PWR_A", self.ids(self.review(d)))

    def test_fuse_hold_boundary(self):
        d = copy.deepcopy(self.safe)
        d["protectedCircuits"][0].update({"continuousCurrentA": 2.4, "surgeCurrentA": 5.9, "holdDerating": 0.8})
        self.assertIn("FUSE_PASS:FUSE_A", self.ids(self.review(d)))
        d["protectedCircuits"][0]["continuousCurrentA"] = 2.401
        self.assertIn("FUSE_HOLD:FUSE_A", self.ids(self.review(d)))

    def test_hbridge_thermal_threshold(self):
        d = copy.deepcopy(self.safe)
        d["hbridgeUses"][0]["maxEstimatedRiseC"] = 4.0
        self.assertNotEqual(self.review(d)["rating"], RATING_UNSUITABLE)
        d["hbridgeUses"][0]["maxEstimatedRiseC"] = 3.99
        self.assertIn("HBRIDGE_THERMAL:DRV_A", self.ids(self.review(d)))
        f = next(x for x in self.review(d)["findings"] if x["id"] == "HBRIDGE_THERMAL:DRV_A")
        self.assertEqual(f["severity"], "blocker")

    def test_regulator_thermal_budget(self):
        d = copy.deepcopy(self.safe)
        d["regulatorUses"][0]["loadMaxA"] = 0.25
        f = next(x for x in self.review(d)["findings"] if x["id"] == "REGULATOR_THERMAL:PWR_A")
        self.assertEqual(f["severity"], "advisory")
        d["regulatorUses"][0]["loadMaxA"] = 0.5
        f = next(x for x in self.review(d)["findings"] if x["id"] == "REGULATOR_THERMAL:PWR_A")
        self.assertEqual(f["severity"], "blocker")

    def test_trace_width_current_boundary(self):
        d = copy.deepcopy(self.safe)
        net = d["nets"][0]
        cap = Review.ipc2221_capacity(net["minWidthMm"], 1.0, 10.0)
        net["designCurrentA"] = cap / 1.25
        self.assertIn("TRACE_PASS:SOURCE", self.ids(self.review(d)))
        net["designCurrentA"] = cap / 1.25 + 0.001
        self.assertIn("TRACE_CAPACITY:SOURCE", self.ids(self.review(d)))

    def test_decoupling_distance_boundary(self):
        d = copy.deepcopy(self.safe)
        cap = next(c for c in d["components"] if c["ref"] == "C_FAST_RAW")
        cap["x"] = 33.0
        self.assertIn("DECOUPLING_PASS:DRV_A:RAW", self.ids(self.review(d)))
        cap["x"] = 33.001
        self.assertIn("DECOUPLING_DISTANCE:DRV_A:RAW", self.ids(self.review(d)))

    def test_level_margin_boundary(self):
        d = copy.deepcopy(self.safe)
        div = d["voltageDividers"][0]
        div.update({"inputMaxV": 5.1, "topOhm": 1, "bottomOhm": 2, "receiverAbsMaxV": 3.6, "requiredMarginV": 0.2})
        finding = next(f for f in self.review(d)["findings"] if f["id"] == "LEVEL_MARGIN:SENSE_A")
        self.assertEqual(finding["severity"], "pass")
        div["inputMaxV"] = 5.115
        finding = next(f for f in self.review(d)["findings"] if f["id"] == "LEVEL_MARGIN:SENSE_A")
        self.assertEqual(finding["severity"], "advisory")

    def test_missing_datasheet_degrades_rating_but_other_checks_continue(self):
        d = copy.deepcopy(self.safe)
        d["components"].append({"ref": "CRITICAL_X", "critical": True, "package": "GENERIC", "x": 0, "y": 0, "nets": []})
        result = self.review(d)
        self.assertIn("DATASHEET_MISSING:CRITICAL_X", self.ids(result))
        self.assertEqual(result["rating"], RATING_FIX_FIRST)
        self.assertGreater(result["counts"]["pass"], 0)

    def test_drc_zero_does_not_override_engineering_blocker(self):
        d = copy.deepcopy(self.safe)
        self.assertEqual(d["checks"]["pcbDrcFindings"], 0)
        d["powerPaths"][0]["sourceMinV"] = 4.0
        result = self.review(d)
        self.assertEqual(result["rating"], RATING_UNSUITABLE)
        self.assertIn("POWER_HEADROOM:PWR_A", self.ids(result))

    def test_ground_and_topology_fail_closed(self):
        d = copy.deepcopy(self.safe)
        d["groundReview"]["islands"] = 1
        d["schematicTopology"]["floatingInputs"] = ["CTRL_A.5"]
        result = self.review(d)
        ids = self.ids(result)
        self.assertIn("GROUND_RETURN", ids)
        self.assertIn("SCHEMATIC_TOPOLOGY", ids)
        self.assertEqual(result["rating"], RATING_UNSUITABLE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
