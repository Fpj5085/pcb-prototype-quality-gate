import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "run-review-pipeline.py"
FIXTURE = REPO / "tests" / "review" / "fixtures" / "synthetic-safe-input.json"
PROFILES = REPO / "src" / "review" / "component-profiles.json"


class ReviewPipelineTests(unittest.TestCase):
    def test_pipeline_reviews_without_eda_or_mutation(self):
        with tempfile.TemporaryDirectory(dir=REPO) as name:
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
            self.assertEqual(run["schema"], "pcb-prototype-quality-gate-pipeline-run/1.0")
            self.assertEqual(run["status"], "reviewed")
            self.assertFalse(run["trustBoundary"]["edaAccess"])
            self.assertEqual(run["trustBoundary"]["edaWrites"], 0)
            self.assertEqual(run["repair"]["status"], "not-requested")
            self.assertTrue((output / "review" / "machine-review.json").is_file())
            self.assertTrue((output / "normalized-input.json").is_file())

    def test_pipeline_rejects_unpaired_repair_arguments(self):
        with tempfile.TemporaryDirectory(dir=REPO) as name:
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
