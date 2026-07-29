import importlib.util
import json
import subprocess
from tests import ArchivedTemporaryDirectory
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def load_script(name: str):
    path = REPO / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


integrity = load_script("update-integrity.py")
release_verify = load_script("release-verify.py")
release_build = load_script("build-release.py")


class ReleaseToolTests(unittest.TestCase):
    def test_archived_temporary_directory_renames_and_cleanup_is_idempotent(self):
        temporary = ArchivedTemporaryDirectory(prefix="archive-contract-")
        active = Path(temporary.name)
        marker = active / "marker.txt"
        marker.write_text("preserve\n", encoding="utf-8")
        archived = temporary.cleanup()
        self.assertIsNotNone(archived)
        self.assertFalse(active.exists())
        self.assertEqual((archived / "marker.txt").read_text(encoding="utf-8"), "preserve\n")
        self.assertEqual(temporary.cleanup(), archived)

    def test_integrity_update_is_idempotent(self):
        with ArchivedTemporaryDirectory() as temp_name:
            root = Path(temp_name)
            (root / "VERSION").write_text("0.1.0-alpha\n", encoding="utf-8")
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            first = integrity.update(root)
            manifest_first = (root / "FILE-MANIFEST.json").read_bytes()
            sums_first = (root / "SHA256SUMS.txt").read_bytes()
            second = integrity.update(root)
            self.assertTrue(first["manifestChanged"])
            self.assertTrue(first["sumsChanged"])
            self.assertFalse(second["manifestChanged"])
            self.assertFalse(second["sumsChanged"])
            self.assertEqual(manifest_first, (root / "FILE-MANIFEST.json").read_bytes())
            self.assertEqual(sums_first, (root / "SHA256SUMS.txt").read_bytes())

    def test_privacy_gate_rejects_constructed_private_values(self):
        with ArchivedTemporaryDirectory() as temp_name:
            root = Path(temp_name)
            private_path = "C:" + "\\" + "Users" + "\\" + "example" + "\\" + "secret.txt"
            private_uuid = "12345678" + "-1234-4abc-8def-" + "1234567890ab"
            path = root / "sample.md"
            path.write_text(private_path + "\n" + private_uuid, encoding="utf-8")
            errors = release_verify.privacy_errors(root, path, path.read_text(encoding="utf-8"))
            self.assertTrue(any("absolute workstation path" in error for error in errors))
            self.assertTrue(any("concrete UUID" in error for error in errors))

    def test_restricted_yaml_accepts_plugin_metadata_and_rejects_tabs(self):
        release_verify.parse_restricted_yaml("interface:\n  display_name: Example\n")
        with self.assertRaises(ValueError):
            release_verify.parse_restricted_yaml("interface:\n\tdisplay_name: Example\n")

    def test_public_and_provenance_inventories_cover_current_tree(self):
        errors = []
        files = list(release_verify.iter_files(REPO))
        release_verify.validate_release_inventories(REPO, files, errors)
        self.assertEqual(errors, [])

    def test_deterministic_zip_matches_committed_tree(self):
        with ArchivedTemporaryDirectory() as temp_name:
            root = Path(temp_name) / "sample-plugin"
            root.mkdir()
            subprocess.run(["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Fixture"], cwd=root, check=True)
            (root / "a.txt").write_text("alpha\n", encoding="utf-8")
            subprocess.run(["git", "add", "a.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "fixture"], cwd=root, check=True, capture_output=True)
            first = root.parent / "first.zip"
            second = root.parent / "second.zip"
            result_one = release_build.build(root, first)
            result_two = release_build.build(root, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(result_one["sha256"], result_two["sha256"])
            self.assertTrue(result_one["verifiedAgainstCommittedTree"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
