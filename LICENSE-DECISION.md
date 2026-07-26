# License decision for v0.1.0-alpha

## Proposed license and present status

Use the **Apache License 2.0** for project-owned code, schemas, skill text,
documentation, and synthetic or sanitized-derived evaluation data in this
repository.

Apache-2.0 is preferred over MIT because it remains permissive while adding an
explicit patent grant and clear contribution terms. A separate documentation
license would add complexity without a clear benefit for this alpha.

The root `LICENSE` is intended to be the verbatim Apache License 2.0 text and
contains the expected title, Sections 1-9, and application appendix. The final
release owner should compare it with the official Apache source before a public
tag. The project `NOTICE` supplies project-level attribution and an independence
statement; it does not import a third-party NOTICE file.

The `Apache-2.0` value in package metadata expresses this proposed release
license. It is not evidence that the current contributor label owns every
staged file. The ownership gate below remains binding.

## Source and ownership findings

The staging audit found these source classes:

1. **Review engine and tests.** They were adapted from a private project working
   tree and made portable for this repository. The command scripts are thin
   project-authored release wrappers. No third-party code header, vendored
   package, or upstream license marker was found in the staged files. A local
   text audit cannot establish chain of title.
2. **JSON schemas.** Eight general hardware-contract/change-management schemas
   are byte-for-byte copies of schema files in the same private project working
   tree. That source snapshot had no project-level license file. The Prototype
   review/profile schemas and M2 evidence-gate schemas were authored for this
   release candidate. Neither provenance class is evidence of third-party
   ownership, but both remain inside the explicit maintainer authorship and
   Apache-2.0 relicensing gate.
3. **Component profiles.** The structure and rule thresholds are project work.
   Manufacturer names, part numbers, and numeric specifications are factual
   evidence with link-only citations. Data-sheet prose, figures, and PDFs are
   excluded.
4. **Skill and documentation.** These are public-facing rewrites or new release
   documents. Rewriting private expression does not by itself settle ownership;
   the maintainer must confirm the right to publish the result.
5. **Evaluation fixtures.** The safe and power-distribution cases are synthetic.
   The car-controller case is a sanitized adversarial replay derived from a
   private project fixture. Sanitization addresses privacy, not copyright or
   contractual ownership, so all fixtures remain inside the ownership gate.
6. **Generated release records.** Integrity lists and audit reports are generated
   from repository state. They carry no independent third-party code, but must
   be regenerated whenever tracked content changes.
7. **M2 import and release tooling.** The evidence gate, release verification,
   integrity, archive scripts, schemas, and their tests were authored for this
   candidate. Their fixtures are synthetic gate inputs, including positive
   documents whose `live` fields exercise validation semantics; those fixtures
   are not observations from a live EDA project.

See `release-audit/SOURCE-BOUNDARY.md` for the detailed inclusion boundary.
See `release-audit/FILE-PROVENANCE.md` for the per-file classification.

## Why Apache-2.0 is compatible with the staged boundary

Subject to the ownership attestation, Apache-2.0 is suitable because the
runtime code has no bundled non-standard-library dependency and the repository
does not include third-party source, binaries, catalog databases, data-sheet
documents, or specification text. The root `LICENSE` is the deliberate exception:
it contains the standard license text governing project-owned material. The
explicit patent grant and contribution terms are useful for a code-and-schema
project.

The following items do not become Apache-2.0 project assets merely by appearing
in the repository:

- third-party names and marks used for identification or interoperability;
- manufacturer names, product numbers, short document titles, package names,
  and numeric engineering facts used as citations;
- public specification names and URIs, including JSON Schema and IPC-2221;
- user-provided runtimes, host applications, renderers, validators, or services.

Their treatment is recorded in `THIRD_PARTY.md`. If future work copies source,
prose, tables, figures, schemas, binaries, or datasets from one of those sources,
that material needs its own license review and must not inherit Apache-2.0 by
default.

## Mandatory ownership gate

Before a public tag or upload, a maintainer must record all of the following:

- the copyright holder name used for the release;
- confirmation that the project may license the review engine, schemas, tests,
  scripts, skill text, documentation, and synthetic or sanitized-derived
  fixtures under Apache-2.0;
- confirmation that no employer, client, contractor, or prior repository has a
  conflicting claim over those files;
- identification of any AI-assisted material, confirmation that applicable tool
  terms permit publication, and human review sufficient to support the chosen
  copyright and contribution statements;
- confirmation that the sanitized fixtures contain no private project material;
- confirmation that every third-party item in `THIRD_PARTY.md` is reference-only
  and that no third-party source or binary is bundled.
- comparison of `LICENSE` with the official Apache License 2.0 text and approval
  of the final copyright line used in `NOTICE`.

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
