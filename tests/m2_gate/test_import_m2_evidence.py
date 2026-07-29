import hashlib
import json
import shutil
import subprocess
import sys
from tests import ArchivedTemporaryDirectory
import time
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SCRIPT = REPO / "scripts" / "import_m2_evidence.py"
FIXTURE = HERE / "fixtures" / "complete"
MANIFEST_NAME = "SHA256-MANIFEST.json"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_manifest(input_dir: Path) -> Path:
    manifest_path = input_dir / MANIFEST_NAME
    files = []
    for path in sorted(input_dir.rglob("*.json")):
        if path == manifest_path:
            continue
        files.append(
            {
                "path": path.relative_to(input_dir).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    write_json(
        manifest_path,
        {
            "schema": "jlceda-m2-evidence-sha-manifest/1.0",
            "algorithm": "sha256",
            "files": files,
        },
    )
    return manifest_path


class M2EvidenceImportGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = ArchivedTemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.input_dir = self.root / "sanitized-input"
        self.output_dir = self.root / "public-output"
        shutil.copytree(FIXTURE, self.input_dir)

    def tearDown(self):
        self.temporary.cleanup()

    def run_gate(self, manifest: Path | None = None):
        manifest = manifest or write_manifest(self.input_dir)
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--input-dir",
                str(self.input_dir),
                "--sha-manifest",
                str(manifest),
                "--output-dir",
                str(self.output_dir),
            ],
            cwd=self.root,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.stderr, "")
        return completed, json.loads(completed.stdout)

    def test_success_copies_only_minimal_sanitized_summary(self):
        completed, result = self.run_gate()
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(result["gate"], "passed")
        self.assertTrue(result["changed"])
        self.assertEqual([path.name for path in self.output_dir.iterdir()], ["m2-live-evidence-summary.json"])

        summary = read_json(self.output_dir / "m2-live-evidence-summary.json")
        self.assertEqual(summary["gate"], "verified")
        self.assertTrue(summary["liveEdaVerified"])
        self.assertTrue(summary["liveSaveReloadVerified"])
        self.assertEqual(summary["before"]["prototypeReview"]["targetFindingStatus"], "present")
        self.assertEqual(summary["after"]["prototypeReview"]["targetFindingStatus"], "resolved")
        self.assertFalse(summary["transition"]["otherRiskSeverityWorsened"])
        serialized = json.dumps(summary)
        for forbidden in ("receipt.json", "SHA256-MANIFEST", "receiptId", "approvalId", "uuid"):
            self.assertNotIn(forbidden, serialized)

    def test_repeated_import_is_byte_and_timestamp_idempotent(self):
        manifest = write_manifest(self.input_dir)
        first, first_result = self.run_gate(manifest)
        self.assertEqual(first.returncode, 0)
        self.assertTrue(first_result["changed"])
        output = self.output_dir / "m2-live-evidence-summary.json"
        first_bytes = output.read_bytes()
        first_mtime = output.stat().st_mtime_ns
        time.sleep(0.02)

        second, second_result = self.run_gate(manifest)
        self.assertEqual(second.returncode, 0)
        self.assertFalse(second_result["changed"])
        self.assertEqual(output.read_bytes(), first_bytes)
        self.assertEqual(output.stat().st_mtime_ns, first_mtime)
        self.assertEqual(list(self.output_dir.glob("*")), [output])

    def test_explicit_pending_bundle_returns_nonzero_and_writes_nothing(self):
        bundle_path = self.input_dir / "bundle.json"
        bundle = read_json(bundle_path)
        bundle["status"] = "pending"
        write_json(bundle_path, bundle)
        completed, result = self.run_gate()
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(result["gate"], "pending")
        self.assertEqual(result["code"], "BUNDLE_PENDING")
        self.assertFalse(self.output_dir.exists())

    def test_missing_required_evidence_returns_pending(self):
        target = self.input_dir / "evidence" / "after" / "drc.json"
        target.rename(self.root / "withheld-drc.json")
        completed, result = self.run_gate()
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(result["gate"], "pending")
        self.assertEqual(result["code"], "MISSING_EVIDENCE")
        self.assertFalse(self.output_dir.exists())

    def test_hash_mismatch_is_rejected_before_import(self):
        manifest = write_manifest(self.input_dir)
        target = self.input_dir / "evidence" / "after" / "drc.json"
        target.write_text(target.read_text(encoding="utf-8") + " ", encoding="utf-8")
        completed, result = self.run_gate(manifest)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(result["gate"], "rejected")
        self.assertEqual(result["code"], "HASH_MISMATCH")
        self.assertFalse(self.output_dir.exists())

    def test_unmanifested_file_is_rejected(self):
        manifest = write_manifest(self.input_dir)
        write_json(self.input_dir / "unlisted.json", {"note": "not covered"})
        completed, result = self.run_gate(manifest)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(result["code"], "UNMANIFESTED_FILE")

    def test_unverified_save_reload_remains_pending(self):
        target = self.input_dir / "evidence" / "after" / "save-reload.json"
        document = read_json(target)
        document["postReloadReadbackSucceeded"] = False
        write_json(target, document)
        completed, result = self.run_gate()
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(result["gate"], "pending")
        self.assertEqual(result["code"], "EVIDENCE_NOT_VERIFIED")

    def test_after_with_remaining_blocker_stays_pending(self):
        target = self.input_dir / "evidence" / "after" / "prototype-review.json"
        document = read_json(target)
        document["blockerCount"] = 1
        document["rating"] = "suitable_after_corrections"
        write_json(target, document)
        completed, result = self.run_gate()
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(result["gate"], "pending")
        self.assertEqual(result["code"], "AFTER_NOT_LOW_RISK_READY")

    def test_output_must_not_overlap_input(self):
        manifest = write_manifest(self.input_dir)
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--input-dir",
                str(self.input_dir),
                "--sha-manifest",
                str(manifest),
                "--output-dir",
                str(self.input_dir / "public-output"),
            ],
            cwd=self.root,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        result = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(result["code"], "OUTPUT_OVERLAP")

    def test_output_directory_rejects_unrelated_files(self):
        self.output_dir.mkdir()
        (self.output_dir / "unrelated.txt").write_text("synthetic\n", encoding="utf-8")
        completed, result = self.run_gate()
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(result["gate"], "rejected")
        self.assertEqual(result["code"], "OUTPUT_NOT_EMPTY")

    def test_private_identifiers_paths_and_secrets_are_rejected(self):
        variants = (
            ("receiptId", "private-receipt-value", "PRIVATE_FIELD"),
            ("approvalId", "private-approval-value", "PRIVATE_FIELD"),
            ("sourcePath", "C:" + chr(92) + "private" + chr(92) + "evidence.json", "PRIVATE_PATH"),
            ("objectUuid", "123e4567" + "-e89b-42d3-a456-" + "426614174000", "PRIVATE_IDENTIFIER"),
            ("accessToken", "private-token-value", "PRIVATE_FIELD"),
        )
        source = FIXTURE / "evidence" / "after" / "receipt.json"
        for index, (key, value, expected_code) in enumerate(variants):
            with self.subTest(key=key):
                if self.input_dir.exists():
                    self.input_dir.rename(self.root / f"archived-input-{index}")
                if self.output_dir.exists():
                    self.output_dir.rename(self.root / f"archived-output-{index}")
                shutil.copytree(FIXTURE, self.input_dir)
                target = self.input_dir / "evidence" / "after" / "receipt.json"
                document = read_json(source)
                document[key] = value
                write_json(target, document)
                completed, result = self.run_gate()
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(result["gate"], "rejected")
                self.assertEqual(result["code"], expected_code)
                self.assertFalse(self.output_dir.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
