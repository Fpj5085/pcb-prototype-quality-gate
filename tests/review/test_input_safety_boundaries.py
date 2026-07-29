import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ENGINE_DIR = REPO / "src" / "review"
FIXTURES = HERE / "fixtures"
sys.path.insert(0, str(ENGINE_DIR))

from prototype_review import InputValidationError, Review, read_json, validate_design, validate_profiles  # noqa: E402


class InputSafetyBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.safe = json.loads((FIXTURES / "synthetic-safe-input.json").read_text(encoding="utf-8"))
        cls.profiles = json.loads((ENGINE_DIR / "component-profiles.json").read_text(encoding="utf-8"))

    def assert_rejected(self, design, message):
        with self.assertRaisesRegex(InputValidationError, message):
            Review(design, self.profiles).run()

    def test_non_finite_engineering_values_are_rejected_before_review(self):
        cases = [
            ("powerPaths", 0, "sourceMinV", float("nan")),
            ("protectedCircuits", 0, "continuousCurrentA", float("inf")),
            ("regulatorUses", 0, "loadMaxA", float("-inf")),
            ("hbridgeUses", 0, "perChannelRunA", float("nan")),
            ("decouplingRequirements", 0, "maxDistanceMm", float("inf")),
            ("bulkCapRequirements", 0, "minCapacitanceUf", float("nan")),
            ("voltageDividers", 0, "topOhm", float("inf")),
        ]
        for section, index, field, value in cases:
            with self.subTest(section=section, field=field):
                design = copy.deepcopy(self.safe)
                design[section][index][field] = value
                self.assert_rejected(design, rf"input\.{section}\[{index}\]\.{field} must be a finite JSON number")

    def test_json_reader_rejects_nan_and_infinity_tokens(self):
        for token in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(token=token), tempfile.TemporaryDirectory() as temp_name:
                path = Path(temp_name) / "input.json"
                path.write_text('{"value": ' + token + "}\n", encoding="utf-8")
                with self.assertRaisesRegex(InputValidationError, "non-standard JSON numeric constant"):
                    read_json(path)

    def test_boolean_values_cannot_masquerade_as_numbers(self):
        cases = [
            ("components", 0, "x"),
            ("components", 5, "capacitanceUf"),
            ("nets", 0, "designCurrentA"),
            ("powerPaths", 0, "sourceMinV"),
            ("hbridgeUses", 0, "channelsUsed"),
        ]
        for section, index, field in cases:
            with self.subTest(section=section, field=field):
                design = copy.deepcopy(self.safe)
                design[section][index][field] = True
                self.assert_rejected(design, rf"input\.{section}\[{index}\]\.{field} must be")

    def test_invalid_confidence_and_finding_severity_are_rejected(self):
        design = copy.deepcopy(self.safe)
        design["groundReview"]["confidence"] = "unknown"
        self.assert_rejected(design, "input.groundReview.confidence must be low, medium or high")

        design = copy.deepcopy(self.safe)
        design["voltageDividers"][0]["confidence"] = "certain"
        self.assert_rejected(design, r"input\.voltageDividers\[0\]\.confidence must be low, medium or high")

        design = copy.deepcopy(self.safe)
        design["decouplingRequirements"][0]["severity"] = "pass"
        self.assert_rejected(design, r"input\.decouplingRequirements\[0\]\.severity must be blocker or advisory")

    def test_missing_required_calculation_inputs_are_not_defaulted_to_zero(self):
        cases = [
            ("powerPaths", "sourceMinV"),
            ("protectedCircuits", "continuousCurrentA"),
            ("regulatorUses", "inputMaxV"),
            ("hbridgeUses", "perChannelRunA"),
            ("bulkCapRequirements", "minCapacitanceUf"),
            ("voltageDividers", "receiverAbsMaxV"),
        ]
        for section, field in cases:
            with self.subTest(section=section, field=field):
                design = copy.deepcopy(self.safe)
                del design[section][0][field]
                self.assert_rejected(design, rf"input\.{section}\[0\]\.{field} is required")

    def test_inverted_or_physically_invalid_ranges_are_rejected(self):
        cases = [
            ("powerPaths", {"sourceMinV": 8.0, "sourceMaxV": 7.0}, "sourceMaxV must be >= sourceMinV"),
            ("protectedCircuits", {"continuousCurrentA": 2.0, "surgeCurrentA": 1.0}, "surgeCurrentA must be >= continuousCurrentA"),
            ("regulatorUses", {"cautionRiseC": 80, "blockerRiseC": 50}, "blockerRiseC must be >= cautionRiseC"),
            ("hbridgeUses", {"perChannelRunA": 1.0, "perChannelPeakA": 0.5}, "perChannelPeakA must be >= perChannelRunA"),
            ("decouplingRequirements", {"minCapacitanceUf": 1.0, "maxCapacitanceUf": 0.1}, "maxCapacitanceUf must be >= minCapacitanceUf"),
            ("voltageDividers", {"topOhm": 0}, "topOhm must be > 0"),
        ]
        for section, update, message in cases:
            with self.subTest(section=section):
                design = copy.deepcopy(self.safe)
                design[section][0].update(update)
                self.assert_rejected(design, message)

    def test_assumptions_must_be_explicit_non_empty_strings(self):
        for value in ("unknown", [""], [1]):
            with self.subTest(value=value):
                design = copy.deepcopy(self.safe)
                design["powerPaths"][0]["assumptions"] = value
                self.assert_rejected(design, r"input\.powerPaths\[0\]\.assumptions")

    def test_declared_assumption_remains_visible_even_when_rule_passes(self):
        design = copy.deepcopy(self.safe)
        design["powerPaths"][0]["assumptions"] = ["minimum source voltage is supplier-declared"]
        result = Review(design, self.profiles).run()
        finding = next(row for row in result["findings"] if row["id"] == "POWER_HEADROOM_PASS:PWR_A")
        self.assertEqual(finding["unresolvedAssumptions"], ["minimum source voltage is supplier-declared"])
        self.assertIn("minimum source voltage is supplier-declared", result["unresolvedAssumptions"])

    def test_finding_confidence_cannot_exceed_profile_source_confidence(self):
        profiles = copy.deepcopy(self.profiles)
        profiles["profiles"]["safe.regulator_5v"]["source"]["confidence"] = "medium"
        result = Review(copy.deepcopy(self.safe), profiles).run()
        finding = next(row for row in result["findings"] if row["id"] == "POWER_HEADROOM_PASS:PWR_A")
        thermal = next(row for row in result["findings"] if row["id"] == "REGULATOR_THERMAL:PWR_A")
        self.assertEqual(finding["confidence"], "medium")
        self.assertEqual(thermal["confidence"], "medium")

    def test_profile_numeric_limits_are_finite_and_physically_ordered(self):
        profiles = copy.deepcopy(self.profiles)
        profiles["profiles"]["safe.fuse"]["holdCurrentA"] = float("nan")
        with self.assertRaisesRegex(InputValidationError, "profile 'safe.fuse'.holdCurrentA must be a finite JSON number"):
            validate_profiles(profiles)

        profiles = copy.deepcopy(self.profiles)
        profiles["profiles"]["safe.hbridge"]["peakCurrentPerChannelA"] = 1.0
        profiles["profiles"]["safe.hbridge"]["continuousCurrentPerChannelA"] = 2.0
        with self.assertRaisesRegex(InputValidationError, "peakCurrentPerChannelA must be >= continuousCurrentPerChannelA"):
            validate_profiles(profiles)

    def test_optional_object_containers_are_rejected_when_wrong_or_incomplete(self):
        cases = [
            ("pcb", [], r"input\.pcb must be a JSON object"),
            ("groundReview", {}, r"input\.groundReview\.pours must be a JSON integer"),
            ("schematicTopology", {}, r"input\.schematicTopology\.floatingInputs must be a JSON array"),
            ("debugInterface", [], r"input\.debugInterface must be a JSON object"),
            ("usability", [], r"input\.usability must be a JSON object"),
        ]
        for field, value, message in cases:
            with self.subTest(field=field):
                design = copy.deepcopy(self.safe)
                design[field] = value
                self.assert_rejected(design, message)

    def test_debug_usability_and_firmware_rows_are_validated_before_rules(self):
        cases = [
            ("debugInterface", {"requiredSignals": "GND", "presentSignals": []}, r"input\.debugInterface\.requiredSignals"),
            ("usability", {"missingTestpointNets": "VCC"}, r"input\.usability\.missingTestpointNets"),
            ("usability", {"antennaKeepout": {"verified": "yes"}}, r"input\.usability\.antennaKeepout\.verified"),
            ("firmwarePins", [{}], r"input\.firmwarePins\[0\]\.pin"),
            ("firmwarePins", [{"pin": "U1.1", "net": 3}], r"input\.firmwarePins\[0\]\.net"),
        ]
        for field, value, message in cases:
            with self.subTest(field=field):
                design = copy.deepcopy(self.safe)
                design[field] = value
                self.assert_rejected(design, message)

    def test_existing_safe_fixture_remains_valid_and_suitable(self):
        validated = validate_design(copy.deepcopy(self.safe))
        result = Review(validated, self.profiles).run()
        self.assertEqual(result["rating"], "suitable_for_low_risk_prototype")
        self.assertEqual(result["engineeringForecastRating"], "suitable_for_low_risk_prototype")


if __name__ == "__main__":
    unittest.main(verbosity=2)
