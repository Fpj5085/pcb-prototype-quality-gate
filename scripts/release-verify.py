#!/usr/bin/env python3
"""Run deterministic repository, privacy, integrity and archive checks."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
import urllib.parse
import zipfile
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[1]
TEXT_EXTENSIONS = {".json", ".md", ".py", ".ps1", ".txt", ".yaml", ".yml"}
TEXT_NAMES = {".gitignore", ".gitattributes", "LICENSE", "NOTICE", "VERSION"}
FORBIDDEN_EXTENSIONS = {
    ".eext", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".log", ".exe", ".dll", ".zip",
    ".7z", ".rar", ".tar", ".tgz", ".gz", ".sha256", ".docx", ".pptx", ".xlsx", ".bin", ".dat",
    ".pyc", ".pyo", ".pyd",
}
INTEGRITY_FILES = {"FILE-MANIFEST.json", "SHA256SUMS.txt"}
MAX_FILE_BYTES = 1024 * 1024
ABSOLUTE_PATH = re.compile(
    r"(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/][^\s\"'<>]+|\\\\[A-Za-z0-9][A-Za-z0-9._-]*[\\/][^\s\"'<>]+|/(?:Users|home|private|tmp|var)/[^\s\"'<>]*|~[\\/][^\s\"'<>]+)"
)
UUID_VALUE = re.compile(r"(?i)(?<![0-9a-f])[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}(?![0-9a-f])")
LONG_HEX = re.compile(r"(?i)(?<![0-9a-f])[0-9a-f]{16,64}(?![0-9a-f])")
SECRET_ASSIGNMENT = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|passwd|authorization|cookie)"
    r"\s*[:=]\s*[\"']?(?!<|\{|\[|none|null|false|true|redacted|placeholder)[A-Za-z0-9_./+=:-]{8,}"
)
PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
MOJIBAKE_MARKERS = (
    chr(0x951F) + chr(0x65A4) + chr(0x62F7),
    chr(0x00E2) + chr(0x20AC),
    chr(0x00EF) + chr(0x00BB) + chr(0x00BF),
)


def iter_files(root: Path) -> Iterable[Path]:
    paths = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if ".git" in relative.parts:
            continue
        paths.append(path)
    yield from sorted(paths, key=lambda item: item.relative_to(root).as_posix())


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def is_text(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name in TEXT_NAMES


def parse_restricted_yaml(text: str) -> None:
    """Validate the conservative mapping-only YAML subset used by this package."""

    stack: list[set[str]] = [set()]
    previous_indent = 0
    for line_number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if "\t" in raw:
            raise ValueError(f"line {line_number}: tab indentation")
        indent = len(raw) - len(raw.lstrip(" "))
        if indent % 2:
            raise ValueError(f"line {line_number}: indentation must be multiples of two")
        if indent > previous_indent + 2:
            raise ValueError(f"line {line_number}: indentation jumped more than one level")
        level = indent // 2
        while len(stack) <= level:
            stack.append(set())
        stack = stack[: level + 1]
        content = raw.strip()
        if ":" not in content or content.startswith("-"):
            raise ValueError(f"line {line_number}: expected mapping entry")
        key, _value = content.split(":", 1)
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", key):
            raise ValueError(f"line {line_number}: unsupported key syntax")
        if key in stack[level]:
            raise ValueError(f"line {line_number}: duplicate key {key}")
        stack[level].add(key)
        previous_indent = indent


def markdown_link_errors(root: Path, path: Path, text: str) -> list[str]:
    errors = []
    for match in MARKDOWN_LINK.finditer(text):
        target = match.group(1).strip().split(maxsplit=1)[0].strip("<>")
        if not target or target.startswith(("#", "http://", "https://", "mailto:", "codex://")):
            continue
        decoded = urllib.parse.unquote(target.split("#", 1)[0])
        destination = (path.parent / decoded).resolve()
        try:
            destination.relative_to(root)
        except ValueError:
            errors.append(f"{rel(root, path)} -> outside repository: {target}")
            continue
        if not destination.exists():
            errors.append(f"{rel(root, path)} -> missing: {target}")
    return errors


def privacy_errors(root: Path, path: Path, text: str) -> list[str]:
    relative = rel(root, path)
    errors = []
    private_username = "289" + "53"
    if private_username in text:
        errors.append(f"{relative}: private username")
    if ABSOLUTE_PATH.search(text):
        errors.append(f"{relative}: absolute workstation path")
    if UUID_VALUE.search(text):
        errors.append(f"{relative}: concrete UUID")
    if PRIVATE_KEY.search(text) or SECRET_ASSIGNMENT.search(text):
        errors.append(f"{relative}: credential-like assignment")
    for match in LONG_HEX.finditer(text):
        line_start = text.rfind("\n", 0, match.start()) + 1
        line_end = text.find("\n", match.end())
        if line_end < 0:
            line_end = len(text)
        context = text[line_start:line_end].lower()
        explicitly_integrity = relative in INTEGRITY_FILES or any(
            term in context for term in ("sha-256", "sha256", "digest", "checksum", "commit")
        )
        if not explicitly_integrity:
            errors.append(f"{relative}: unexplained long hexadecimal value")
            break
    return errors


def validate_plugin(root: Path, errors: list[str]) -> None:
    path = root / ".codex-plugin" / "plugin.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"plugin manifest: {exc}")
        return
    name = data.get("name")
    version = data.get("version")
    permitted_roots = {name, f"{name}-v{version}"} if isinstance(name, str) and isinstance(version, str) else set()
    if root.name not in permitted_roots:
        errors.append("plugin manifest name/version must match repository directory")
    for field in ("version", "description", "license", "skills"):
        if not data.get(field):
            errors.append(f"plugin manifest missing {field}")
    if data.get("skills") != "./skills/":
        errors.append("plugin manifest skills path must be ./skills/")


def validate_skill(root: Path, errors: list[str]) -> None:
    for path in sorted((root / "skills").glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            errors.append(f"{rel(root, path)}: invalid frontmatter")
            continue
        frontmatter = text.split("---\n", 2)[1]
        fields = {}
        for line in frontmatter.splitlines():
            if ":" not in line:
                errors.append(f"{rel(root, path)}: unsupported frontmatter line")
                continue
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
        if set(fields) != {"name", "description"}:
            errors.append(f"{rel(root, path)}: frontmatter fields must be name and description")
        if fields.get("name") != path.parent.name or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fields.get("name", "")):
            errors.append(f"{rel(root, path)}: invalid skill name")
        if not fields.get("description", "").startswith("Use when"):
            errors.append(f"{rel(root, path)}: description must start with Use when")


def validate_release_inventories(root: Path, files: list[Path], errors: list[str]) -> None:
    expected = {rel(root, path) for path in files}
    public_path = root / "PUBLIC-FILES.md"
    provenance_path = root / "release-audit" / "FILE-PROVENANCE.md"
    try:
        public_text = public_path.read_text(encoding="utf-8")
        public_files = set(re.findall(r"^- `([^`]+)`", public_text, re.MULTILINE))
        declared_match = re.search(r"Total intended repository files:\s*(\d+)", public_text)
        declared = int(declared_match.group(1)) if declared_match else -1
        if public_files != expected or declared != len(expected):
            errors.append("PUBLIC-FILES.md inventory or declared count differs from repository")
    except OSError as exc:
        errors.append(f"PUBLIC-FILES.md: {exc}")
    try:
        provenance_text = provenance_path.read_text(encoding="utf-8")
        provenance_files = set(re.findall(r"^\| `([^`]+)` \|", provenance_text, re.MULTILINE))
        if provenance_files != expected:
            errors.append("release-audit/FILE-PROVENANCE.md inventory differs from repository")
    except OSError as exc:
        errors.append(f"release-audit/FILE-PROVENANCE.md: {exc}")


def validate_integrity(root: Path, files: list[Path], errors: list[str]) -> dict[str, int]:
    manifest_path = root / "FILE-MANIFEST.json"
    sums_path = root / "SHA256SUMS.txt"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"FILE-MANIFEST.json: {exc}")
        return {"manifestEntries": 0, "sumEntries": 0}
    expected = {
        rel(root, path): path
        for path in files
        if path.name not in INTEGRITY_FILES
    }
    rows = {row.get("path"): row for row in manifest.get("files", []) if isinstance(row, dict)}
    if set(rows) != set(expected):
        errors.append("FILE-MANIFEST.json inventory differs from repository")
    for relative, path in expected.items():
        row = rows.get(relative)
        if not row:
            continue
        payload = path.read_bytes()
        if row.get("bytes") != len(payload) or row.get("sha256") != sha256_bytes(payload):
            errors.append(f"FILE-MANIFEST.json mismatch: {relative}")
    if manifest.get("fileCount") != len(expected):
        errors.append("FILE-MANIFEST.json fileCount mismatch")

    sums: dict[str, str] = {}
    try:
        for line in sums_path.read_text(encoding="utf-8").splitlines():
            digest, relative = line.split("  ", 1)
            sums[relative] = digest
    except (OSError, ValueError) as exc:
        errors.append(f"SHA256SUMS.txt: {exc}")
        return {"manifestEntries": len(rows), "sumEntries": len(sums)}
    expected_sums = {rel(root, path): sha256_bytes(path.read_bytes()) for path in files if path.name != "SHA256SUMS.txt"}
    if sums != expected_sums:
        errors.append("SHA256SUMS.txt differs from repository")
    return {"manifestEntries": len(rows), "sumEntries": len(sums)}


def validate_archive(root: Path, archive_path: Path, errors: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {"archive": archive_path.name, "archiveFiles": 0}
    try:
        with zipfile.ZipFile(archive_path) as archive:
            members = [item for item in archive.infolist() if not item.is_dir()]
            result["archiveFiles"] = len(members)
            prefix = root.name + "/"
            normalized: dict[str, bytes] = {}
            for item in members:
                if not item.filename.startswith(prefix) or ".." in Path(item.filename).parts:
                    errors.append(f"archive unsafe or unexpected member: {item.filename}")
                    continue
                normalized[item.filename[len(prefix):]] = archive.read(item)
            try:
                git_files = subprocess.check_output(
                    ["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=root, text=True, encoding="utf-8"
                ).splitlines()
                if set(normalized) != set(git_files):
                    errors.append("archive inventory differs from committed tree")
                for relative in set(normalized) & set(git_files):
                    expected = subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=root)
                    if normalized[relative] != expected:
                        errors.append(f"archive content differs from HEAD: {relative}")
            except (OSError, subprocess.SubprocessError) as exc:
                errors.append(f"archive Git verification failed: {exc}")
    except (OSError, zipfile.BadZipFile) as exc:
        errors.append(f"archive: {exc}")
    if archive_path.is_file():
        result["sha256"] = sha256_bytes(archive_path.read_bytes())
        sidecar = archive_path.with_suffix(archive_path.suffix + ".sha256")
        if sidecar.is_file():
            expected = sidecar.read_text(encoding="ascii").split()[0].lower()
            if expected != result["sha256"]:
                errors.append("archive SHA-256 sidecar mismatch")
        else:
            errors.append("archive SHA-256 sidecar missing")
    return result


def verify(root: Path, archive: Path | None = None, *, skip_integrity: bool = False) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    counts = {"files": 0, "text": 0, "json": 0, "yaml": 0, "python": 0, "markdownLinks": 0}
    files = list(iter_files(root))
    counts["files"] = len(files)
    for path in files:
        relative = rel(root, path)
        if path.is_symlink():
            errors.append(f"{relative}: symbolic links are excluded")
            continue
        if path.suffix.lower() in FORBIDDEN_EXTENSIONS or path.name.startswith(".tmp-") or "__pycache__" in path.parts:
            errors.append(f"{relative}: forbidden release file")
        if path.stat().st_size > MAX_FILE_BYTES:
            errors.append(f"{relative}: exceeds 1 MiB")
        if not is_text(path):
            continue
        counts["text"] += 1
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"{relative}: invalid UTF-8: {exc}")
            continue
        if chr(0xFFFD) in text:
            errors.append(f"{relative}: replacement character")
        for marker in MOJIBAKE_MARKERS:
            if marker in text:
                errors.append(f"{relative}: mojibake marker")
                break
        errors.extend(privacy_errors(root, path, text))
        if path.suffix.lower() == ".json":
            counts["json"] += 1
            try:
                json.loads(text)
            except json.JSONDecodeError as exc:
                errors.append(f"{relative}: invalid JSON: {exc}")
        elif path.suffix.lower() in {".yaml", ".yml"}:
            counts["yaml"] += 1
            try:
                parse_restricted_yaml(text)
            except ValueError as exc:
                errors.append(f"{relative}: invalid restricted YAML: {exc}")
        elif path.suffix.lower() == ".py":
            counts["python"] += 1
            try:
                ast.parse(text, filename=relative)
            except SyntaxError as exc:
                errors.append(f"{relative}: invalid Python: {exc}")
        elif path.suffix.lower() == ".md":
            links = MARKDOWN_LINK.findall(text)
            counts["markdownLinks"] += len(links)
            errors.extend(markdown_link_errors(root, path, text))
    validate_plugin(root, errors)
    validate_skill(root, errors)
    validate_release_inventories(root, files, errors)
    integrity = {"manifestEntries": 0, "sumEntries": 0}
    if not skip_integrity:
        integrity = validate_integrity(root, files, errors)
    archive_result: dict[str, Any] = {}
    if archive is not None:
        archive_result = validate_archive(root, archive.resolve(), errors)
    return {
        "schema": "codex-jlceda-release-verification/1.0",
        "status": "pass" if not errors else "fail",
        "root": root.name,
        "counts": counts,
        "integrity": integrity,
        "archive": archive_result,
        "highRiskFindings": len(errors),
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=REPO)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--skip-integrity", action="store_true")
    args = parser.parse_args(argv)
    result = verify(args.repository, args.archive, skip_integrity=args.skip_integrity)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
