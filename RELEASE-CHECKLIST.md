# v0.1.0-alpha release checklist

This checklist distinguishes completed local release preparation from human decisions and any future network publication.

## Scope and product claims

- [x] Positioning says this is a Prototype-readiness quality gate, not merely an AI PCB drawing tool.
- [x] Automatic repair claims are limited to the published allow-list status.
- [x] M2 BEFORE/AFTER is labeled offline/pending rather than live save/reload proof.
- [x] The car-controller `9/9` statement is limited to nine predefined/manual risk families on one 28-component fixture.
- [x] No general Manufacturing Release, certification or physical-function claim is made.
- [x] Live EDA is described as a separately audited environment integration.

## Source and licensing

- [x] Apache-2.0 text, license decision, NOTICE and third-party boundary are present.
- [x] Third-party Copilot source/binary/extension, data-sheet PDFs and supplier catalogs are excluded.
- [x] Original review code, schemas, skill and docs are separated from reference-only third parties.
- [ ] **Maintainer:** record the final copyright-holder name.
- [ ] **Maintainer:** attest authorship or Apache-2.0 relicensing rights for the review engine, schemas, tests, skill, docs and synthetic fixtures.
- [ ] **Maintainer:** confirm no employer, client, contractor or prior repository has a conflicting claim.

## Functional validation

- [x] Unit and release-runtime tests: 21/21.
- [x] Sanitized eval replay: 4/4.
- [x] Python CLI smoke passed.
- [x] PowerShell wrapper smoke passed.
- [x] Plugin manifest validator passed.
- [x] Skill validator passed.
- [x] All 11 JSON Schemas compiled with a local Draft 2020-12 validator.
- [x] Component profiles plus four review inputs and four outputs validated against public schemas.
- [x] JSON/YAML parsing, Python syntax and Markdown relative-link checks passed.

## Privacy and release hygiene

- [x] Concrete username, absolute path, UUID, internal runtime ID and credential findings are zero.
- [x] No private logs, screenshots, conversations, raw EDA projects or machine state are included.
- [x] No PDF, EDA extension, executable, unexplained archive or file over 1 MiB is included in the repository.
- [x] Temporary output and Python bytecode caches were removed before manifest generation.
- [x] Allow-listed long hexadecimal values are only documented SHA-256 file digests.
- [x] Public file list, excluded-file list, privacy scan and test report are present.

## Evaluation evidence

- [x] `synthetic-safe` fixture and expected result are present.
- [x] `power-distribution-before` fixture has one intended decoupling blocker.
- [x] `power-distribution-after` successor closes the blocker in offline replay.
- [x] `car-controller-adversarial` reproduces the scoped engineering risk benchmark.
- [x] All evals include input, expected result, current manifest, manifest template, status and README.
- [x] External M2 live evidence was checked read-only and was not promoted because it still recorded zero live EDA calls.

## Integrity and local packaging

- [x] `FILE-MANIFEST.json` and `SHA256SUMS.txt` are generated from repository-relative files.
- [x] Local Git repository initialized and initial candidate commit created.
- [x] Git working tree was clean after the final integrity update and archive verification.
- [x] Local ZIP created from the committed tree without `.git/`.
- [x] ZIP inventoried and matched byte-for-byte to the committed file set.
- [x] ZIP SHA-256 sidecar generated outside the repository tree.

## Network publication

- [x] No GitHub push, release, upload or network publication was performed during preparation.
- [ ] **Maintainer, after ownership sign-off:** choose public repository owner/name and review the local ZIP.
- [ ] **Maintainer, after ownership sign-off:** create the public GitHub repository and publish the reviewed commit/archive.

Unchecked human/publication items do not block this **local review candidate**. They intentionally block a public tag or upload.
