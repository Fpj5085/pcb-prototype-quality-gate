#!/usr/bin/env python3
"""Regenerate repository integrity files deterministically.

The manifest intentionally carries no wall-clock timestamp. Running this script
twice over the same tree produces byte-identical outputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable


REPO = Path(__file__).resolve().parents[1]
MANIFEST_NAME = "FILE-MANIFEST.json"
SUMS_NAME = "SHA256SUMS.txt"
EXCLUDED_PARTS = {".git", "__pycache__"}
EXCLUDED_NAMES = {MANIFEST_NAME, SUMS_NAME}


def iter_release_files(root: Path, *, include_manifest: bool = False) -> Iterable[Path]:
    """Yield release files in stable repository-relative order."""

    paths: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"symbolic links are excluded: {relative.as_posix()}")
        if path.name in EXCLUDED_NAMES and not (include_manifest and path.name == MANIFEST_NAME):
            continue
        paths.append(path)
    yield from sorted(paths, key=lambda item: item.relative_to(root).as_posix())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(data: object) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def build_manifest(root: Path) -> dict[str, object]:
    files = []
    for path in iter_release_files(root):
        relative = path.relative_to(root).as_posix()
        files.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)})
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    return {
        "schema": "codex-jlceda-release-file-manifest/1.1",
        "version": version,
        "candidateStatus": "local-review-candidate-not-published",
        "algorithm": "SHA-256",
        "reproducible": True,
        "fileCount": len(files),
        "repositoryFileCountIncludingIntegrityFiles": len(files) + 2,
        "selfHashExclusions": [MANIFEST_NAME, SUMS_NAME],
        "files": files,
    }


def write_if_changed(path: Path, payload: bytes) -> bool:
    if path.is_file() and path.read_bytes() == payload:
        return False
    path.write_bytes(payload)
    return True


def update(root: Path) -> dict[str, object]:
    root = root.resolve()
    manifest_path = root / MANIFEST_NAME
    sums_path = root / SUMS_NAME
    manifest_changed = write_if_changed(manifest_path, canonical_json(build_manifest(root)))

    sum_lines = []
    for path in iter_release_files(root, include_manifest=True):
        relative = path.relative_to(root).as_posix()
        sum_lines.append(f"{sha256(path)}  {relative}")
    sums_payload = ("\n".join(sum_lines) + "\n").encode("utf-8")
    sums_changed = write_if_changed(sums_path, sums_payload)
    return {
        "schema": "codex-jlceda-integrity-update/1.0",
        "root": root.name,
        "manifestChanged": manifest_changed,
        "sumsChanged": sums_changed,
        "manifestEntries": len(json.loads(manifest_path.read_text(encoding="utf-8"))["files"]),
        "sumEntries": len(sum_lines),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=REPO)
    args = parser.parse_args(argv)
    try:
        result = update(args.repository)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"status": "pass", **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
