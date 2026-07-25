# Privacy, secret and release-hygiene scan

Candidate: `codex-jlceda-hardware-agent` v0.1.0-alpha  
Scope: the complete repository tree excluding local Git metadata.

## Result

**Concrete high-risk findings: 0.**

| Check | Result | Notes |
| --- | ---: | --- |
| Workstation username under review | 0 | No literal private username retained |
| Windows/UNC or user-home absolute paths | 0 | Runtime privacy tests construct sentinels without storing a real path |
| Concrete UUID values | 0 | Schema property names are syntax, not values |
| Concrete project/page/PCB/object/library/device IDs | 0 | Public evals use synthetic stable case IDs only |
| Concrete approval/receipt/checkpoint/bundle/nonce values | 0 | Policy vocabulary is allow-listed; no runtime record is included |
| Credential assignment, bearer/cookie value or private-key header | 0 | Deterministic pattern scan passed |
| Invalid UTF-8 or replacement/private-use/control characters | 0 | Text decode gate passed |
| Unparseable JSON | 0 | All public JSON parsed |
| Unparseable YAML | 0 | Public YAML parsed |
| Missing Markdown relative links | 0 | Link gate passed |
| Images, PDFs, extension packages, logs, archives or executables in repository | 0 | Local release ZIP is generated outside the repository tree |
| Files larger than 1 MiB | 0 | No unexplained large file |
| `.tmp-*`, `__pycache__`, `*.pyc` or `*.pyo` | 0 | Removed before manifest and commit |

## Long hexadecimal values

The only permitted 64-character hexadecimal values in the final candidate are file SHA-256 digests in `FILE-MANIFEST.json`, `SHA256SUMS.txt` and release-audit integrity prose. They are bound to repository-relative file names and are not project, session, approval or object identifiers.

No unexplained 16–64-character hexadecimal value is permitted elsewhere.

## Narrow allowlist

The machine-readable rationale is in `release-audit/PRIVACY-SCAN-ALLOWLIST.json`. It covers only:

- generic schema property names such as project or change identifiers;
- security-policy words used to prohibit credentials and runtime receipts;
- non-resolving `.invalid` schema identifiers;
- official manufacturer evidence URLs;
- repository file SHA-256 digests.

It does not permit a concrete live value.

## Third-party and private material check

The candidate contains no EasyEDA Copilot source or extension package, no EDA/Gateway binary, no manufacturer data-sheet PDF, no supplier catalog, no private bridge runtime, no raw EDA project, no screenshot, no private log and no historical conversation.

Manufacturer facts are represented as factual metadata plus official links. The ownership/relicensing decision for original project code and schemas remains a human gate in `LICENSE-DECISION.md` and `RELEASE-CHECKLIST.md`.

## Tooling note

`gitleaks` was not installed locally. Credential screening used deterministic repository-wide regular-expression checks for common secret assignments and private-key headers, plus the tests documented in `TEST-REPORT.md`. This limitation is recorded rather than presented as a tool pass.

## External M2 evidence

The latest read-only M2 check still showed offline artifact preparation with zero live EDA calls. No external raw evidence was copied; public BEFORE/AFTER manifests remain pending as documented in `release-audit/M2-INTEGRATION-STATUS.md`.
