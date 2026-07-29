import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "build-readonly-adapter-envelope.py"
FIXTURE = REPO / "tests" / "review" / "fixtures" / "synthetic-safe-input.json"


class ReadonlyAdapterExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.capture = {
            "capturedAt": "2026-07-29T04:00:00+00:00",
            "target": {"projectKeySha256": "a" * 64, "schematicKeySha256": "b" * 64, "pcbKeySha256": "c" * 64},
            "state": {"schematicStateSha256": "d" * 64, "pcbStateSha256": "e" * 64},
            "persistence": {"savedReloaded": True, "independentReadback": True, "targetStable": True},
        }

    def test_cli_builds_complete_envelope_and_derives_design_digest(self):
        with tempfile.TemporaryDirectory(dir=REPO) as name:
            root = Path(name)
            design = root / "design.json"
            capture = root / "capture.json"
            output = root / "envelope.json"
            design.write_text(json.dumps(self.design, ensure_ascii=False), encoding="utf-8")
            capture.write_text(json.dumps(self.capture, ensure_ascii=False), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--design", str(design), "--capture", str(capture), "--adapter-name", "offline-fixture", "--adapter-version", "1.0", "--output", str(output)],
                cwd=REPO, text=True, encoding="utf-8", capture_output=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            envelope = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(envelope["status"], "complete")
            self.assertEqual(envelope["adapter"]["edaWrites"], 0)
            self.assertEqual(len(envelope["capture"]["state"]["normalizedDesignSha256"]), 64)
            self.assertNotIn("design.json", json.dumps(envelope, ensure_ascii=False))

    def test_complete_export_rejects_capture_with_partial_or_extra_fields(self):
        with tempfile.TemporaryDirectory(dir=REPO) as name:
            root = Path(name)
            design = root / "design.json"
            capture = root / "capture.json"
            design.write_text(json.dumps(self.design, ensure_ascii=False), encoding="utf-8")
            bad_capture = dict(self.capture)
            bad_capture["partialRawResponse"] = {"privateId": "should-not-pass"}
            capture.write_text(json.dumps(bad_capture, ensure_ascii=False), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--design", str(design), "--capture", str(capture), "--adapter-name", "fixture", "--adapter-version", "1", "--output", str(root / "out.json")],
                cwd=REPO, text=True, encoding="utf-8", capture_output=True, check=False,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("keys mismatch", completed.stderr)

    def test_cli_builds_failed_envelope_without_partial_state(self):
        with tempfile.TemporaryDirectory(dir=REPO) as name:
            output = Path(name) / "failed.json"
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--status", "unknown", "--error-class", "timeout_unknown", "--message", "readback timed out", "--adapter-name", "fixture", "--adapter-version", "1", "--output", str(output)],
                cwd=REPO, text=True, encoding="utf-8", capture_output=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            envelope = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(envelope["status"], "unknown")
            self.assertIsNone(envelope["capture"])
            self.assertIsNone(envelope["normalizedDesign"])
            self.assertEqual(envelope["errors"][0]["class"], "timeout_unknown")

    def test_cli_rejects_unknown_failure_class(self):
        with tempfile.TemporaryDirectory(dir=REPO) as name:
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--status", "failed", "--error-class", "made-up", "--message", "bad", "--adapter-name", "fixture", "--adapter-version", "1", "--output", str(Path(name) / "out.json")],
                cwd=REPO, text=True, encoding="utf-8", capture_output=True, check=False,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("unsupported", completed.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
