import copy
import json
import sys
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
ENGINE_DIR = REPO / "src" / "review"
EVALS = REPO / "evals"
sys.path.insert(0, str(ENGINE_DIR))

from prototype_review import Review  # noqa: E402


PAIRS = {
    "power-input": {
        "before": "power-input-before",
        "after": "power-input-after",
        "beforeIds": {"POWER_HEADROOM:REG_PWR", "FUSE_HOLD:F_PROT", "TRACE_CAPACITY:SOURCE_PWR"},
        "afterPassIds": {"POWER_HEADROOM_PASS:REG_PWR", "FUSE_PASS:F_PROT", "TRACE_PASS:SOURCE_PWR"},
    },
    "sensor-interface": {
        "before": "sensor-interface-before",
        "after": "sensor-interface-after",
        "beforeIds": {"DECOUPLING_DISTANCE:CTRL_S:V3_S", "LEVEL_MARGIN:SENSOR_LEVEL", "GROUND_RETURN"},
        "afterPassIds": {"DECOUPLING_PASS:CTRL_S:V3_S", "LEVEL_MARGIN:SENSOR_LEVEL", "GROUND_RETURN"},
    },
    "communication-interface": {
        "before": "communication-interface-before",
        "after": "communication-interface-after",
        "beforeIds": {"DEBUG_SIGNALS", "TESTPOINTS", "SILKSCREEN", "SCHEMATIC_TOPOLOGY", "FIRMWARE_PIN_CONFLICT:CTRL_C.1"},
        "afterPassIds": {"DEBUG_PASS", "GROUND_RETURN", "SCHEMATIC_TOPOLOGY"},
    },
}


class DiverseBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = json.loads((ENGINE_DIR / "component-profiles.json").read_text(encoding="utf-8"))

    def load(self, case):
        return json.loads((EVALS / case / "input.json").read_text(encoding="utf-8"))

    def review(self, case):
        return Review(self.load(case), self.profiles).run()

    def ids(self, result):
        return {row["id"] for row in result["findings"]}

    def test_each_before_is_unsuitable_and_after_has_low_risk_forecast(self):
        for family, pair in PAIRS.items():
            with self.subTest(family=family):
                before = self.review(pair["before"])
                after = self.review(pair["after"])
                self.assertEqual(before["rating"], "not_suitable_for_prototype")
                self.assertEqual(before["engineeringForecastRating"], "not_suitable_for_prototype")
                self.assertEqual(after["rating"], "suitable_after_corrections")
                self.assertEqual(after["engineeringForecastRating"], "suitable_for_low_risk_prototype")
                self.assertTrue(pair["beforeIds"].issubset(self.ids(before)))
                self.assertTrue(pair["afterPassIds"].issubset(self.ids(after)))
                self.assertEqual(after["counts"]["blocker"], 0)

    def test_all_six_are_explicit_offline_zero_write_fixtures(self):
        for pair in PAIRS.values():
            for case in (pair["before"], pair["after"]):
                with self.subTest(case=case):
                    manifest = json.loads((EVALS / case / "manifest.json").read_text(encoding="utf-8"))
                    design = self.load(case)
                    self.assertEqual(manifest["fixtureKind"], "synthetic-benchmark")
                    self.assertFalse(manifest["execution"]["liveEdaVerified"])
                    self.assertFalse(manifest["execution"]["liveSaveReloadVerified"])
                    self.assertEqual(manifest["execution"]["edaWritesInThisReleaseFixture"], 0)
                    self.assertFalse(design["fixtureMetadata"]["liveEdaVerified"])
                    self.assertFalse(design["fixtureMetadata"]["persistenceEvidenceIncluded"])
                    self.assertNotIn("savedReloaded", design["checks"])

    def test_component_and_net_order_does_not_change_results(self):
        for pair in PAIRS.values():
            for case in (pair["before"], pair["after"]):
                with self.subTest(case=case):
                    design = self.load(case)
                    reordered = copy.deepcopy(design)
                    reordered["components"] = list(reversed(reordered["components"]))
                    reordered["nets"] = list(reversed(reordered["nets"]))
                    normal = Review(design, self.profiles).run()
                    changed = Review(reordered, self.profiles).run()
                    self.assertEqual(normal["rating"], changed["rating"])
                    self.assertEqual(normal["engineeringForecastRating"], changed["engineeringForecastRating"])
                    self.assertEqual(normal["counts"], changed["counts"])
                    self.assertEqual(self.ids(normal), self.ids(changed))

    def test_after_fixtures_do_not_gain_mutation_or_manufacturing_claims(self):
        forbidden_text = ("changeset", "manufacturing release", "order", "payment", "live write")
        for pair in PAIRS.values():
            case = pair["after"]
            text = (EVALS / case / "input.json").read_text(encoding="utf-8").lower()
            manifest_text = (EVALS / case / "manifest.json").read_text(encoding="utf-8").lower()
            with self.subTest(case=case):
                for term in forbidden_text:
                    self.assertNotIn(term, text)
                    self.assertNotIn(term, manifest_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
