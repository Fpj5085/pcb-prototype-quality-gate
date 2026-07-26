#!/usr/bin/env python3
"""Build and verify a deterministic local ZIP from the committed Git tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


class ReleaseBuildError(RuntimeError):
    pass


def git(root: Path, *args: str, text: bool = True) -> str | bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=text,
        encoding="utf-8" if text else None,
    )
    if completed.returncode:
        stderr = completed.stderr if text else completed.stderr.decode("utf-8", errors="replace")
        raise ReleaseBuildError(stderr.strip() or f"git {' '.join(args)} failed")
    return completed.stdout


def committed_files(root: Path) -> list[str]:
    output = str(git(root, "ls-tree", "-r", "--name-only", "HEAD"))
    return sorted(line for line in output.splitlines() if line)


def committed_blob(root: Path, relative: str) -> bytes:
    return bytes(git(root, "show", f"HEAD:{relative}", text=False))


def verify_clean(root: Path) -> None:
    status = str(git(root, "status", "--porcelain", "--untracked-files=all"))
    if status.strip():
        raise ReleaseBuildError("working tree is not clean")


def zip_member_name(prefix: str, relative: str) -> str:
    return f"{prefix}/{relative}"


def build(root: Path, output: Path, *, require_clean: bool = True) -> dict[str, object]:
    root = root.resolve()
    output = output.resolve()
    if require_clean:
        verify_clean(root)
    files = committed_files(root)
    prefix = root.name
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_STORED, strict_timestamps=True) as archive:
        for relative in files:
            info = zipfile.ZipInfo(zip_member_name(prefix, relative), FIXED_ZIP_TIME)
            info.create_system = 3
            info.external_attr = (0o100644 & 0xFFFF) << 16
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, committed_blob(root, relative))
    temporary.replace(output)

    with zipfile.ZipFile(output) as archive:
        actual = sorted(item.filename for item in archive.infolist() if not item.is_dir())
        expected = [zip_member_name(prefix, relative) for relative in files]
        if actual != expected:
            raise ReleaseBuildError("archive file inventory differs from committed tree")
        for relative in files:
            if archive.read(zip_member_name(prefix, relative)) != committed_blob(root, relative):
                raise ReleaseBuildError(f"archive content differs from HEAD: {relative}")

    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    sidecar = output.with_suffix(output.suffix + ".sha256")
    sidecar.write_text(f"{digest}  {output.name}\n", encoding="ascii", newline="\n")
    return {
        "schema": "codex-jlceda-local-release-build/1.0",
        "commit": str(git(root, "rev-parse", "HEAD")).strip(),
        "archive": output.name,
        "sha256": digest,
        "files": len(files),
        "topLevelDirectory": prefix,
        "compression": "stored",
        "fixedTimestamp": "1980-01-01T00:00:00Z",
        "verifiedAgainstCommittedTree": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=REPO)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-dirty", action="store_true", help="development only")
    args = parser.parse_args(argv)
    root = args.repository.resolve()
    output = args.output or root.parent / f"{root.name}.zip"
    try:
        result = build(root, output, require_clean=not args.allow_dirty)
    except (OSError, subprocess.SubprocessError, zipfile.BadZipFile, ReleaseBuildError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"status": "pass", **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
