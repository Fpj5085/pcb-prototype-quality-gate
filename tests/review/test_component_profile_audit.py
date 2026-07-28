import copy
import importlib.util
import json
import sys
import unittest
from datetime import date
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
ENGINE_DIR = REPO / "src" / "review"

spec = importlib.util.spec_from_file_location("component_profile_audit", ENGINE_DIR / "component_profile_audit.py")
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit
assert spec.loader is not None
spec.loader.exec_module(audit)


class ComponentProfileAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = json.loads((ENGINE_DIR / "component-profiles.json").read_text(encoding="utf-8"))

    def valid_source(self, *, source_type="official_datasheet"):
        if source_type == "synthetic_fixture":
            return {
                "manufacturer": "Synthetic fixture",
                "title": "synthetic-safe-test",
                "url": None,
                "pageOrTable": "table 1",
                "confidence": "high",
                "redistribution": "original synthetic test data",
                "sourceType": source_type,
                "documentRevision": "fixture-1",
                "provenanceStatement": "Values are original synthetic test data.",
                "retrievedAt": "2026-07-01",
                "maxAgeDays": 365,
            }
        return {
            "manufacturer": "Example Semiconductor",
            "title": "Example device datasheet",
            "url": "https://example.invalid/datasheet.pdf",
            "pageOrTable": "page 4, electrical characteristics",
            "confidence": "high",
            "redistribution": "link-only; datasheet PDF not bundled",
            "sourceType": source_type,
            "documentRevision": "Rev 1.2",
            "provenanceStatement": "Numeric limits are transcribed from the linked official datasheet.",
            "retrievedAt": "2026-07-01",
            "maxAgeDays": 365,
        }

    def document(self, source=None):
        return {"schema": "jlceda-component-profiles/1.0", "profiles": {"test.example": {"kind": "test", "source": source or self.valid_source()}}}

    def test_complete_official_source_passes(self):
        result = audit.audit_profiles(self.document(), date(2026, 7, 28))
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["findingCount"], 0)
        self.assertEqual(result["states"], {"fresh": 1, "stale": 0, "invalid": 0})

    def test_complete_synthetic_source_passes_without_url(self):
        result = audit.audit_profiles(self.document(self.valid_source(source_type="synthetic_fixture")), date(2026, 7, 28))
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["sourceTypeCounts"]["synthetic_fixture"], 1)

    def test_missing_provenance_fails_closed(self):
        source = self.valid_source()
        del source["documentRevision"]
        del source["retrievedAt"]
        result = audit.audit_profiles(self.document(source), date(2026, 7, 28))
        codes = {item["code"] for item in result["findings"]}
        self.assertEqual(result["status"], "fail")
        self.assertIn("PROVENANCE_FIELD_MISSING", codes)
        self.assertIn("RETRIEVED_AT_INVALID", codes)

    def test_invalid_and_future_dates_fail(self):
        for field, value, expected in (
            ("retrievedAt", "2026-02-30", "RETRIEVED_AT_INVALID"),
            ("retrievedAt", "2026-08-01", "RETRIEVED_AT_FUTURE"),
            ("reviewAfter", "2026-13-01", "REVIEW_AFTER_INVALID"),
        ):
            with self.subTest(field=field, value=value):
                source = self.valid_source()
                source[field] = value
                result = audit.audit_profiles(self.document(source), date(2026, 7, 28))
                self.assertIn(expected, {item["code"] for item in result["findings"]})

    def test_expired_source_fails_and_is_marked_stale(self):
        source = self.valid_source()
        source["reviewAfter"] = "2026-07-27"
        result = audit.audit_profiles(self.document(source), date(2026, 7, 28))
        self.assertEqual(result["status"], "fail")
        self.assertIn("SOURCE_STALE", {item["code"] for item in result["findings"]})
        self.assertEqual(result["states"], {"fresh": 0, "stale": 1, "invalid": 0})

    def test_official_source_requires_https_and_location(self):
        source = self.valid_source()
        source["url"] = "http://example.invalid/datasheet.pdf"
        source["pageOrTable"] = ""
        result = audit.audit_profiles(self.document(source), date(2026, 7, 28))
        codes = {item["code"] for item in result["findings"]}
        self.assertIn("OFFICIAL_HTTPS_URL_REQUIRED", codes)
        self.assertIn("SOURCE_LOCATION_MISSING", codes)

    def test_synthetic_source_must_declare_origin(self):
        source = self.valid_source(source_type="synthetic_fixture")
        source["redistribution"] = "link-only"
        source["url"] = "https://example.invalid/not-allowed"
        result = audit.audit_profiles(self.document(source), date(2026, 7, 28))
        codes = {item["code"] for item in result["findings"]}
        self.assertIn("SYNTHETIC_URL_MUST_BE_NULL", codes)
        self.assertIn("SYNTHETIC_ORIGIN_UNCLEAR", codes)

    def test_max_age_is_conservative_and_bounded(self):
        source = self.valid_source()
        source["maxAgeDays"] = 30
        result = audit.audit_profiles(self.document(source), date(2026, 8, 1))
        self.assertIn("SOURCE_STALE", {item["code"] for item in result["findings"]})
        source = self.valid_source()
        source["maxAgeDays"] = 0
        result = audit.audit_profiles(self.document(source), date(2026, 7, 28))
        self.assertIn("MAX_AGE_DAYS_INVALID", {item["code"] for item in result["findings"]})

    def test_not_stated_revision_requires_basis(self):
        source = self.valid_source()
        source["documentRevision"] = "not stated"
        result = audit.audit_profiles(self.document(source), date(2026, 7, 28))
        self.assertIn("REVISION_BASIS_MISSING", {item["code"] for item in result["findings"]})
        source["revisionBasis"] = "Official URL has no revision label; retrieval date is recorded."
        result = audit.audit_profiles(self.document(source), date(2026, 7, 28))
        self.assertEqual(result["status"], "pass")

    def test_output_is_deterministic_for_profile_order(self):
        first = self.document(self.valid_source())
        first["profiles"]["test.alpha"] = {"kind": "test", "source": self.valid_source()}
        second = {"schema": first["schema"], "profiles": {}}
        for key in reversed(list(first["profiles"])):
            second["profiles"][key] = copy.deepcopy(first["profiles"][key])
        result_one = audit.audit_profiles(first, date(2026, 7, 28))
        result_two = audit.audit_profiles(second, date(2026, 7, 28))
        self.assertEqual(result_one, result_two)


if __name__ == "__main__":
    unittest.main(verbosity=2)
