# v0.1.4-alpha release checklist

This checklist distinguishes completed local release preparation from human decisions and any future network publication.

## Scope and product claims

- [x] Positioning says this is a Prototype-readiness quality gate, not merely an AI PCB drawing tool.
- [x] The user-facing loop is stated consistently: ordinary-language need → real editable schematic/PCB → independent automated review → allow-listed correction → save/reload re-verification → plain-language prototype rating.
- [x] Draft generators are described as replaceable adapters; the independent review and bounded re-validation loop is the trusted core.
- [x] Automatic repair claims are limited to the published allow-list status.
- [x] M2 BEFORE/AFTER inputs remain labeled as offline fixtures and are kept separate from the gate-verified minimal live summary.
- [x] The car-controller `9/9` statement is limited to nine predefined/manual risk families on one 28-component fixture.
- [x] No general Manufacturing Release, certification or physical-function claim is made.
- [x] Live EDA is described as a separately audited environment integration.
- [x] A second independent NOT FOR MANUFACTURING fixture completed the guided read-only environment qualification with zero EDA writes; raw identities and receipts remain outside the public candidate.

## Source and licensing

- [x] Apache-2.0 text, license decision, NOTICE and third-party boundary are present.
- [x] Third-party Copilot source/binary/extension, data-sheet PDFs and supplier catalogs are excluded.
- [x] Original review code, schemas, skill and docs are separated from reference-only third parties.
- [x] **Maintainer:** record the final copyright-holder name. *(2026-07-28: `Copyright 2026 Fpj5085` in LICENSE and NOTICE.)*
- [x] **Maintainer:** attest authorship or Apache-2.0 relicensing rights for the review engine, schemas, tests, skill, docs and synthetic fixtures. *(2026-07-28: attested in LICENSE-DECISION.md.)*
- [x] **Maintainer:** confirm no employer, client, contractor or prior repository has a conflicting claim. *(2026-07-28: confirmed, entirely self-developed.)*
- [x] **Maintainer:** identify AI-assisted material, confirm applicable tool terms permit publication, and approve the final human-reviewed expression. *(2026-07-28: tool terms permit publication and commercial use; maintainer reviewed and approved the released expression, and elected not to add a repository-level AI-assistance notice.)*

## Functional validation

- [x] Local-only addition after this checklist: closed-loop public example for the real M2 case (cleaned inputs + one-command offline demo `scripts/run-closed-loop-demo.py`); it replays only the offline needs→contract→review→rating chain, performs no EDA write and claims no automatic repair; not published, integrity files regenerated (174 files).
- [x] Local-only addition after this checklist: offline fail-closed requirements gate (requirements-input schema, `src/spec/requirements_gate.py`, `scripts/requirements-gate.py`, `tests/spec/`) adds 33 passing tests on top of the 105 published suite; not pushed, tagged or uploaded, and integrity files regenerated.
- [x] Local-only addition after this checklist: `hardware-contract` schema status enum extended (additive) with `requirements-complete` and `requirements-incomplete`; the gate output is self-checked against the schema; not published, integrity files regenerated.
- [x] Verified in v0.1.4-alpha: offline contract→review-input converter (`src/spec/contract_to_review.py`, `scripts/contract-to-review-cli.py`, `tests/spec/test_contract_to_review.py`) projects the gate's `hardware-contract` into `jlceda-prototype-review-input/1.0`, re-validates its output with the review engine's own validator, and closes the offline needs→contract→review→rating chain; a 28-test `tests/spec/test_contract_to_review.py` suite covers mapping, fail-closed negatives, determinism and end-to-end review.
- [x] Verified in v0.1.4-alpha: the closed-loop demo (`scripts/run-closed-loop-demo.py`) auto-converts the gate's hardware contract into review input (`review-input.json`) by default, so the one-command "中文需求 → 规格 → 自动转换 → 审核 → 评级" chain needs no prefab design data; the explicit `--design` override keeps the old prefab path, and the default fail-closed outcome is one `PERSISTENCE` blocker plus three data-completeness advisories (`TRACE_DATA_MISSING`×2, `EVIDENCE_SCOPE:OFFLINE_FORECAST`), covered by 4 end-to-end regression tests in `tests/review/test_closed_loop_demo.py`.
- [x] Verified in v0.1.4-alpha: schematic sheet-frame containment (additive `schematicSheet` block in the review-input schema + new `schematic_containment` rule family in `src/review/prototype_review.py`) lets the engine geometrically detect components drawn outside the schematic page from component x/y plus page frame, emitting `SCHEMATIC_CONTAINMENT:<ref>` blockers or an aggregate pass with mm evidence, `CONTAINMENT_DATA_MISSING` advisories for coordinates it cannot see, and a short-circuit on an externally-decided `schematicSheet.containment` bool; 10 new tests include a real M2 BEFORE/AFTER replay (old units -355..335 → 5 blockers; fixed 280..890 / -620..-200 units → pass).
- [x] Complete Python suite: 180/180, covering Prototype/runtime, M2 evidence import, local-bypass planning, profile audit, input safety, diverse benchmarks, read-only adapter contracts, health gate, Pipeline, requirements gate, contract→review converter, schematic containment, closed-loop demo, no-delete test-workspace archival and release tooling.
- [x] Sanitized/synthetic eval replay: 10/10.
- [x] Component-profile audit: 11/11 fresh, 0 stale, 0 invalid at the locked as-of date.
- [x] Python CLI smoke passed (synthetic-safe → `suitable_for_low_risk_prototype`).
- [x] PowerShell wrapper smoke passed (same fixture).
- [x] Plugin manifest JSON parse passed; `.codex-plugin/plugin.json` layout is unchanged from the reviewed v0.1.3 structure apart from the version string.
- [x] Skill layout unchanged from the reviewed v0.1.3 structure; bundled JSON/YAML passes release-verify parsing.
- [x] All 19 JSON Schemas parsed; health and envelope contracts are additionally covered by strict Python validators.
- [x] Public JSON instances parse cleanly; `prototype-review-input`/`prototype-review-output`/`hardware-contract`/`requirements-input` documents are exercised at runtime through the engine's schema-backed validators in the 180-test suite and the closed-loop demo.
- [x] JSON/YAML parsing, Python syntax and 125 Markdown relative-link checks passed.
- [x] The deterministic M2 import gate covers success, pending, missing evidence, hash mismatch, privacy rejection and idempotence.
- [x] Integrity generation and Git-tree ZIP construction have repeatable command entries and regression tests.

## Privacy and release hygiene

- [x] Concrete username, absolute path, UUID, internal runtime ID and credential findings are zero.
- [x] No private logs, screenshots, conversations, raw EDA projects or machine state are included.
- [x] No PDF, EDA extension, executable, unexplained archive or file over 1 MiB is included in the repository.
- [x] Test workspaces were moved by rename into an external archive; temporary output and Python bytecode caches are absent from the candidate tree.
- [x] Allow-listed long hexadecimal values are only documented SHA-256 file digests.
- [x] Public file list, excluded-file list, privacy scan and test report are present.

## Evaluation evidence

- [x] `synthetic-safe` offline eval is fail-closed; the separate complete-evidence semantic fixture still exercises the strict passing path.
- [x] `power-distribution-before` fixture has one intended decoupling blocker.
- [x] `power-distribution-after` closes the engineering blocker in offline replay while its fixture strict rating remains `suitable_after_corrections`.
- [x] `car-controller-adversarial` reproduces the scoped engineering risk benchmark.
- [x] All evals include input, expected result, current manifest, manifest template, status and README.
- [x] A separately reviewed sanitized M2 bundle passed the existing hash/privacy gate; only its minimal generated summary is public.
- [x] BEFORE/AFTER manifests link the verified live summary while preserving zero writes in each offline fixture.
- [x] The positive M2 importer unit fixture remains explicitly synthetic and cannot by itself promote either live-verification flag.

## Integrity and local packaging

- [x] `FILE-MANIFEST.json` and `SHA256SUMS.txt` regenerated from repository-relative files; a second `update-integrity.py` run reported `manifestChanged: false` / `sumsChanged: false` (idempotent).
- [x] Local Git repository initialized and candidate commits exist (base 9af3c00).
- [x] Working tree contains no untracked artifacts after the integrity update (bytecode caches and demo outputs are absent; only the reviewed tracked changes remain).
- [ ] Local ZIP created from the committed tree without `.git/` — pending the maintainer commit of the v0.1.4-alpha changes (the release builder requires a clean committed tree by design).
- [ ] ZIP inventoried and matched byte-for-byte to the committed file set — pending the maintainer commit.
- [ ] ZIP SHA-256 sidecar generated outside the repository tree — pending the maintainer commit.

## Network publication

- [x] Public repository `Fpj5085/pcb-prototype-quality-gate` and published prereleases `v0.1.1-alpha` / `v0.1.3-alpha` remain unchanged by this preparation (no push, tag or upload was performed).
- [x] No v0.1.4-alpha GitHub push, tag, Release upload or network publication was performed during preparation.
- [ ] **Maintainer:** review the final v0.1.4-alpha commit, ZIP and SHA-256 sidecar.
- [ ] **Maintainer:** make the separate final decision to push the reviewed commit, create tag/Release `v0.1.4-alpha`, and upload the reviewed archive.

Unchecked human/publication items do not block this **local review candidate**. They intentionally block a public tag or upload.
