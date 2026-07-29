import hashlib
import json
import subprocess
import sys
from tests import ArchivedTemporaryDirectory
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "run-review-pipeline.py"
FIXTURE = REPO / "tests" / "review" / "fixtures" / "synthetic-safe-input.json"
PROFILES = REPO / "src" / "review" / "component-profiles.json"
ADAPTER_SCHEMA = "pcb-prototype-quality-gate-readonly-adapter/1.0"
HEALTH_SCHEMA = "pcb-prototype-quality-gate-readonly-adapter-health/1.0"


def health_receipt(status="ready"):
    errors = [] if status == "ready" else [{"class": "upstream_5xx", "message": "gateway returned 502"}]
    return {
        "schema": HEALTH_SCHEMA,
        "status": status,
        "adapter": {"name": "fixture-adapter", "version": "test", "readOnly": True, "edaWrites": 0},
        "probe": {
            "probedAt": "2026-07-29T04:00:00+00:00",
            "transport": {"ok": status == "ready", "httpStatus": 200 if status == "ready" else 502, "contentType": "application/json"},
            "session": {"windowCount": 1, "uniqueTarget": True, "readOnly": True, "edaWrites": 0},
            "response": {"jsonObject": True, "protocolValid": True},
        },
        "errors": errors,
    }


def adapter_envelope(design):
    canonical = json.dumps(design, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    return {
        "schema": ADAPTER_SCHEMA,
        "status": "complete",
        "adapter": {"name": "fixture-adapter", "version": "test", "readOnly": True, "edaWrites": 0},
        "capture": {
            "capturedAt": "2026-07-29T04:00:00+00:00",
            "target": {"projectKeySha256": "a" * 64, "schematicKeySha256": "b" * 64, "pcbKeySha256": "c" * 64},
            "state": {"schematicStateSha256": "d" * 64, "pcbStateSha256": "e" * 64, "normalizedDesignSha256": digest},
            "persistence": {"savedReloaded": True, "independentReadback": True, "targetStable": True},
        },
        "normalizedDesign": design,
        "errors": [],
    }


class ReviewPipelineTests(unittest.TestCase):
    def test_pipeline_reviews_without_eda_or_mutation(self):
        with ArchivedTemporaryDirectory() as name:
            output = Path(name) / "run"
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(FIXTURE), "--profiles", str(PROFILES), "--output", str(output)],
                cwd=REPO,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            run = json.loads((output / "pipeline-run.json").read_text(encoding="utf-8"))
            self.assertEqual(run["schema"], "pcb-prototype-quality-gate-pipeline-run/1.1")
            self.assertEqual(run["status"], "reviewed")
            self.assertFalse(run["trustBoundary"]["edaAccess"])
            self.assertEqual(run["trustBoundary"]["edaWrites"], 0)
            self.assertEqual(run["repair"]["status"], "not-requested")
            self.assertTrue((output / "review" / "machine-review.json").is_file())
            self.assertTrue((output / "normalized-input.json").is_file())

    def test_pipeline_consumes_validated_read_only_adapter_envelope(self):
        design = json.loads(FIXTURE.read_text(encoding="utf-8"))
        with ArchivedTemporaryDirectory() as name:
            root = Path(name)
            input_path = root / "input.json"
            evidence_path = root / "adapter.json"
            output = root / "run"
            input_path.write_text(json.dumps(design, ensure_ascii=False), encoding="utf-8")
            evidence_path.write_text(json.dumps(adapter_envelope(design), ensure_ascii=False), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(input_path), "--profiles", str(PROFILES), "--output", str(output), "--adapter-evidence", str(evidence_path)],
                cwd=REPO, text=True, encoding="utf-8", capture_output=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            run = json.loads((output / "pipeline-run.json").read_text(encoding="utf-8"))
            self.assertEqual(run["trustBoundary"]["currentStateReadback"], "validated-readonly-envelope")
            self.assertEqual(run["inputs"]["adapter"]["state"]["pcbStateSha256"], "e" * 64)

    def test_pipeline_rejects_tampered_adapter_design(self):
        design = json.loads(FIXTURE.read_text(encoding="utf-8"))
        envelope = adapter_envelope(design)
        envelope["normalizedDesign"] = {**design, "designName": "tampered"}
        with ArchivedTemporaryDirectory() as name:
            root = Path(name)
            input_path = root / "input.json"
            evidence_path = root / "adapter.json"
            input_path.write_text(json.dumps(design, ensure_ascii=False), encoding="utf-8")
            evidence_path.write_text(json.dumps(envelope, ensure_ascii=False), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(input_path), "--profiles", str(PROFILES), "--output", str(root / "run"), "--adapter-evidence", str(evidence_path)],
                cwd=REPO, text=True, encoding="utf-8", capture_output=True, check=False,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("normalizedDesignSha256", completed.stderr)

    def test_pipeline_requires_ready_health_when_health_evidence_is_supplied(self):
        with ArchivedTemporaryDirectory() as name:
            root = Path(name)
            health_path = root / "health.json"
            health_path.write_text(json.dumps(health_receipt("blocked"), ensure_ascii=False), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(FIXTURE), "--profiles", str(PROFILES), "--output", str(root / "run"), "--health-evidence", str(health_path)],
                cwd=REPO, text=True, encoding="utf-8", capture_output=True, check=False,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("upstream_5xx", completed.stderr)

    def test_pipeline_records_ready_health_without_granting_eda_access(self):
        with ArchivedTemporaryDirectory() as name:
            root = Path(name)
            health_path = root / "health.json"
            health_path.write_text(json.dumps(health_receipt(), ensure_ascii=False), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(FIXTURE), "--profiles", str(PROFILES), "--output", str(root / "run"), "--health-evidence", str(health_path)],
                cwd=REPO, text=True, encoding="utf-8", capture_output=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            run = json.loads((root / "run" / "pipeline-run.json").read_text(encoding="utf-8"))
            self.assertEqual(run["trustBoundary"]["environmentHealth"], "validated-read-only")
            self.assertFalse(run["trustBoundary"]["edaAccess"])
            self.assertEqual(run["trustBoundary"]["edaWrites"], 0)

    def test_pipeline_rejects_unpaired_repair_arguments(self):
        with ArchivedTemporaryDirectory() as name:
            output = Path(name) / "run"
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(FIXTURE), "--output", str(output), "--goal", "修正"],
                cwd=REPO,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("--repair-evidence", completed.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
