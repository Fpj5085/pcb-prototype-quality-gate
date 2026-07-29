import json
import unittest

from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src" / "review"))

from readonly_adapter_contract import (  # noqa: E402
    AdapterContractError,
    normalized_design_sha256,
    validate_adapter_envelope,
)


FIXTURE = REPO / "tests" / "review" / "fixtures" / "synthetic-safe-input.json"


def make_envelope(design):
    digest = normalized_design_sha256(design)
    return {
        "schema": "pcb-prototype-quality-gate-readonly-adapter/1.0",
        "status": "complete",
        "adapter": {"name": "contract-fixture", "version": "1.0", "readOnly": True, "edaWrites": 0},
        "capture": {
            "capturedAt": "2026-07-29T04:00:00+00:00",
            "target": {"projectKeySha256": "a" * 64, "schematicKeySha256": "b" * 64, "pcbKeySha256": "c" * 64},
            "state": {"schematicStateSha256": "d" * 64, "pcbStateSha256": "e" * 64, "normalizedDesignSha256": digest},
            "persistence": {"savedReloaded": True, "independentReadback": True, "targetStable": True},
        },
        "normalizedDesign": design,
        "errors": [],
    }


class ReadonlyAdapterContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_complete_envelope_is_accepted_and_digest_is_canonical(self):
        envelope = validate_adapter_envelope(make_envelope(self.design))
        self.assertEqual(envelope["status"], "complete")
        self.assertEqual(len(normalized_design_sha256(self.design)), 64)

    def test_digest_tampering_is_rejected(self):
        envelope = make_envelope(self.design)
        envelope["capture"]["state"]["normalizedDesignSha256"] = "f" * 64
        with self.assertRaisesRegex(AdapterContractError, "normalizedDesignSha256"):
            validate_adapter_envelope(envelope)

    def test_non_read_only_adapter_is_rejected(self):
        envelope = make_envelope(self.design)
        envelope["adapter"]["readOnly"] = False
        with self.assertRaisesRegex(AdapterContractError, "readOnly"):
            validate_adapter_envelope(envelope)

    def test_unknown_or_failed_state_requires_error_and_is_rejected_for_review(self):
        envelope = make_envelope(self.design)
        envelope["status"] = "unknown"
        envelope["capture"] = None
        envelope["normalizedDesign"] = None
        envelope["errors"] = [{"class": "timeout_unknown", "message": "readback timed out"}]
        with self.assertRaisesRegex(AdapterContractError, "timeout_unknown"):
            validate_adapter_envelope(envelope)

    def test_failed_state_rejects_partial_capture_evidence(self):
        envelope = make_envelope(self.design)
        envelope["status"] = "failed"
        envelope["normalizedDesign"] = None
        envelope["errors"] = [{"class": "upstream_5xx", "message": "gateway failed"}]
        with self.assertRaisesRegex(AdapterContractError, "partial capture"):
            validate_adapter_envelope(envelope, require_complete=False)

    def test_error_class_is_allow_listed(self):
        envelope = make_envelope(self.design)
        envelope["errors"] = [{"class": "made_up", "message": "bad"}]
        with self.assertRaisesRegex(AdapterContractError, "unsupported"):
            validate_adapter_envelope(envelope)


if __name__ == "__main__":
    unittest.main(verbosity=2)
