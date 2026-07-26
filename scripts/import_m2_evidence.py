#!/usr/bin/env python3
"""Import a minimal, sanitized M2 live-evidence summary.

The gate is intentionally offline and narrow.  It accepts an explicitly named
input directory plus an explicitly named SHA-256 manifest, verifies every input
byte, validates the required BEFORE/AFTER evidence classes, rejects private
identifiers, and writes one deterministic public summary.  It never copies raw
receipts or source evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, NoReturn


MANIFEST_SCHEMA = "jlceda-m2-evidence-sha-manifest/1.0"
BUNDLE_SCHEMA = "jlceda-m2-live-evidence-bundle/1.0"
SUMMARY_SCHEMA = "jlceda-m2-public-evidence-summary/1.0"
OUTPUT_NAME = "m2-live-evidence-summary.json"

EVIDENCE_SPECS: dict[str, tuple[str, frozenset[str]]] = {
    "receipt": (
        "jlceda-m2-delivery-receipt-evidence/1.0",
        frozenset(
            {
                "schema",
                "stage",
                "source",
                "live",
                "verified",
                "idState",
                "operation",
                "operationStatus",
                "mutationCount",
            }
        ),
    ),
    "saveReload": (
        "jlceda-m2-save-reload-evidence/1.0",
        frozenset(
            {
                "schema",
                "stage",
                "live",
                "saveSucceeded",
                "closeSucceeded",
                "reloadSucceeded",
                "postReloadReadbackSucceeded",
            }
        ),
    ),
    "independentReadback": (
        "jlceda-m2-independent-readback-evidence/1.0",
        frozenset(
            {
                "schema",
                "stage",
                "live",
                "independentVerifier",
                "readbackSucceeded",
                "componentCount",
                "networkCount",
            }
        ),
    ),
    "drc": (
        "jlceda-m2-drc-evidence/1.0",
        frozenset(
            {
                "schema",
                "stage",
                "live",
                "completed",
                "errorCount",
                "boardContainmentPassed",
                "connectivityPassed",
            }
        ),
    ),
    "prototypeReview": (
        "jlceda-m2-prototype-review-evidence/1.0",
        frozenset(
            {
                "schema",
                "stage",
                "live",
                "completed",
                "rating",
                "blockerCount",
                "targetFindingStatus",
                "otherRiskSeverityWorsened",
            }
        ),
    ),
}

RATINGS = {
    "not_suitable_for_prototype",
    "suitable_after_corrections",
    "suitable_for_low_risk_prototype",
}

WINDOWS_ABSOLUTE = re.compile(r"(?i)(?:[a-z]:[\\/]|\\\\[^\\/]+[\\/])")
POSIX_PRIVATE_ABSOLUTE = re.compile(r"/(?:home|Users|private|var|tmp)/", re.IGNORECASE)
UUID = re.compile(
    r"(?i)(?<![0-9a-f])[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}(?![0-9a-f])"
)
OPAQUE_ID = re.compile(r"(?i)(?<![0-9a-f])[0-9a-f]{16,64}(?![0-9a-f])")
SECRET_VALUE = re.compile(
    r"(?i)(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|bearer\s+[a-z0-9._~+/=-]+|gh[pousr]_[a-z0-9]{20,})"
)
FORBIDDEN_KEYS = {
    "accesstoken",
    "apikey",
    "approvalid",
    "authorization",
    "checkpointid",
    "cookie",
    "deviceid",
    "deviceuuid",
    "libraryid",
    "libraryuuid",
    "nonce",
    "objectid",
    "pageid",
    "password",
    "pcbid",
    "privatekey",
    "projectid",
    "receiptid",
    "refreshtoken",
    "secret",
    "token",
    "username",
    "uuid",
}


class GateError(Exception):
    """Expected gate outcome with stable machine-readable classification."""

    def __init__(self, gate: str, code: str, message: str, exit_code: int):
        super().__init__(message)
        self.gate = gate
        self.code = code
        self.message = message
        self.exit_code = exit_code


def reject(code: str, message: str) -> NoReturn:
    raise GateError("rejected", code, message, 2)


def pending(code: str, message: str) -> NoReturn:
    raise GateError("pending", code, message, 3)


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        pending("MISSING_EVIDENCE", f"{label}: required file is missing")
    except (UnicodeDecodeError, json.JSONDecodeError):
        reject("INVALID_JSON", f"{label}: expected valid UTF-8 JSON")
    except OSError:
        reject("IO_ERROR", f"{label}: file could not be read")


def require_exact_keys(value: Any, expected: frozenset[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        reject("INVALID_EVIDENCE", f"{label}: expected an object")
    actual = set(value)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        pending("MISSING_EVIDENCE_FIELD", f"{label}: missing {', '.join(missing)}")
    if extra:
        reject("UNEXPECTED_EVIDENCE_FIELD", f"{label}: unexpected {', '.join(extra)}")
    return value


def contained_relative_path(root: Path, value: Any, label: str) -> tuple[Path, str]:
    if not isinstance(value, str) or not value or "\\" in value:
        reject("INVALID_RELATIVE_PATH", f"{label}: expected a non-empty POSIX relative path")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or "." in relative.parts:
        reject("INVALID_RELATIVE_PATH", f"{label}: path must stay inside the input directory")
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        reject("INVALID_RELATIVE_PATH", f"{label}: path must stay inside the input directory")
    return resolved, relative.as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        reject("IO_ERROR", "manifest member could not be read")
    return digest.hexdigest()


def verify_manifest(input_root: Path, manifest_path: Path) -> set[str]:
    manifest = read_json(manifest_path, "SHA manifest")
    expected_keys = frozenset({"schema", "algorithm", "files"})
    manifest = require_exact_keys(manifest, expected_keys, "SHA manifest")
    if manifest["schema"] != MANIFEST_SCHEMA or manifest["algorithm"] != "sha256":
        reject("INVALID_MANIFEST", "SHA manifest schema or algorithm is unsupported")
    if not isinstance(manifest["files"], list) or not manifest["files"]:
        reject("INVALID_MANIFEST", "SHA manifest files must be a non-empty array")

    listed: set[str] = set()
    for index, row in enumerate(manifest["files"]):
        label = f"SHA manifest files[{index}]"
        row = require_exact_keys(row, frozenset({"path", "sha256"}), label)
        path, relative = contained_relative_path(input_root, row["path"], f"{label}.path")
        expected_hash = row["sha256"]
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            reject("INVALID_MANIFEST", f"{label}.sha256: expected lowercase SHA-256")
        if relative in listed:
            reject("INVALID_MANIFEST", f"{label}.path: duplicate manifest member")
        listed.add(relative)
        if not path.exists() or not path.is_file() or path.is_symlink():
            pending("MISSING_EVIDENCE", f"{relative}: required manifest member is missing")
        if sha256_file(path) != expected_hash:
            reject("HASH_MISMATCH", f"{relative}: SHA-256 mismatch")

    actual: set[str] = set()
    try:
        for path in input_root.rglob("*"):
            if path.is_symlink():
                reject("SYMLINK_REJECTED", "input directory must not contain symbolic links")
            if not path.is_file():
                continue
            if path.resolve() == manifest_path.resolve():
                continue
            relative = path.relative_to(input_root).as_posix()
            actual.add(relative)
            if path.suffix.lower() != ".json":
                reject("UNSUPPORTED_INPUT_FILE", f"{relative}: only JSON evidence is accepted")
    except OSError:
        reject("IO_ERROR", "input directory could not be enumerated")
    unlisted = sorted(actual - listed)
    if unlisted:
        reject("UNMANIFESTED_FILE", f"SHA manifest does not cover: {', '.join(unlisted)}")
    # Listed-but-missing members were classified above; this catches a manifest
    # outside the input tree and keeps exact coverage deterministic.
    if listed != actual:
        pending("MISSING_EVIDENCE", "one or more manifest members are missing from the input directory")
    return listed


def scan_private(value: Any, label: str = "input") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())
            if normalized in FORBIDDEN_KEYS or normalized.endswith("approvalid") or normalized.endswith("receiptid"):
                reject("PRIVATE_FIELD", f"{label}: private identifier or secret field is forbidden")
            scan_private(child, f"{label}.{key}")
        return
    if isinstance(value, list):
        for child in value:
            scan_private(child, label)
        return
    if not isinstance(value, str):
        return
    if WINDOWS_ABSOLUTE.search(value) or POSIX_PRIVATE_ABSOLUTE.search(value) or value.startswith(("/", "~")):
        reject("PRIVATE_PATH", f"{label}: absolute or workstation path is forbidden")
    if UUID.search(value) or OPAQUE_ID.search(value):
        reject("PRIVATE_IDENTIFIER", f"{label}: concrete UUID or opaque identifier is forbidden")
    if SECRET_VALUE.search(value):
        reject("SECRET_VALUE", f"{label}: secret-like value is forbidden")


def require_bool(document: dict[str, Any], field: str, label: str, expected: bool = True) -> None:
    if document[field] is not expected:
        pending("EVIDENCE_NOT_VERIFIED", f"{label}.{field}: expected {str(expected).lower()}")


def require_nonnegative_int(document: dict[str, Any], field: str, label: str) -> int:
    value = document[field]
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        reject("INVALID_EVIDENCE", f"{label}.{field}: expected a non-negative integer")
    return value


def validate_evidence(kind: str, stage: str, document: Any, label: str) -> dict[str, Any]:
    schema, keys = EVIDENCE_SPECS[kind]
    scan_private(document, label)
    document = require_exact_keys(document, keys, label)
    if document["schema"] != schema or document["stage"] != stage:
        reject("INVALID_EVIDENCE", f"{label}: schema or stage mismatch")
    require_bool(document, "live", label)

    if kind == "receipt":
        require_bool(document, "verified", label)
        if document["source"] != "live-eda" or document["idState"] != "redacted":
            reject("PRIVATE_OR_NONLIVE_RECEIPT", f"{label}: receipt must be live and its identifier redacted")
        if document["operationStatus"] != "success":
            pending("RECEIPT_NOT_SUCCESSFUL", f"{label}: receipt does not record success")
        mutation_count = require_nonnegative_int(document, "mutationCount", label)
        expected_operation = "baseline-capture" if stage == "before" else "repair-delivery"
        if document["operation"] != expected_operation:
            reject("INVALID_EVIDENCE", f"{label}.operation: expected {expected_operation}")
        if stage == "before" and mutation_count != 0:
            reject("INVALID_EVIDENCE", f"{label}.mutationCount: baseline must be zero")
        if stage == "after" and mutation_count < 1:
            pending("NO_LIVE_MUTATION", f"{label}.mutationCount: repaired state requires a live mutation")
    elif kind == "saveReload":
        for field in ("saveSucceeded", "closeSucceeded", "reloadSucceeded", "postReloadReadbackSucceeded"):
            require_bool(document, field, label)
    elif kind == "independentReadback":
        require_bool(document, "independentVerifier", label)
        require_bool(document, "readbackSucceeded", label)
        require_nonnegative_int(document, "componentCount", label)
        require_nonnegative_int(document, "networkCount", label)
    elif kind == "drc":
        require_bool(document, "completed", label)
        require_bool(document, "boardContainmentPassed", label)
        require_bool(document, "connectivityPassed", label)
        if require_nonnegative_int(document, "errorCount", label) != 0:
            pending("DRC_NOT_CLEAN", f"{label}.errorCount: expected zero")
    elif kind == "prototypeReview":
        require_bool(document, "completed", label)
        require_bool(document, "otherRiskSeverityWorsened", label, expected=False)
        if document["rating"] not in RATINGS:
            reject("INVALID_EVIDENCE", f"{label}.rating: unsupported rating")
        blocker_count = require_nonnegative_int(document, "blockerCount", label)
        expected_status = "present" if stage == "before" else "resolved"
        if document["targetFindingStatus"] != expected_status:
            pending("TARGET_FINDING_NOT_CLOSED", f"{label}.targetFindingStatus: expected {expected_status}")
        if stage == "before" and blocker_count < 1:
            pending("BASELINE_FINDING_NOT_BLOCKING", f"{label}.blockerCount: expected at least one baseline blocker")
        if stage == "after" and (blocker_count != 0 or document["rating"] != "suitable_for_low_risk_prototype"):
            pending(
                "AFTER_NOT_LOW_RISK_READY",
                f"{label}: repaired state must have zero blockers and a low-risk Prototype rating",
            )
    return document


def load_bundle(input_root: Path, listed: set[str]) -> dict[str, Any]:
    if "bundle.json" not in listed:
        pending("MISSING_EVIDENCE", "bundle.json is required")
    bundle = read_json(input_root / "bundle.json", "bundle.json")
    expected_keys = frozenset({"schema", "status", "case", "before", "after"})
    scan_private(bundle, "bundle.json")
    bundle = require_exact_keys(bundle, expected_keys, "bundle.json")
    if bundle["schema"] != BUNDLE_SCHEMA:
        reject("INVALID_BUNDLE", "bundle.json: unsupported schema")
    if bundle["status"] == "pending":
        pending("BUNDLE_PENDING", "bundle.json: live evidence remains pending")
    if bundle["status"] != "complete":
        reject("INVALID_BUNDLE", "bundle.json.status must be pending or complete")
    if not isinstance(bundle["case"], str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", bundle["case"]):
        reject("INVALID_BUNDLE", "bundle.json.case must be a public lowercase slug")
    reference_keys = frozenset(EVIDENCE_SPECS)
    for stage in ("before", "after"):
        references = require_exact_keys(bundle[stage], reference_keys, f"bundle.json.{stage}")
        for kind, value in references.items():
            _, relative = contained_relative_path(input_root, value, f"bundle.json.{stage}.{kind}")
            if relative not in listed:
                pending("MISSING_EVIDENCE", f"{relative}: referenced evidence is not in the SHA manifest")
    return bundle


def load_and_validate_documents(
    input_root: Path, bundle: dict[str, Any]
) -> dict[str, dict[str, dict[str, Any]]]:
    documents: dict[str, dict[str, dict[str, Any]]] = {"before": {}, "after": {}}
    for stage in ("before", "after"):
        for kind, reference in bundle[stage].items():
            path, relative = contained_relative_path(input_root, reference, f"bundle.json.{stage}.{kind}")
            document = read_json(path, relative)
            documents[stage][kind] = validate_evidence(kind, stage, document, relative)
    return documents


def public_stage_summary(documents: dict[str, dict[str, Any]]) -> dict[str, Any]:
    readback = documents["independentReadback"]
    drc = documents["drc"]
    review = documents["prototypeReview"]
    return {
        "receiptVerified": True,
        "saveReloadVerified": True,
        "independentReadbackVerified": True,
        "designMetrics": {
            "componentCount": readback["componentCount"],
            "networkCount": readback["networkCount"],
        },
        "drc": {
            "completed": True,
            "errorCount": drc["errorCount"],
            "boardContainmentPassed": True,
            "connectivityPassed": True,
        },
        "prototypeReview": {
            "completed": True,
            "rating": review["rating"],
            "blockerCount": review["blockerCount"],
            "targetFindingStatus": review["targetFindingStatus"],
        },
    }


def build_summary(bundle: dict[str, Any], documents: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    return {
        "schema": SUMMARY_SCHEMA,
        "case": bundle["case"],
        "gate": "verified",
        "liveEdaVerified": True,
        "liveSaveReloadVerified": True,
        "before": public_stage_summary(documents["before"]),
        "after": public_stage_summary(documents["after"]),
        "transition": {
            "targetFindingResolved": True,
            "otherRiskSeverityWorsened": False,
        },
        "privacy": {
            "rawEvidenceCopied": False,
            "workstationPathsIncluded": False,
            "privateIdentifiersIncluded": False,
        },
    }


def write_idempotent(output_dir: Path, summary: dict[str, Any]) -> bool:
    payload = canonical_bytes(summary)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / OUTPUT_NAME
        existing = list(output_dir.iterdir())
        if any(path.name != OUTPUT_NAME or not path.is_file() for path in existing):
            reject("OUTPUT_NOT_EMPTY", "output directory may contain only the deterministic public summary")
        if output_path.is_symlink():
            reject("SYMLINK_REJECTED", "output summary must not be a symbolic link")
        if output_path.exists() and output_path.read_bytes() == payload:
            return False
        descriptor, temporary_name = tempfile.mkstemp(prefix=".m2-evidence-", suffix=".tmp", dir=output_dir)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, output_path)
        finally:
            try:
                Path(temporary_name).unlink()
            except FileNotFoundError:
                pass
        return True
    except GateError:
        raise
    except OSError:
        reject("IO_ERROR", "public summary could not be written")


def run_gate(input_dir: Path, sha_manifest: Path, output_dir: Path) -> dict[str, Any]:
    if input_dir.is_symlink():
        reject("SYMLINK_REJECTED", "input directory must not be a symbolic link")
    try:
        input_root = input_dir.resolve(strict=True)
    except (OSError, RuntimeError):
        pending("MISSING_INPUT", "input directory does not exist")
    if not input_root.is_dir():
        reject("INVALID_INPUT", "input must be a real directory")
    absolute_output = output_dir.absolute()
    for candidate in (absolute_output, *absolute_output.parents):
        if candidate.exists() and candidate.is_symlink():
            reject("SYMLINK_REJECTED", "output path must not traverse a symbolic link")
    output_root = absolute_output.resolve()
    try:
        output_root.relative_to(input_root)
    except ValueError:
        pass
    else:
        reject("OUTPUT_OVERLAP", "output directory must be outside the evidence input directory")
    if sha_manifest.is_symlink():
        reject("SYMLINK_REJECTED", "SHA manifest must not be a symbolic link")
    try:
        manifest_path = sha_manifest.resolve(strict=True)
    except (OSError, RuntimeError):
        pending("MISSING_MANIFEST", "SHA manifest does not exist")
    if not manifest_path.is_file():
        reject("INVALID_MANIFEST", "SHA manifest must be a regular file")

    listed = verify_manifest(input_root, manifest_path)
    bundle = load_bundle(input_root, listed)
    documents = load_and_validate_documents(input_root, bundle)
    summary = build_summary(bundle, documents)
    scan_private(summary, "public summary")
    changed = write_idempotent(output_root, summary)
    return {
        "schema": "jlceda-m2-evidence-gate-result/1.0",
        "gate": "passed",
        "code": "LIVE_EVIDENCE_VERIFIED",
        "changed": changed,
        "output": OUTPUT_NAME,
    }


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Validate and import sanitized M2 live evidence")
    parser.add_argument("--input-dir", type=Path, required=True, help="explicit sanitized evidence directory")
    parser.add_argument("--sha-manifest", type=Path, required=True, help="explicit SHA-256 manifest JSON")
    parser.add_argument("--output-dir", type=Path, required=True, help="directory for the minimal public summary")
    args = parser.parse_args(argv)
    try:
        result = run_gate(args.input_dir, args.sha_manifest, args.output_dir)
    except GateError as exc:
        result = {
            "schema": "jlceda-m2-evidence-gate-result/1.0",
            "gate": exc.gate,
            "code": exc.code,
            "message": exc.message,
            "changed": False,
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return exc.exit_code
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
