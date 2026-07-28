#!/usr/bin/env python3
"""Audit component-profile provenance and freshness without network access."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


AUDIT_SCHEMA = "jlceda-component-profile-audit/1.0"
PROFILE_SCHEMA = "jlceda-component-profiles/1.0"
SOURCE_TYPES = {"official_datasheet", "synthetic_fixture"}
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}\Z")


def _parse_date(value: Any, label: str) -> tuple[date | None, str | None]:
    if not isinstance(value, str) or not DATE_PATTERN.fullmatch(value):
        return None, f"{label} must be an ISO 8601 calendar date (YYYY-MM-DD)"
    try:
        return date.fromisoformat(value), None
    except ValueError:
        return None, f"{label} must be a valid calendar date"


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _finding(profile_id: str, code: str, field: str, message: str) -> dict[str, str]:
    return {"profileId": profile_id, "code": code, "field": field, "message": message}


def audit_profiles(profiles: Any, as_of: date) -> dict[str, Any]:
    """Return a deterministic fail-closed audit result for a profile document."""

    findings: list[dict[str, str]] = []
    audited: list[dict[str, Any]] = []
    source_type_counts = {source_type: 0 for source_type in sorted(SOURCE_TYPES)}

    if not isinstance(profiles, dict):
        findings.append(_finding("$document", "DOCUMENT_NOT_OBJECT", "$", "profile document must be a JSON object"))
        rows: dict[str, Any] = {}
    else:
        if profiles.get("schema") != PROFILE_SCHEMA:
            findings.append(
                _finding(
                    "$document",
                    "SCHEMA_UNSUPPORTED",
                    "schema",
                    f"profile schema must equal {PROFILE_SCHEMA}",
                )
            )
        raw_rows = profiles.get("profiles")
        if not isinstance(raw_rows, dict):
            findings.append(_finding("$document", "PROFILES_NOT_OBJECT", "profiles", "profiles must be a JSON object"))
            rows = {}
        else:
            rows = raw_rows

    for profile_id in sorted(rows):
        profile = rows[profile_id]
        profile_findings: list[dict[str, str]] = []
        if not isinstance(profile_id, str) or not profile_id:
            profile_findings.append(_finding(str(profile_id), "PROFILE_ID_INVALID", "profileId", "profile id must be non-empty"))
        if not isinstance(profile, dict):
            profile_findings.append(_finding(str(profile_id), "PROFILE_NOT_OBJECT", "$", "profile must be a JSON object"))
            findings.extend(profile_findings)
            audited.append({"profileId": str(profile_id), "state": "invalid", "sourceType": None, "reviewAfter": None})
            continue

        source = profile.get("source")
        if not isinstance(source, dict):
            profile_findings.append(_finding(profile_id, "SOURCE_NOT_OBJECT", "source", "source must be a JSON object"))
            findings.extend(profile_findings)
            audited.append({"profileId": profile_id, "state": "invalid", "sourceType": None, "reviewAfter": None})
            continue

        source_type = source.get("sourceType")
        if source_type not in SOURCE_TYPES:
            profile_findings.append(
                _finding(
                    profile_id,
                    "SOURCE_TYPE_INVALID",
                    "source.sourceType",
                    "sourceType must be official_datasheet or synthetic_fixture",
                )
            )
        else:
            source_type_counts[source_type] += 1

        for field in ("documentRevision", "provenanceStatement"):
            if not _non_empty_string(source.get(field)):
                profile_findings.append(
                    _finding(profile_id, "PROVENANCE_FIELD_MISSING", f"source.{field}", f"{field} must be a non-empty string")
                )

        revision = source.get("documentRevision")
        if revision == "not stated" and not _non_empty_string(source.get("revisionBasis")):
            profile_findings.append(
                _finding(
                    profile_id,
                    "REVISION_BASIS_MISSING",
                    "source.revisionBasis",
                    "revisionBasis is required when documentRevision is not stated",
                )
            )

        retrieved_at, retrieved_error = _parse_date(source.get("retrievedAt"), "retrievedAt")
        if retrieved_error:
            profile_findings.append(_finding(profile_id, "RETRIEVED_AT_INVALID", "source.retrievedAt", retrieved_error))
        elif retrieved_at is not None and retrieved_at > as_of:
            profile_findings.append(
                _finding(profile_id, "RETRIEVED_AT_FUTURE", "source.retrievedAt", "retrievedAt must not be later than as-of")
            )

        review_after: date | None = None
        explicit_review_after = source.get("reviewAfter")
        max_age_days = source.get("maxAgeDays")
        if explicit_review_after is None and max_age_days is None:
            profile_findings.append(
                _finding(
                    profile_id,
                    "FRESHNESS_POLICY_MISSING",
                    "source.reviewAfter",
                    "reviewAfter or maxAgeDays is required",
                )
            )
        if explicit_review_after is not None:
            review_after, review_error = _parse_date(explicit_review_after, "reviewAfter")
            if review_error:
                profile_findings.append(_finding(profile_id, "REVIEW_AFTER_INVALID", "source.reviewAfter", review_error))
        if max_age_days is not None:
            if isinstance(max_age_days, bool) or not isinstance(max_age_days, int) or not 1 <= max_age_days <= 3650:
                profile_findings.append(
                    _finding(
                        profile_id,
                        "MAX_AGE_DAYS_INVALID",
                        "source.maxAgeDays",
                        "maxAgeDays must be an integer from 1 through 3650",
                    )
                )
            elif retrieved_at is not None:
                calculated_review_after = retrieved_at + timedelta(days=max_age_days)
                review_after = min(review_after, calculated_review_after) if review_after else calculated_review_after

        if retrieved_at is not None and review_after is not None and review_after <= retrieved_at:
            profile_findings.append(
                _finding(
                    profile_id,
                    "FRESHNESS_WINDOW_INVALID",
                    "source.reviewAfter",
                    "effective reviewAfter must be later than retrievedAt",
                )
            )
        if review_after is not None and as_of > review_after:
            profile_findings.append(
                _finding(profile_id, "SOURCE_STALE", "source.reviewAfter", "source provenance is stale as of the requested date")
            )

        url = source.get("url")
        if source_type == "official_datasheet":
            parsed = urlparse(url) if isinstance(url, str) else None
            if parsed is None or parsed.scheme != "https" or not parsed.netloc:
                profile_findings.append(
                    _finding(
                        profile_id,
                        "OFFICIAL_HTTPS_URL_REQUIRED",
                        "source.url",
                        "official datasheet source must provide an absolute HTTPS URL",
                    )
                )
            if not _non_empty_string(source.get("pageOrTable")):
                profile_findings.append(
                    _finding(
                        profile_id,
                        "SOURCE_LOCATION_MISSING",
                        "source.pageOrTable",
                        "official datasheet source must identify a page, table or section",
                    )
                )
        elif source_type == "synthetic_fixture":
            if url is not None:
                profile_findings.append(
                    _finding(
                        profile_id,
                        "SYNTHETIC_URL_MUST_BE_NULL",
                        "source.url",
                        "synthetic fixture source must use a null URL",
                    )
                )
            redistribution = source.get("redistribution")
            if not _non_empty_string(redistribution) or "synthetic" not in redistribution.lower():
                profile_findings.append(
                    _finding(
                        profile_id,
                        "SYNTHETIC_ORIGIN_UNCLEAR",
                        "source.redistribution",
                        "synthetic fixture redistribution must explicitly identify synthetic origin",
                    )
                )

        findings.extend(profile_findings)
        state = "invalid" if profile_findings else "fresh"
        if any(item["code"] == "SOURCE_STALE" for item in profile_findings):
            state = "stale"
        audited.append(
            {
                "profileId": profile_id,
                "state": state,
                "sourceType": source_type if source_type in SOURCE_TYPES else None,
                "retrievedAt": retrieved_at.isoformat() if retrieved_at else None,
                "reviewAfter": review_after.isoformat() if review_after else None,
            }
        )

    findings.sort(key=lambda item: (item["profileId"], item["code"], item["field"], item["message"]))
    audited.sort(key=lambda item: item["profileId"])
    states = {state: sum(1 for row in audited if row["state"] == state) for state in ("fresh", "stale", "invalid")}
    return {
        "schema": AUDIT_SCHEMA,
        "status": "pass" if not findings else "fail",
        "asOf": as_of.isoformat(),
        "profileCount": len(rows),
        "sourceTypeCounts": source_type_counts,
        "states": states,
        "auditedProfiles": audited,
        "findingCount": len(findings),
        "findings": findings,
    }


def audit_file(path: Path, as_of: date) -> dict[str, Any]:
    try:
        profiles = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        finding = _finding("$document", "DOCUMENT_UNREADABLE", "$", f"could not read valid JSON: {exc}")
        return {
            "schema": AUDIT_SCHEMA,
            "status": "fail",
            "asOf": as_of.isoformat(),
            "profileCount": 0,
            "sourceTypeCounts": {source_type: 0 for source_type in sorted(SOURCE_TYPES)},
            "states": {"fresh": 0, "stale": 0, "invalid": 0},
            "auditedProfiles": [],
            "findingCount": 1,
            "findings": [finding],
        }
    return audit_profiles(profiles, as_of)


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profiles", type=Path, default=Path(__file__).with_name("component-profiles.json"))
    parser.add_argument("--as-of", required=True, help="explicit audit date in YYYY-MM-DD format")
    args = parser.parse_args(argv)
    as_of, error = _parse_date(args.as_of, "as-of")
    if error or as_of is None:
        parser.error(error or "invalid as-of date")
    result = audit_file(args.profiles, as_of)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
