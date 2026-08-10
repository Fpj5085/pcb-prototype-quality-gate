import copy
import json
import sys
from tests import ArchivedTemporaryDirectory
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = REPO / "src" / "review"
FIXTURES = HERE / "fixtures"
sys.path.insert(0, str(ROOT))

from prototype_review import (  # noqa: E402
    InputValidationError,
    Review,
    RATING_FIX_FIRST,
    RATING_SUITABLE,
    RATING_UNSUITABLE,
    normalize_raw_input,
)


class _ReviewTestCaseBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = json.loads((ROOT / "component-profiles.json").read_text(encoding="utf-8"))
        cls.safe = json.loads((FIXTURES / "synthetic-safe-input.json").read_text(encoding="utf-8"))

    def review(self, design):
        return Review(copy.deepcopy(design), self.profiles).run()

    def ids(self, result):
        return {f["id"] for f in result["findings"]}


class PrototypeReviewTests(_ReviewTestCaseBase):

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
        with ArchivedTemporaryDirectory() as temp_name:
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


def _complete_checks():
    return {
        "schematicErrors": 0,
        "schematicWarnings": 0,
        "pcbDrcFindings": 0,
        "unroutedNets": 0,
        "containment": True,
        "savedReloaded": True,
    }


class SchematicContainmentTests(_ReviewTestCaseBase):
    """Rule family schematic_containment: schematic sheet-frame containment.

    Coordinate convention under test: (originXmm, originYmm) is the sheet's top-left
    corner; X increases right and Y decreases downward (top edge = originYmm, bottom
    edge = originYmm-heightMm), so the page spans
    x in [originXmm, originXmm+widthMm] and y in [originYmm-heightMm, originYmm].
    Component x/y are converted to millimetres via /unitsPerMm.
    """

    def containment_design(self, components, sheet):
        design = {
            "schema": "jlceda-prototype-review-input/1.0",
            "designName": "schematic containment unit design",
            "components": components,
            "nets": [],
            "checks": _complete_checks(),
        }
        if sheet is not None:
            design["schematicSheet"] = sheet
        return design

    def containment_ids(self, result):
        return {i for i in self.ids(result) if i.startswith("SCHEMATIC_CONTAINMENT")}

    def m2_design(self, coordinates):
        return self.containment_design(
            [{"ref": ref, "x": x, "y": y} for ref, x, y in coordinates],
            {"widthMm": 297, "heightMm": 210, "originXmm": 0, "originYmm": 0, "unitsPerMm": 3.937},
        )

    def test_components_inside_page_record_pass(self):
        sheet = {"widthMm": 100, "heightMm": 100, "originXmm": 0, "originYmm": 100}
        d = self.containment_design(
            [
                {"ref": "C_IN_1", "x": 20, "y": 20},
                {"ref": "C_IN_2", "x": 80, "y": 80},
                {"ref": "C_EDGE", "x": 0, "y": 100},  # exactly on the top-left corner: inclusive
            ],
            sheet,
        )
        result = self.review(d)
        self.assertEqual(result["rating"], RATING_SUITABLE)
        self.assertIn("SCHEMATIC_CONTAINMENT", self.ids(result))
        pass_finding = next(f for f in result["findings"] if f["id"] == "SCHEMATIC_CONTAINMENT")
        self.assertEqual(pass_finding["severity"], "pass")
        self.assertEqual(self.containment_ids(result), {"SCHEMATIC_CONTAINMENT"})
        self.assertEqual(pass_finding["evidence"][0]["checkedComponents"], 3)

    def test_out_of_bounds_blockers_on_all_four_sides(self):
        sheet = {"widthMm": 100, "heightMm": 100, "originXmm": 0, "originYmm": 100}
        d = self.containment_design(
            [
                {"ref": "R_LEFT", "x": -5, "y": 50},
                {"ref": "R_RIGHT", "x": 105, "y": 50},
                {"ref": "R_TOP", "x": 50, "y": 105},
                {"ref": "R_BOTTOM", "x": 50, "y": -5},
            ],
            sheet,
        )
        result = self.review(d)
        expected = {"SCHEMATIC_CONTAINMENT:R_LEFT", "SCHEMATIC_CONTAINMENT:R_RIGHT", "SCHEMATIC_CONTAINMENT:R_TOP", "SCHEMATIC_CONTAINMENT:R_BOTTOM"}
        self.assertTrue(expected.issubset(self.ids(result)))
        self.assertEqual(result["rating"], RATING_UNSUITABLE)
        left = next(f for f in result["findings"] if f["id"] == "SCHEMATIC_CONTAINMENT:R_LEFT")
        self.assertEqual(left["severity"], "blocker")
        self.assertEqual(left["confidence"], "high")
        ev = left["evidence"][0]
        self.assertEqual(ev["ref"], "R_LEFT")
        self.assertEqual(ev["xMm"], -5.0)
        self.assertEqual(ev["yMm"], 50.0)
        self.assertEqual(ev["pageWidthMm"], 100)
        self.assertEqual(ev["pageHeightMm"], 100)
        self.assertEqual(ev["pageXMinMm"], 0.0)
        self.assertEqual(ev["pageXMaxMm"], 100.0)
        bottom = next(f for f in result["findings"] if f["id"] == "SCHEMATIC_CONTAINMENT:R_BOTTOM")
        self.assertEqual(bottom["evidence"][0]["yMm"], -5.0)
        self.assertEqual(bottom["evidence"][0]["pageYMinMm"], 0.0)

    def test_units_per_mm_conversion(self):
        sheet = {"widthMm": 297, "heightMm": 210, "originXmm": 0, "originYmm": 0, "unitsPerMm": 3.937}
        d = self.containment_design(
            [
                {"ref": "U_IN", "x": 400, "y": -400},      # 101.6, -101.6 mm: inside only after units->mm
                {"ref": "U_RIGHT", "x": 1200, "y": -400},  # 304.8 mm: right of page
                {"ref": "U_LEFT", "x": -100, "y": -400},   # -25.4 mm: left of page
                {"ref": "U_TOP", "x": 400, "y": 50},       # 12.7 mm: above page top (y=0)
                {"ref": "U_BOTTOM", "x": 400, "y": -900},  # -228.6 mm: below page bottom (y=-210)
            ],
            sheet,
        )
        result = self.review(d)
        self.assertNotIn("SCHEMATIC_CONTAINMENT:U_IN", self.ids(result))
        self.assertIn("SCHEMATIC_CONTAINMENT:U_RIGHT", self.ids(result))
        self.assertIn("SCHEMATIC_CONTAINMENT:U_LEFT", self.ids(result))
        self.assertIn("SCHEMATIC_CONTAINMENT:U_TOP", self.ids(result))
        self.assertIn("SCHEMATIC_CONTAINMENT:U_BOTTOM", self.ids(result))
        right = next(f for f in result["findings"] if f["id"] == "SCHEMATIC_CONTAINMENT:U_RIGHT")
        self.assertAlmostEqual(right["evidence"][0]["xMm"], 304.8, delta=0.01)
        top = next(f for f in result["findings"] if f["id"] == "SCHEMATIC_CONTAINMENT:U_TOP")
        self.assertAlmostEqual(top["evidence"][0]["yMm"], 12.7, delta=0.01)
        self.assertEqual(top["evidence"][0]["unitsPerMm"], 3.937)

    def test_missing_schematic_sheet_is_silent(self):
        d = self.containment_design([{"ref": "C1", "x": 200, "y": -200}], None)
        result = self.review(d)
        self.assertEqual(self.containment_ids(result), set())
        self.assertNotIn("CONTAINMENT_DATA_MISSING", self.ids(result))
        self.assertEqual(result["rating"], RATING_SUITABLE)
        self.assertEqual(result["counts"], {"pass": 0, "advisory": 0, "blocker": 0})

    def test_missing_coordinates_are_not_guessed(self):
        d = self.containment_design(
            [{"ref": "C_NO_XY_1", "nets": []}, {"ref": "C_NO_XY_2", "nets": []}],
            {"widthMm": 100, "heightMm": 100, "originXmm": 0, "originYmm": 100},
        )
        result = self.review(d)
        self.assertEqual(self.containment_ids(result), set())
        self.assertIn("CONTAINMENT_DATA_MISSING:C_NO_XY_1", self.ids(result))
        self.assertIn("CONTAINMENT_DATA_MISSING:C_NO_XY_2", self.ids(result))
        self.assertEqual(result["rating"], RATING_FIX_FIRST)

    def test_partial_coordinates_suppress_aggregate_pass(self):
        d = self.containment_design(
            [{"ref": "C_HAS_XY", "x": 50, "y": 50}, {"ref": "C_NO_XY", "nets": []}],
            {"widthMm": 100, "heightMm": 100, "originXmm": 0, "originYmm": 100},
        )
        result = self.review(d)
        self.assertNotIn("SCHEMATIC_CONTAINMENT", self.ids(result))  # no aggregate pass
        self.assertNotIn("SCHEMATIC_CONTAINMENT:C_HAS_XY", self.ids(result))
        self.assertIn("CONTAINMENT_DATA_MISSING:C_NO_XY", self.ids(result))

    def test_external_containment_short_circuits_geometry(self):
        inside = self.containment_design(
            [{"ref": "C1", "x": 50, "y": 50}],
            {"widthMm": 100, "heightMm": 100, "originXmm": 0, "originYmm": 100, "containment": False},
        )
        failed = self.review(inside)
        self.assertEqual(failed["rating"], RATING_UNSUITABLE)
        finding = next(f for f in failed["findings"] if f["id"] == "SCHEMATIC_CONTAINMENT")
        self.assertEqual(finding["severity"], "blocker")
        self.assertEqual(finding["evidence"][0], {"containment": False, "decidedExternally": True})

        outside = self.containment_design(
            [{"ref": "C1", "x": 200, "y": 50}],
            {"widthMm": 100, "heightMm": 100, "originXmm": 0, "originYmm": 100, "containment": True},
        )
        passed = self.review(outside)
        self.assertEqual(passed["rating"], RATING_SUITABLE)
        pass_finding = next(f for f in passed["findings"] if f["id"] == "SCHEMATIC_CONTAINMENT")
        self.assertEqual(pass_finding["severity"], "pass")
        self.assertEqual(pass_finding["evidence"][0], {"containment": True, "decidedExternally": True})

    def test_schematic_containment_coexists_with_decoupling(self):
        d = copy.deepcopy(self.safe)
        d["schematicSheet"] = {"widthMm": 100, "heightMm": 100, "originXmm": 0, "originYmm": 100}
        result = self.review(d)
        self.assertIn("SCHEMATIC_CONTAINMENT", self.ids(result))
        self.assertEqual(self.containment_ids(result), {"SCHEMATIC_CONTAINMENT"})
        self.assertIn("DECOUPLING_PASS:DRV_A:RAW", self.ids(result))
        self.assertEqual(result["rating"], RATING_SUITABLE)

    def test_real_m2_sheet_containment_before_and_after(self):
        # Real 2026-08-10 M2 lesson: components were drawn outside the A4 schematic frame
        # (A4 = 297 x 210 mm, 10 mil/unit, unitsPerMm ~= 1/0.254). Old schematic units span
        # -355..335 (x) and -355..335 (y) vs page x in [0,1170] / y in [-825,0] units.
        before_coordinates = [
            ("J1", -355, -355), ("J2", 335, 335), ("J3", -355, 335),
            ("C1", 335, -355), ("C2", -100, -100), ("C3", 200, 50),
        ]
        before = self.review(self.m2_design(before_coordinates))
        blocker_ids = {i["id"] for i in before["findings"] if i["severity"] == "blocker" and i["id"].startswith("SCHEMATIC_CONTAINMENT:")}
        self.assertEqual(blocker_ids, {"SCHEMATIC_CONTAINMENT:J1", "SCHEMATIC_CONTAINMENT:J2", "SCHEMATIC_CONTAINMENT:J3", "SCHEMATIC_CONTAINMENT:C2", "SCHEMATIC_CONTAINMENT:C3"})
        self.assertNotIn("SCHEMATIC_CONTAINMENT:C1", blocker_ids)  # C1 was inside the page
        self.assertEqual(before["rating"], RATING_UNSUITABLE)
        self.assertNotIn("CONTAINMENT_DATA_MISSING", self.ids(before))

        # After the fix the design lies inside the page: x in [280,890], y in [-620,-200] units
        # (71.1..226.1 mm and -157.5..-50.8 mm in A4 mm coordinates).
        after_coordinates = [
            ("J1", 280, -620), ("J2", 890, -200), ("J3", 280, -200),
            ("C1", 890, -620), ("C2", 500, -400), ("C3", 600, -300),
        ]
        after = self.review(self.m2_design(after_coordinates))
        self.assertEqual(self.containment_ids(after), {"SCHEMATIC_CONTAINMENT"})
        self.assertEqual({i for i in after["findings"] if i["severity"] == "blocker"}, set())
        self.assertEqual(after["rating"], RATING_SUITABLE)

    def test_malformed_schematic_sheet_is_rejected(self):
        cases = [
            {"heightMm": 210},                                    # widthMm missing
            {"widthMm": 0, "heightMm": 210},                      # widthMm must be > 0
            {"widthMm": 297, "heightMm": 210, "unitsPerMm": 0},   # unitsPerMm must be > 0
            {"widthMm": 297, "heightMm": "210"},                  # heightMm must be a number
            {"widthMm": 297, "heightMm": 210, "containment": "yes"},  # containment must be bool
        ]
        for sheet in cases:
            with self.subTest(sheet=sheet):
                d = self.containment_design([{"ref": "C1", "x": 1, "y": 1}], sheet)
                with self.assertRaises(InputValidationError):
                    Review(d, self.profiles).run()


if __name__ == "__main__":
    unittest.main(verbosity=2)
