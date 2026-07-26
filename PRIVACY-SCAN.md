# Privacy, secret and release-hygiene scan

Candidate: `codex-jlceda-hardware-agent` v0.1.0-alpha  
Scope: the complete repository tree excluding local Git metadata.

## Result

**Concrete high-risk findings: 0.**

The deterministic final scan covers 121 public files. Every current file is also
classified in `release-audit/FILE-PROVENANCE.md`.

| Check | Result | Notes |
| --- | ---: | --- |
| Workstation username under review | 0 | The literal private username is absent |
| Windows/UNC or user-home absolute paths | 0 | Tests construct sentinels at runtime without storing a real path |
| Concrete UUID values | 0 | Generic schema field names and regex syntax are not values |
| Concrete project/page/PCB/object/library/device IDs | 0 | Public cases use descriptive synthetic references only |
| Concrete approval/receipt/checkpoint/bundle/nonce values | 0 | Policy vocabulary is allowed; runtime values are absent |
| Credential assignment, bearer/cookie value or private-key header | 0 | Repository-wide deterministic pattern gate passed |
| Invalid UTF-8, replacement character or known mojibake marker | 0 | 121 text files passed |
| Unparseable JSON | 0 | 52 public JSON files parsed |
| Unparseable restricted YAML | 0 | The single host metadata file passed |
| Missing Markdown relative links | 0 | 104 links across 47 Markdown files passed |
| Images, PDFs, extension packages, logs, archives or executables in repository | 0 | The local release ZIP is outside the repository tree |
| Files larger than 1 MiB | 0 | No unexplained large file |
| Symbolic links | 0 | Release inventory contains regular files only |
| `.tmp-*`, `__pycache__`, `*.pyc` or `*.pyo` | 0 | Removed before integrity generation |

## M2 evidence gate

The import gate rejects absolute paths, UUIDs, opaque identifiers, credential-like
values, sensitive identifier fields, symbolic links, unmanifested files and hash
mismatches before writing output. Its successful branch writes one aggregate
summary and copies no raw receipt or project identity.

Files under `tests/m2_gate/fixtures/` are synthetic branch-coverage data. Their
positive `live` booleans are test values and do not change the public M2 status,
which remains pending.

## Long hexadecimal values

Final 64-character hexadecimal values are limited to labelled SHA-256 integrity
records in `FILE-MANIFEST.json`, `SHA256SUMS.txt` and narrowly classified audit
context. The scanner requires surrounding integrity vocabulary and rejects an
unexplained long hexadecimal value elsewhere.

The machine-readable rationale is in
`release-audit/PRIVACY-SCAN-ALLOWLIST.json`. It permits syntax and policy
vocabulary, not a concrete live identifier or credential.

## Third-party and private material

The candidate contains no EasyEDA Copilot source or extension package, no
EDA/Gateway binary, no manufacturer data-sheet PDF, no supplier catalog, no
private bridge runtime, no raw EDA project, no screenshot, no private log and no
historical conversation.

Manufacturer facts are represented as factual metadata plus official links.
Source and relicensing decisions remain human gates in `LICENSE-DECISION.md`,
`release-audit/FILE-PROVENANCE.md` and `RELEASE-CHECKLIST.md`.

## Tooling note

`gitleaks` was not installed locally. Credential screening used the published
standard-library repository gate plus regression tests. The exact limitation is
recorded here instead of being presented as a third-party tool pass.

## External M2 evidence

No external M2 artifact was read or copied in this release-hardening task. The
authoritative starting state kept both live-verification booleans false, and the
candidate preserves that pending state. A future sanitized bundle must pass
`scripts/import_m2_evidence.py` before any public live claim is considered.
