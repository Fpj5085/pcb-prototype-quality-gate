import copy
import json
import re
import subprocess
import sys
from tests import ArchivedTemporaryDirectory
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ENGINE_DIR = REPO / "src" / "review"
EVALS = REPO / "evals"
SCHEMAS = REPO / "schemas"
ENGINE = ENGINE_DIR / "prototype_review.py"
EVAL_RUNNER = REPO / "scripts" / "run-evals.py"
sys.path.insert(0, str(ENGINE_DIR))

from prototype_review import (  # noqa: E402
    InputValidationError,
    Review,
    RATING_FIX_FIRST,
    RATING_SUITABLE,
    RATING_UNSUITABLE,
    sanitize_public_value,
    validate_design,
    validate_profiles,
)


class ReleaseRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = json.loads((ENGINE_DIR / "component-profiles.json").read_text(encoding="utf-8"))
        cls.safe = json.loads((HERE / "fixtures" / "synthetic-safe-input.json").read_text(encoding="utf-8"))
        cls.temporary = ArchivedTemporaryDirectory(prefix="release-runtime-")
        cls.temp_root = Path(cls.temporary.name)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_all_json_schemas_parse(self):
        schema_paths = sorted(SCHEMAS.glob("*.schema.json"))
        self.assertGreaterEqual(len(schema_paths), 10)
        for path in schema_paths:
            with self.subTest(path=path.name):
                schema = json.loads(path.read_text(encoding="utf-8-sig"))
                self.assertEqual(schema.get("$schema"), "https://json-schema.org/draft/2020-12/schema")
                self.assertEqual(schema.get("type"), "object")

    def test_design_and_profile_validation(self):
        self.assertEqual(validate_design(copy.deepcopy(self.safe))["components"][0]["ref"], "PWR_A")
        self.assertIn("profiles", validate_profiles(self.profiles))
        duplicate = copy.deepcopy(self.safe)
        duplicate["components"].append(copy.deepcopy(duplicate["components"][0]))
        with self.assertRaisesRegex(InputValidationError, "duplicate"):
            validate_design(duplicate)

    def test_all_ten_eval_replays_match_expected(self):
        completed = subprocess.run(
            [sys.executable, str(EVAL_RUNNER)],
            cwd=self.temp_root,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        replay = json.loads(completed.stdout)
        self.assertEqual(replay["status"], "pass")
        self.assertEqual(
            {case["id"] for case in replay["cases"]},
            {
                "power-distribution-before",
                "power-distribution-after",
                "car-controller-adversarial",
                "synthetic-safe",
                "power-input-before",
                "power-input-after",
                "sensor-interface-before",
                "sensor-interface-after",
                "communication-interface-before",
                "communication-interface-after",
            },
        )
        self.assertTrue(all(case["status"] == "pass" for case in replay["cases"]))

    def test_before_after_keep_offline_fixtures_separate_from_verified_live_summary(self):
        summary_path = REPO / "release-audit" / "m2-live-evidence-summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["gate"], "verified")
        self.assertTrue(summary["liveEdaVerified"])
        self.assertTrue(summary["liveSaveReloadVerified"])
        self.assertFalse(summary["privacy"]["rawEvidenceCopied"])
        self.assertFalse(summary["privacy"]["workstationPathsIncluded"])
        self.assertFalse(summary["privacy"]["privateIdentifiersIncluded"])

        for case_name in ("power-distribution-before", "power-distribution-after"):
            case = EVALS / case_name
            manifest = json.loads((case / "manifest.json").read_text(encoding="utf-8"))
            design = json.loads((case / "input.json").read_text(encoding="utf-8"))
            status = json.loads((case / "evidence" / "status.json").read_text(encoding="utf-8"))
            with self.subTest(case=case_name):
                self.assertEqual(manifest["execution"]["status"], "live-evidence-gate-verified")
                self.assertTrue(manifest["execution"]["liveEdaVerified"])
                self.assertTrue(manifest["execution"]["liveSaveReloadVerified"])
                self.assertEqual(manifest["execution"]["edaWritesInThisReleaseFixture"], 0)
                self.assertEqual(
                    manifest["publicLiveEvidenceSummary"],
                    "../../release-audit/m2-live-evidence-summary.json",
                )
                self.assertNotIn("savedReloaded", design["checks"])
                self.assertFalse(design["fixtureMetadata"]["liveEdaVerified"])
                self.assertEqual(status["status"], "verified")
                self.assertTrue(status["liveEvidenceIncluded"])
                self.assertEqual(
                    status["publicSummary"],
                    "../../../release-audit/m2-live-evidence-summary.json",
                )

    def test_m2_after_strict_rating_stays_pending_while_forecast_can_pass(self):
        after = json.loads((EVALS / "power-distribution-after" / "input.json").read_text(encoding="utf-8"))
        result = Review(after, self.profiles).run()
        ids = {finding["id"] for finding in result["findings"]}
        self.assertEqual(result["rating"], RATING_FIX_FIRST)
        self.assertEqual(result["engineeringForecastRating"], RATING_SUITABLE)
        self.assertIn("EVIDENCE_INCOMPLETE:PERSISTENCE", ids)
        self.assertIn("EVIDENCE_SCOPE:OFFLINE_FORECAST", ids)
        self.assertEqual(result["evidenceCompleteness"]["status"], "incomplete")

    def test_m2_before_remains_unsuitable_even_when_evidence_only_findings_are_excluded(self):
        before = json.loads((EVALS / "power-distribution-before" / "input.json").read_text(encoding="utf-8"))
        result = Review(before, self.profiles).run()
        self.assertEqual(result["rating"], RATING_UNSUITABLE)
        self.assertEqual(result["engineeringForecastRating"], RATING_UNSUITABLE)

    def test_adversarial_benchmark_is_fixture_scoped_nine_of_nine(self):
        case = EVALS / "car-controller-adversarial"
        expected = json.loads((case / "expected.json").read_text(encoding="utf-8"))
        benchmark = expected["benchmark"]
        self.assertEqual(benchmark["seededRiskFamilies"], 9)
        self.assertEqual(len(benchmark["requiredFamilyMatches"]), 9)
        self.assertEqual(benchmark["expectedMatchedFamilies"], 9)
        self.assertEqual(benchmark["scope"], "this sanitized fixture only")
        self.assertFalse(benchmark["generalAccuracyClaim"])

    def test_eval_files_have_no_workstation_paths_ids_or_username(self):
        posix_home = "/" + "home/"
        posix_users = "/" + "Users/"
        absolute_path = re.compile(
            r"(?i)(?:[A-Z]:[\\/]|\\\\[^\\]+\\|"
            + re.escape(posix_home)
            + "|"
            + re.escape(posix_users)
            + ")"
        )
        opaque_id = re.compile(r"(?i)(?<![A-Za-z0-9])[0-9a-f]{16,64}(?![A-Za-z0-9])")
        mojibake_markers = (
            chr(0xFFFD),
            "锟" + "斤拷",
            "б" + "к",
            "â" + "€",
            "ï" + "»¿",
        )
        for path in sorted(EVALS.rglob("*.json")):
            text = path.read_text(encoding="utf-8-sig")
            with self.subTest(path=path.relative_to(REPO).as_posix()):
                self.assertNotIn("289" + "53", text)
                self.assertIsNone(absolute_path.search(text))
                self.assertIsNone(opaque_id.search(text))
                for marker in mojibake_markers:
                    self.assertNotIn(marker, text)

    def test_absolute_source_and_screenshot_paths_are_not_emitted(self):
        design = copy.deepcopy(self.safe)
        windows_user_path = "C:" + r"\Users\example\private\capture.json"
        embedded_windows_path = "captured from " + "D:" + r"\private\embedded.json"
        screenshot_path = "K:" + r"\private\screen.png"
        posix_home_path = "/" + "home/example/private/board.json"
        posix_user_path = "/" + "Users/example/private/detail.png"
        design["sourceEvidence"] = [
            windows_user_path,
            posix_home_path,
            "relative/evidence.json",
            embedded_windows_path,
        ]
        design["screenshots"] = [
            screenshot_path,
            {"path": posix_user_path, "label": "detail"},
        ]
        result = Review(design, self.profiles).run()
        self.assertEqual(
            result["sourceEvidence"],
            ["capture.json", "board.json", "relative/evidence.json", "local-source"],
        )
        self.assertEqual(sanitize_public_value(design["screenshots"])[0], "screen.png")
        self.assertEqual(sanitize_public_value(design["screenshots"])[1]["path"], "detail.png")

        with ArchivedTemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            input_path = temp / "input.json"
            output = temp / "out"
            normalized = temp / "normalized.json"
            input_path.write_text(json.dumps(design, ensure_ascii=False), encoding="utf-8-sig")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ENGINE),
                    "--input",
                    str(input_path),
                    "--output",
                    str(output),
                    "--normalized-output",
                    str(normalized),
                ],
                cwd=temp,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            machine = json.loads((output / "machine-review.json").read_text(encoding="utf-8"))
            manifest = json.loads((output / "evidence-manifest.json").read_text(encoding="utf-8"))
            screenshot_index = json.loads((output / "screenshot-index.json").read_text(encoding="utf-8"))
            normalized_data = json.loads(normalized.read_text(encoding="utf-8"))
            self.assertEqual(machine["sourceEvidence"][:2], ["capture.json", "board.json"])
            self.assertEqual(manifest["sourceEvidence"][:2], ["capture.json", "board.json"])
            self.assertEqual(screenshot_index["screenshots"][0], "screen.png")
            self.assertEqual(normalized_data["sourceEvidence"][:2], ["capture.json", "board.json"])
            self.assertTrue(all(not Path(row["path"]).is_absolute() for row in manifest["files"]))

    def test_cli_runs_from_an_unrelated_working_directory_with_default_profiles(self):
        with ArchivedTemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            output = temp / "portable-output"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ENGINE),
                    "--input",
                    str(HERE / "fixtures" / "synthetic-safe-input.json"),
                    "--output",
                    str(output),
                ],
                cwd=temp,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout)
            self.assertEqual(summary["rating"], "suitable_for_low_risk_prototype")
            self.assertEqual(summary["output"], "portable-output")
            self.assertTrue((output / "machine-review.json").is_file())
            self.assertTrue((output / "evidence-manifest.json").is_file())

    def test_cli_rejects_duplicate_component_refs_without_traceback(self):
        design = copy.deepcopy(self.safe)
        design["components"].append(copy.deepcopy(design["components"][0]))
        with ArchivedTemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            input_path = temp / "invalid.json"
            input_path.write_text(json.dumps(design, ensure_ascii=False), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(ENGINE), "--input", str(input_path), "--output", str(temp / "out")],
                cwd=temp,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 2)
            error = json.loads(completed.stderr)
            self.assertEqual(error["error"], "InputValidationError")
            self.assertIn("duplicate", error["message"])
            self.assertNotIn("Traceback", completed.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
