import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "validate-readonly-adapter-health.py"


def receipt(status="ready"):
    errors = [] if status == "ready" else [{"class": "upstream_5xx", "message": "gateway returned 502"}]
    return {
        "schema": "pcb-prototype-quality-gate-readonly-adapter-health/1.0",
        "status": status,
        "adapter": {"name": "bridge-probe", "version": "1.0", "readOnly": True, "edaWrites": 0},
        "probe": {
            "probedAt": "2026-07-29T05:40:00+00:00",
            "transport": {"ok": status == "ready", "httpStatus": 200 if status == "ready" else 502, "contentType": "application/json"},
            "session": {"windowCount": 1, "uniqueTarget": True, "readOnly": True, "edaWrites": 0},
            "response": {"jsonObject": True, "protocolValid": True},
        },
        "errors": errors,
    }


class ReadonlyAdapterHealthTests(unittest.TestCase):
    def run_cli(self, payload, *extra):
        with tempfile.TemporaryDirectory(dir=REPO) as name:
            path = Path(name) / "health.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return subprocess.run([sys.executable, str(SCRIPT), "--input", str(path), *extra], cwd=REPO, text=True, encoding="utf-8", capture_output=True, check=False)

    def test_ready_probe_clears_gate(self):
        completed = self.run_cli(receipt())
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn('"status": "ready"', completed.stdout)

    def test_502_is_blocked_by_default(self):
        completed = self.run_cli(receipt("blocked"))
        self.assertEqual(completed.returncode, 2)
        self.assertIn("upstream_5xx", completed.stdout)

    def test_blocked_probe_is_diagnostic_only_when_explicit(self):
        completed = self.run_cli(receipt("blocked"), "--allow-blocked")
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("diagnostic-only", completed.stdout)

    def test_ready_rejects_multiple_windows(self):
        value = receipt()
        value["probe"]["session"]["windowCount"] = 2
        completed = self.run_cli(value)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("one unique read-only", completed.stdout)

    def test_ready_rejects_write_capability_or_count(self):
        value = receipt()
        value["adapter"]["readOnly"] = False
        completed = self.run_cli(value)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("readOnly", completed.stdout)

    def test_unknown_error_class_is_rejected(self):
        value = receipt("blocked")
        value["errors"][0]["class"] = "made-up"
        completed = self.run_cli(value, "--allow-blocked")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("unsupported", completed.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
