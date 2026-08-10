"""End-to-end regression coverage for the one-command closed-loop demo.

The demo script (`scripts/run-closed-loop-demo.py`) now auto-converts the
requirements-gate hardware contract into review input via
`src/spec/contract_to_review.py`, so the default run needs no prefab design
data and must fail-closed to a PERSISTENCE blocker (no offline save/reload
evidence) plus three data-completeness advisories. The explicit ``--design``
override keeps the old prefab path and must still produce the historical
``DECOUPLING_DISTANCE:J2:+5V`` finding.
"""

import contextlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

from tests import ArchivedTemporaryDirectory


REPO = Path(__file__).resolve().parents[2]
DEMO = REPO / "scripts" / "run-closed-loop-demo.py"
DESIGN_DATA = REPO / "examples" / "m2-closed-loop" / "design-data.json"
PIN = "2026-08-09T00:00:00+00:00"


@contextlib.contextmanager
def run_demo(*extra_args):
    """Run the demo inside an archived workspace and yield (completed, out_dir).

    The workspace directory is archived (moved, never deleted) only when the
    ``with`` block exits, so reading the generated files inside the block is
    safe.
    """
    with ArchivedTemporaryDirectory(prefix="closed-loop-demo-") as name:
        output = Path(name) / "out"
        yield invoke_demo(output, *extra_args), output


@contextlib.contextmanager
def archived_workspace():
    """Yield (out_dir, root) inside an archived workspace located outside the repo."""
    with ArchivedTemporaryDirectory(prefix="closed-loop-demo-") as name:
        root = Path(name)
        yield root / "out", root


def invoke_demo(output: Path, *extra_args):
    """Run the demo once with a fixed timestamp, capturing stdout/stderr."""
    return subprocess.run(
        [sys.executable, "-B", str(DEMO), "--now", PIN, "--out", str(output), *extra_args],
        cwd=REPO,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )


class ClosedLoopDemoTests(unittest.TestCase):
    def test_default_run_auto_converts_and_fails_closed(self):
        with run_demo() as (completed, output):
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            self.assertIn("not_suitable_for_prototype", completed.stdout)
            self.assertIn("PERSISTENCE", completed.stdout)
            self.assertNotIn("DECOUPLING_DISTANCE", completed.stdout)
            # review input was auto-converted from the contract, not prefab
            review_input = json.loads((output / "review-input.json").read_text(encoding="utf-8"))
            self.assertEqual(review_input["schema"], "jlceda-prototype-review-input/1.0")
            for component in review_input["components"]:
                self.assertNotIn("capacitanceUf", component)
            for net in review_input["nets"]:
                self.assertNotIn("minWidthMm", net)
            self.assertNotIn("decouplingRequirements", review_input)
            # the converted input drives the deterministic review to the expected
            # fail-closed outcome: 1 PERSISTENCE blocker + 3 data-completeness advisories
            result = json.loads((output / "machine-review.json").read_text(encoding="utf-8"))
            self.assertEqual(result["rating"], "not_suitable_for_prototype")
            self.assertEqual(result["counts"], {"pass": 0, "advisory": 3, "blocker": 1})
            ids = [finding["id"] for finding in result["findings"]]
            self.assertEqual(
                [finding["id"] for finding in result["findings"] if finding["severity"] == "blocker"],
                ["PERSISTENCE"],
            )
            self.assertEqual(
                sorted(finding["id"] for finding in result["findings"] if finding["severity"] == "advisory"),
                ["EVIDENCE_SCOPE:OFFLINE_FORECAST", "TRACE_DATA_MISSING:+5V", "TRACE_DATA_MISSING:GND"],
            )
            self.assertNotIn("DECOUPLING_DISTANCE", ids)
            # the summary documents the auto-conversion chain and the honest
            # fail-closed blocker (the real-loop history may mention the historical
            # DECOUPLING finding separately, so only the offline audit line is asserted)
            summary = (output / "demo-summary.zh.md").read_text(encoding="utf-8")
            self.assertIn("自动转换", summary)
            self.assertIn("PERSISTENCE", summary)
            self.assertIn("设计数据:由需求门禁产出的", summary)

    def test_explicit_design_keeps_old_prefab_path(self):
        with run_demo("--design", str(DESIGN_DATA)) as (completed, output):
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            self.assertIn("DECOUPLING_DISTANCE:J2:+5V", completed.stdout)
            # the explicit design is used directly: no auto-conversion artifact
            self.assertFalse((output / "review-input.json").exists())
            result = json.loads((output / "machine-review.json").read_text(encoding="utf-8"))
            self.assertEqual(result["rating"], "not_suitable_for_prototype")
            self.assertEqual(result["counts"], {"pass": 3, "advisory": 2, "blocker": 1})
            self.assertEqual(
                [finding["id"] for finding in result["findings"] if finding["severity"] == "blocker"],
                ["DECOUPLING_DISTANCE:J2:+5V"],
            )
            # the summary must not contradict the audit section: no default-path
            # fail-closed blocker or data-missing markers appear, and the
            # explicit-design note does (the advisory EVIDENCE_INCOMPLETE:PERSISTENCE
            # is a legitimate --design-path finding, so only the default-path
            # blocker line and the TRACE_DATA_MISSING markers are asserted)
            summary = (output / "demo-summary.zh.md").read_text(encoding="utf-8")
            self.assertNotIn("`PERSISTENCE` ——", summary)
            self.assertNotIn("TRACE_DATA_MISSING", summary)
            self.assertIn("显式 `--design`", summary)
            self.assertIn("显式提供的完整设计数据样例", summary)

    def test_out_of_repo_design_path_works(self):
        # A --design path outside the repository (absolute path on Windows)
        # must not crash on path rendering; the file-name fallback is used.
        with archived_workspace() as (output, root):
            outside = root / "outside-design.json"
            outside.write_bytes(DESIGN_DATA.read_bytes())
            completed = invoke_demo(output, "--design", str(outside))
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            self.assertNotIn("Traceback", completed.stderr + completed.stdout)
            self.assertIn("DECOUPLING_DISTANCE:J2:+5V", completed.stdout)
            summary = (output / "demo-summary.zh.md").read_text(encoding="utf-8")
            self.assertNotIn("`PERSISTENCE` ——", summary)
            self.assertNotIn("TRACE_DATA_MISSING", summary)
            self.assertIn("显式 `--design`", summary)

    def test_missing_design_exits_2_without_half_output(self):
        # A nonexistent --design file fails cleanly (exit 2, no traceback) and
        # leaves no half-written artifacts behind.
        with archived_workspace() as (output, root):
            missing = root / "missing-design.json"
            self.assertFalse(missing.exists())
            completed = invoke_demo(output, "--design", str(missing))
            self.assertEqual(completed.returncode, 2)
            self.assertNotIn("Traceback", completed.stderr + completed.stdout)
            self.assertIn("--design file not found", completed.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
