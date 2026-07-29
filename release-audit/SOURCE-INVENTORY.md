# Source inventory

This inventory records how the staged v0.1.0-alpha files were assembled. It is an internal release-review aid and contains no workstation paths.

| Area | Classification | Treatment in staging | Release note |
| --- | --- | --- | --- |
| `src/review/prototype_review.py` | Original project code | Copied from the private working tree, then changed to machine-stable English ratings and repository-relative evidence output | Read-only deterministic Prototype review core |
| `src/review/component-profiles.json` | Original project rule facts plus third-party factual citations | Local PDF filenames replaced by manufacturer/title/official-link metadata; PDFs excluded | Numeric facts must be rechecked against current official revisions |
| Eight general `schemas/*.schema.json` contracts | Original project schemas | Copied without live runtime state or example identifiers | Ownership/relicensing attestation required; no bridge runtime included |
| Prototype/profile and M2 evidence schemas | Original release-candidate work | Authored for the portable review and evidence-import surfaces | Synthetic tests only; schemas do not establish live capability |
| `tests/review/*` | Original project tests and synthetic fixtures | Paths made repository-relative; adversarial input regenerated as a sanitized synthetic fixture | No live project identity |
| `skills/jlceda-hardware-design/*` | Public rewrite of an original private skill | Rewritten around portable triggers, evidence gates and bounded claims | Private wrappers, approvals and machine paths removed |
| `README*`, `docs/*`, `INSTALL.md`, `CONTRIBUTING.md`, `CHANGELOG.md` | Original public documentation | Written for the alpha candidate | Claims must match committed files and fixture status |
| `evals/*` | Synthetic/sanitized evaluation successors | Regenerated from engineering structures; internal IDs and raw evidence excluded | M2 fixtures remain offline; manifests link a separately gate-verified minimal live summary |
| `scripts/import_m2_evidence.py`, `tests/m2_gate/` and `release-audit/m2-live-evidence-summary.json` | Original release-candidate gate code, synthetic gate fixtures and generated sanitized summary | Created for explicit hashed import, privacy rejection and idempotent minimal-summary generation | Synthetic positive branch is not live evidence; the public live claim comes only from the separately reviewed gate output |
| `scripts/build-readonly-adapter-envelope.py`, `src/review/readonly_adapter_export.py` and `tests/review/test_readonly_adapter_export.py` | Original post-release project code and tests | Created for explicit offline assembly of the public read-only adapter envelope from already sanitized capture facts | Does not collect from EDA, infer state, approve changes or emit partial evidence |
| `scripts/validate-readonly-adapter-health.py`, `src/review/readonly_adapter_health.py`, `schemas/readonly-adapter-health.schema.json` and `tests/review/test_readonly_adapter_health.py` | Original post-release project code, schema and tests | Created for offline validation of external adapter transport/session/protocol health before any live evidence collection | Does not make network requests, select windows, read EDA state or grant mutation permission |
| Release verification/build scripts and tests | Original release-candidate code | Created for deterministic scanning, integrity generation and Git-tree packaging | Operates locally; no network publication action |
| `LICENSE` | Apache License 2.0 standard text | Included as proposed root license | Applies only after ownership review passes |
| `NOTICE`, `THIRD_PARTY.md` | Original attribution documents | Distinguish original work, reference-only dependencies and excluded artifacts | No third-party source or binaries bundled |

## Original value proposed for publication

- Draft/Prototype/Manufacturing Release governance model;
- explainable three-rating Prototype review;
- finding evidence and confidence model;
- deterministic electrical, thermal, protection, layout and persistence screening rules;
- immutable-plan and allow-list repair policy;
- sanitized positive and adversarial evaluation design;
- reusable JSON schemas and tests.

## Reference-only or excluded capabilities

- JLCEDA/EasyEDA application and APIs;
- third-party draft-generation adapters, including EasyEDA Copilot;
- live bridge/gateway delivery, approval and recovery implementations;
- manufacturer data-sheet PDFs and supplier catalogs;
- raw EDA projects, screenshots, logs, receipts, checkpoints and machine state.

No excluded capability should be described as original project code or as a generally demonstrated alpha feature.
