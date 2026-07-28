# Privacy and release sanitization

This repository is designed to be reviewable without publishing a workstation, private EDA project or third-party extension internals.

## Included data

- original review rules, tests and schemas;
- synthetic or manually sanitized fixtures;
- repository-relative evidence references;
- manufacturer name, MPN, package and pin-to-pad facts when redistribution is permitted;
- public document title and official URL instead of a bundled data-sheet PDF;
- fixture-scoped aggregate facts needed to reproduce an evaluation.

## Excluded data

- usernames and workstation-specific absolute paths;
- real project, document, object, library or board identifiers;
- approval, receipt, checkpoint, nonce or transaction identifiers;
- access tokens, cookies, authorization headers, passwords and private keys;
- full private logs, historical conversations and process dumps;
- screenshots containing accounts, other projects or private workspace details;
- EasyEDA Copilot source, extension packages or other third-party binaries;
- manufacturer data-sheet PDFs or supplier catalog exports without redistribution permission.

## Fixture policy

Each public evaluation manifest declares a `fixtureKind`, an `execution.status`, two explicit live-verification booleans and its EDA write count. Current examples include `synthetic-unit`, `synthetic-offline-before`, `synthetic-offline-successor` and `sanitized-adversarial-replay`.

An offline forecast must not be relabeled as live evidence. The public M2 eval inputs remain synthetic offline fixtures even though their manifests link to a separate gate-verified live summary. `edaWritesInThisReleaseFixture` therefore remains zero, while the linked summary carries the sanitized real verification result.

M2 evidence enters through the offline [M2 evidence gate](m2-evidence-gate.md).
The importer requires exact SHA coverage, rejects private fields and paths, and
copies only aggregate counts and verification states into one public summary.
Raw receipts and their identifiers remain outside the repository. Positive unit
fixtures remain synthetic branch inputs and are not the source of the live claim.

## Screenshot policy

Screenshots are excluded by default. If a future release needs one, crop it to the single relevant design region, remove account and project navigation, strip metadata, and record the sanitization steps. A screenshot is supplementary evidence, not the machine source of truth.

## Release scan

Before packaging, scan the entire candidate for:

- workstation path prefixes and usernames;
- UUID-like and long hexadecimal identifiers;
- internal approval/receipt/checkpoint terminology with concrete values;
- secret and credential patterns;
- binary files, oversized files and image metadata;
- invalid JSON/YAML and malformed UTF-8 or mojibake.

Every hit must be removed, replaced with a synthetic placeholder, or recorded in a narrow allowlist with a public reason. High-risk unexplained hits block release.

## Reporting a privacy issue

Follow the private reporting process in [SECURITY.md](../SECURITY.md). Include the affected public path and data class; do not paste a live credential or private project export into a public issue.
