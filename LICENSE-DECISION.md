# License decision for v0.1.0-alpha

## Proposed license

Use the **Apache License 2.0** for the original code, schemas, skill text,
documentation, and synthetic evaluation data in this repository.

Apache-2.0 is preferred over MIT because it remains permissive while adding an
explicit patent grant and clear contribution terms. A separate documentation
license would add complexity without a clear benefit for this alpha.

The root `LICENSE` is the unmodified Apache License 2.0 text. The project
`NOTICE` supplies the project-level attribution and independence statement.

## Source and ownership findings

The staging audit found these source classes:

1. **Review engine and tests.** They were adapted from a private project
   working tree and made portable for this repository. No third-party code
   header or upstream license marker was found in the staged files.
2. **JSON schemas.** The staged schema files are byte-for-byte copies of schema
   files in the same private project working tree. That source snapshot had no
   project-level license file. This is not evidence of third-party ownership,
   but it makes an explicit maintainer authorship/relicensing attestation a
   mandatory release gate.
3. **Component profiles.** The structure and rule thresholds are project work.
   Manufacturer names, part numbers, and numeric specifications are factual
   evidence with link-only citations. Data-sheet prose, figures, and PDFs are
   excluded.
4. **Skill, documentation, and evaluation fixtures.** These are public-facing
   rewrites or synthetic fixtures. They must remain free of private runtime
   state and live project identity.

See `release-audit/SOURCE-BOUNDARY.md` for the detailed inclusion boundary.

## Mandatory ownership gate

Before a public tag or upload, a maintainer must record all of the following:

- the copyright holder name used for the release;
- confirmation that the project may license the review engine, schemas, tests,
  skill text, documentation, and synthetic fixtures under Apache-2.0;
- confirmation that no employer, client, contractor, or prior repository has a
  conflicting claim over those files;
- confirmation that the sanitized fixtures contain no private project material;
- confirmation that every third-party item in `THIRD_PARTY.md` is reference-only
  and that no third-party source or binary is bundled.

Until that sign-off exists, this directory is a **local release candidate**, not
a public release.

## Explicit exclusions

Apache-2.0 in this repository does not relicense or distribute:

- JLCEDA/EasyEDA, Codex, or EasyEDA Copilot software;
- extension packages, gateways, bridge runtimes, supplier catalogs, or EDA
  project files;
- manufacturer data-sheet PDFs;
- screenshots, private logs, conversations, credentials, receipts, checkpoints,
  approvals, or machine state;
- vendored dependency directories or generated binary caches.

This document records a release recommendation and provenance gate, not legal
advice.
