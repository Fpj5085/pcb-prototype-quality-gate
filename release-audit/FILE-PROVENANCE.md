# Per-file provenance audit

This inventory classifies every file in the public candidate as observed during the local source and license audit. It uses repository-relative paths and records source class rather than workstation history. "Project-authored" means prepared within this project; it is not a finding about human copyrightability or AI-assistance. A privacy scan or absence of an upstream header does not prove copyright ownership.

## Class legend

- **A-private-adapted / C-private-copied** - project implementation brought from a private working tree; publication requires a chain-of-title and Apache-2.0 relicensing attestation.
- **R-*** - public expression rewritten from project concepts/private material or adapted from an identified public template; follow the row-specific ownership and attribution treatment.
- **O-*** - project-authored public code, documentation, configuration, or governance material.
- **S-*** - project-authored synthetic data or template.
- **D-sanitized-derived** - derived from a private fixture and stripped of live identity; sanitization is not an ownership determination.
- **F-factual-profile** - project arrangement of factual manufacturer evidence and links.
- **G-*** - generated integrity, audit, status, or expected-result material; regenerate when its inputs change.
- **T-standard-text** - third-party standard legal text retained verbatim.

## File inventory

| Path | Class | Source basis | Publication treatment |
| --- | --- | --- | --- |
| `.codex-plugin/plugin.json` | R-public-rewrite | Project-authored portable plugin metadata based on project concepts | Codex layout/names are interoperability only; no host schema/validator bundled |
| `.gitattributes` | O-repo-metadata | Project-authored repository configuration/version metadata | No third-party code or data |
| `.gitignore` | O-repo-metadata | Project-authored repository configuration/version metadata | No third-party code or data |
| `CHANGELOG.md` | O-governance-doc | Project-authored release history whose layout is inspired by Keep a Changelog | Source link retained; no template prose or implementation bundled; SemVer is reference-only |
| `CONTRIBUTING.md` | O-governance-doc | Project-authored release/governance documentation | Referenced tools/conventions are not bundled; verify generated facts after changes |
| `docs/architecture.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `docs/demo.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `docs/evidence-schema.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `docs/limitations.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `docs/m2-evidence-gate.md` | O-public-doc | Project-authored public documentation for the deterministic sanitized-evidence gate | Explains synthetic fixtures and pending/live boundary; no raw M2 evidence copied |
| `docs/privacy.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `docs/reproducible-release.md` | O-public-doc | Project-authored deterministic local release and verification instructions | Git, ZIP, SHA-256, and Python names are functional references; no tool code copied |
| `docs/resume.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `docs/review-model.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `docs/roadmap.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `docs/supported-repairs.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `evals/car-controller-adversarial/evidence/README.md` | O-public-doc | Project-authored public explanation for sanitized offline replay | No raw project, screenshot, log or vendor document |
| `evals/car-controller-adversarial/evidence/status.json` | G-status | Project-authored status/manifest for sanitized offline replay | States live evidence is not bundled |
| `evals/car-controller-adversarial/expected.json` | G-sanitized-result | Project-generated expected result for the sanitized-derived input | Fixture-scoped benchmark only; regenerate with reviewed engine changes |
| `evals/car-controller-adversarial/input.json` | D-sanitized-derived | Normalized adversarial input derived from a private fixture and stripped of live identity | Ownership attestation required; MPN/package strings are factual interoperability data |
| `evals/car-controller-adversarial/manifest.json` | G-status | Project-authored status/manifest for sanitized offline replay | States live evidence is not bundled |
| `evals/car-controller-adversarial/manifest.template.json` | S-template | Project-authored placeholder manifest | Placeholders only; no concrete live identifiers |
| `evals/car-controller-adversarial/README.md` | O-public-doc | Project-authored public explanation for sanitized offline replay | No raw project, screenshot, log or vendor document |
| `evals/power-distribution-after/evidence/README.md` | O-public-doc | Project-authored explanation of the synthetic M2 fixture | No live result or third-party asset |
| `evals/power-distribution-after/evidence/status.json` | G-status | Project-authored fixture status linked to the separate gate-generated live summary | No real M2 project identity or raw evidence; does not relabel fixture bytes as live |
| `evals/power-distribution-after/expected.json` | G-synthetic-result | Project-generated expected result for a synthetic BEFORE/AFTER input | Offline forecast only; separate live conclusion is carried by the minimal summary |
| `evals/power-distribution-after/input.json` | S-synthetic | Project-authored synthetic M2 AFTER fixture | No real M2 project identity or raw evidence; zero EDA writes in this fixture |
| `evals/power-distribution-after/manifest.json` | G-status | Project-authored offline-fixture manifest linked to the separate gate-generated live summary | Preserves synthetic fixture provenance while recording the reviewed summary relationship |
| `evals/power-distribution-after/manifest.template.json` | S-template | Project-authored placeholder manifest | Placeholders only; no concrete live identifiers |
| `evals/power-distribution-after/README.md` | O-public-doc | Project-authored explanation of the synthetic M2 fixture | No live result or third-party asset |
| `evals/power-distribution-before/evidence/README.md` | O-public-doc | Project-authored explanation of the synthetic M2 fixture | No live result or third-party asset |
| `evals/power-distribution-before/evidence/status.json` | G-status | Project-authored fixture status linked to the separate gate-generated live summary | No real M2 project identity or raw evidence; does not relabel fixture bytes as live |
| `evals/power-distribution-before/expected.json` | G-synthetic-result | Project-generated expected result for a synthetic BEFORE/AFTER input | Offline baseline result only; separate live conclusion is carried by the minimal summary |
| `evals/power-distribution-before/input.json` | S-synthetic | Project-authored synthetic M2 BEFORE fixture | No real M2 project identity or raw evidence; zero EDA writes in this fixture |
| `evals/power-distribution-before/manifest.json` | G-status | Project-authored offline-fixture manifest linked to the separate gate-generated live summary | Preserves synthetic fixture provenance while recording the reviewed summary relationship |
| `evals/power-distribution-before/manifest.template.json` | S-template | Project-authored placeholder manifest | Placeholders only; no concrete live identifiers |
| `evals/power-distribution-before/README.md` | O-public-doc | Project-authored explanation of the synthetic M2 fixture | No live result or third-party asset |
| `evals/synthetic-safe/evidence/README.md` | O-public-doc | Project-authored explanation of the synthetic control | No third-party asset |
| `evals/synthetic-safe/evidence/status.json` | S-synthetic | Project-authored generic synthetic control data or status | No product identity, vendor library record or physical claim |
| `evals/synthetic-safe/expected.json` | G-synthetic-result | Project-generated expected result for the synthetic safe input | Unit/eval evidence only; no live EDA claim |
| `evals/synthetic-safe/input.json` | S-synthetic | Project-authored generic synthetic control data or status | No product identity, vendor library record or physical claim |
| `evals/synthetic-safe/manifest.json` | S-synthetic | Project-authored generic synthetic control data or status | No product identity, vendor library record or physical claim |
| `evals/synthetic-safe/manifest.template.json` | S-template | Project-authored placeholder manifest | Placeholders only; no concrete live identifiers |
| `evals/synthetic-safe/README.md` | O-public-doc | Project-authored explanation of the synthetic control | No third-party asset |
| `examples/expected-output.zh-CN.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `examples/ordinary-language-requests.zh-CN.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `examples/README.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `EXCLUDED-FILES.md` | O-governance-doc | Project-authored release/governance documentation | Referenced tools/conventions are not bundled; verify generated facts after changes |
| `FILE-MANIFEST.json` | G-integrity | Deterministically generated from repository-relative file bytes | Regenerate after any change; SHA values are integrity data |
| `INSTALL.md` | O-governance-doc | Project-authored release/governance documentation | Referenced tools/conventions are not bundled; verify generated facts after changes |
| `LICENSE` | T-standard-text | Apache License 2.0 standard legal text; not project-authored | Keep verbatim; compare with official Apache source before release |
| `LICENSE-DECISION.md` | O-legal-audit | Project-authored license/attribution decision record | Final copyright holder and relicensing rights require human approval |
| `NOTICE` | O-legal-audit | Project-authored license/attribution decision record | Final copyright holder and relicensing rights require human approval |
| `PRIVACY-SCAN.md` | G-audit | Locally generated release-validation summary | Regenerate or update after final tests/scans; no external report copied |
| `PUBLIC-FILES.md` | O-governance-doc | Project-authored release/governance documentation | Referenced tools/conventions are not bundled; verify generated facts after changes |
| `README.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `README.zh-CN.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `release-audit/DOCS-REVIEW.md` | G-audit | Locally authored release audit record | No third-party report or private raw evidence copied |
| `release-audit/FILE-PROVENANCE.md` | G-audit | Generated per-file provenance inventory plus release analysis | Regenerate/extend when public file set changes |
| `release-audit/M2-INTEGRATION-STATUS.md` | G-status | Locally authored M2 integration status summary | Records the sanitized gate outcome without copying raw M2 evidence or private identity |
| `release-audit/m2-live-evidence-summary.json` | G-sanitized-summary | Deterministically generated by the reviewed M2 evidence-import gate from a separately reviewed sanitized bundle | Minimal aggregate proof only; no raw receipt, workstation path, private identifier, approval value or primitive identity |
| `release-audit/PRIVACY-SCAN-ALLOWLIST.json` | O-audit-config | Project-authored narrow allowlist for release scanning | Pattern vocabulary only; concrete secrets/IDs remain prohibited |
| `release-audit/SOURCE-BOUNDARY.md` | O-audit | Project-authored source-boundary audit from staged evidence | Chain of title still requires maintainer attestation |
| `release-audit/SOURCE-INVENTORY.md` | O-audit | Project-authored source-boundary audit from staged evidence | Chain of title still requires maintainer attestation |
| `RELEASE-CHECKLIST.md` | O-governance-doc | Project-authored release/governance documentation | Referenced tools/conventions are not bundled; verify generated facts after changes |
| `schemas/change-preview.schema.json` | C-private-copied | Project schema copied from the private working tree | No upstream marker found; explicit Apache-2.0 relicensing attestation required |
| `schemas/change-set.schema.json` | C-private-copied | Project schema copied from the private working tree | No upstream marker found; explicit Apache-2.0 relicensing attestation required |
| `schemas/circuit-dsl.schema.json` | C-private-copied | Project schema copied from the private working tree | No upstream marker found; explicit Apache-2.0 relicensing attestation required |
| `schemas/component-lockfile.schema.json` | C-private-copied | Project schema copied from the private working tree | No upstream marker found; explicit Apache-2.0 relicensing attestation required |
| `schemas/component-profiles.schema.json` | O-public-schema | Project-authored runtime schema created for the release candidate | Apache-2.0 after ownership attestation; JSON Schema vocabulary is reference-only |
| `schemas/firmware-pin-manifest.schema.json` | C-private-copied | Project schema copied from the private working tree | No upstream marker found; explicit Apache-2.0 relicensing attestation required |
| `schemas/hardware-contract.schema.json` | C-private-copied | Project schema copied from the private working tree | No upstream marker found; explicit Apache-2.0 relicensing attestation required |
| `schemas/m2-evidence-sha-manifest.schema.json` | O-public-schema | Project-authored evidence-gate schema created for this candidate | Apache-2.0 after ownership attestation; JSON Schema vocabulary is reference-only |
| `schemas/m2-live-evidence-bundle.schema.json` | O-public-schema | Project-authored evidence-gate schema created for this candidate | Apache-2.0 after ownership attestation; JSON Schema vocabulary is reference-only |
| `schemas/m2-live-evidence-document.schema.json` | O-public-schema | Project-authored evidence-gate schema created for this candidate | Apache-2.0 after ownership attestation; JSON Schema vocabulary is reference-only |
| `schemas/m2-public-evidence-summary.schema.json` | O-public-schema | Project-authored minimal-public-summary schema created for this candidate | Apache-2.0 after ownership attestation; contains no vendor API schema |
| `schemas/pin-consistency-report.schema.json` | C-private-copied | Project schema copied from the private working tree | No upstream marker found; explicit Apache-2.0 relicensing attestation required |
| `schemas/project-snapshot.schema.json` | C-private-copied | Project schema copied from the private working tree | No upstream marker found; explicit Apache-2.0 relicensing attestation required |
| `schemas/prototype-review-input.schema.json` | O-public-schema | Project-authored runtime schema created for the release candidate | Apache-2.0 after ownership attestation; JSON Schema vocabulary is reference-only |
| `schemas/prototype-review-output.schema.json` | O-public-schema | Project-authored runtime schema created for the release candidate | Apache-2.0 after ownership attestation; JSON Schema vocabulary is reference-only |
| `schemas/README.md` | O-public-doc | Project-authored public explanation of project schemas | JSON Schema name/meta-schema URI are reference-only |
| `scripts/build-release.py` | O-public-code | Project-authored deterministic local archive builder created for this candidate | Apache-2.0 after ownership attestation; Git and Python are user-provided |
| `scripts/import_m2_evidence.py` | O-public-code | Project-authored deterministic M2 sanitized-evidence import gate | Apache-2.0 after ownership attestation; copies only a minimal summary |
| `scripts/prototype-review.ps1` | O-public-code | Thin project-authored release wrapper for repository-relative offline use | Apache-2.0 after ownership attestation; PowerShell is user-provided |
| `scripts/release-verify.py` | O-public-code | Project-authored repository/privacy/integrity verifier created for this candidate | Apache-2.0 after ownership attestation; standard library only |
| `scripts/run-evals.py` | O-public-code | Project-authored deterministic eval runner created for the release candidate | Apache-2.0 after ownership attestation; Python is user-provided |
| `scripts/update-integrity.py` | O-public-code | Project-authored deterministic manifest/checksum generator created for this candidate | Apache-2.0 after ownership attestation; standard library only |
| `SECURITY.md` | O-governance-doc | Project-authored release/governance documentation | Referenced tools/conventions are not bundled; verify generated facts after changes |
| `SHA256SUMS.txt` | G-integrity | Deterministically generated from repository-relative file bytes | Regenerate after any change; SHA values are integrity data |
| `skills/jlceda-hardware-design/agents/openai.yaml` | R-public-rewrite | Public rewrite of project governance skill or host metadata | Private wrappers/runtime bindings excluded; host names are interoperability only |
| `skills/jlceda-hardware-design/references/review-evidence.md` | R-public-rewrite | Public rewrite of project governance skill or host metadata | Private wrappers/runtime bindings excluded; host names are interoperability only |
| `skills/jlceda-hardware-design/references/safety-and-privacy.md` | R-public-rewrite | Public rewrite of project governance skill or host metadata | Private wrappers/runtime bindings excluded; host names are interoperability only |
| `skills/jlceda-hardware-design/references/supported-repair-policy.md` | R-public-rewrite | Public rewrite of project governance skill or host metadata | Private wrappers/runtime bindings excluded; host names are interoperability only |
| `skills/jlceda-hardware-design/references/work-modes.md` | R-public-rewrite | Public rewrite of project governance skill or host metadata | Private wrappers/runtime bindings excluded; host names are interoperability only |
| `skills/jlceda-hardware-design/SKILL.md` | R-public-rewrite | Public rewrite of project governance skill or host metadata | Private wrappers/runtime bindings excluded; host names are interoperability only |
| `src/review/component-profiles.json` | F-factual-profile | Project-authored profile structure and thresholds with manufacturer factual citations | Official links, names, MPNs and numeric facts only; no PDF/table/figure |
| `src/review/prototype_review.py` | A-private-adapted | Project review engine adapted and portabilized from a private working tree | Apache-2.0 only after authorship/relicensing attestation; standard library only |
| `TEST-REPORT.md` | G-audit | Locally generated release-validation summary | Regenerate or update after final tests/scans; no external report copied |
| `tests/__init__.py` | A-private-adapted | Project tests adapted for portable repository-relative execution | Apache-2.0 only after ownership attestation; standard library only |
| `tests/m2_gate/__init__.py` | O-public-test | Project-authored test-package marker | Apache-2.0 after ownership attestation |
| `tests/m2_gate/fixtures/complete/bundle.json` | S-synthetic-gate | Project-authored synthetic complete-bundle index | Gate-positive semantics only; no real receipt, ID, path, or EDA evidence |
| `tests/m2_gate/fixtures/complete/evidence/after/drc.json` | S-synthetic-gate | Project-authored synthetic AFTER DRC evidence document | Gate-positive semantics only; not an observed EDA result |
| `tests/m2_gate/fixtures/complete/evidence/after/independent-readback.json` | S-synthetic-gate | Project-authored synthetic AFTER readback evidence document | Gate-positive semantics only; not an observed EDA result |
| `tests/m2_gate/fixtures/complete/evidence/after/prototype-review.json` | S-synthetic-gate | Project-authored synthetic AFTER Prototype-review evidence document | Gate-positive semantics only; not an observed M2 result |
| `tests/m2_gate/fixtures/complete/evidence/after/receipt.json` | S-synthetic-gate | Project-authored synthetic AFTER receipt evidence document | Contains no real receipt identifier; not an observed delivery |
| `tests/m2_gate/fixtures/complete/evidence/after/save-reload.json` | S-synthetic-gate | Project-authored synthetic AFTER save/reload evidence document | Gate-positive semantics only; not an observed EDA result |
| `tests/m2_gate/fixtures/complete/evidence/before/drc.json` | S-synthetic-gate | Project-authored synthetic BEFORE DRC evidence document | Gate-positive semantics only; not an observed EDA result |
| `tests/m2_gate/fixtures/complete/evidence/before/independent-readback.json` | S-synthetic-gate | Project-authored synthetic BEFORE readback evidence document | Gate-positive semantics only; not an observed EDA result |
| `tests/m2_gate/fixtures/complete/evidence/before/prototype-review.json` | S-synthetic-gate | Project-authored synthetic BEFORE Prototype-review evidence document | Gate-positive semantics only; not an observed M2 result |
| `tests/m2_gate/fixtures/complete/evidence/before/receipt.json` | S-synthetic-gate | Project-authored synthetic BEFORE receipt evidence document | Contains no real receipt identifier; not an observed baseline capture |
| `tests/m2_gate/fixtures/complete/evidence/before/save-reload.json` | S-synthetic-gate | Project-authored synthetic BEFORE save/reload evidence document | Gate-positive semantics only; not an observed EDA result |
| `tests/m2_gate/fixtures/README.md` | O-public-doc | Project-authored declaration that all enclosed positive evidence is synthetic gate data | Retain next to fixtures; positive live flags are not live M2 proof |
| `tests/m2_gate/test_import_m2_evidence.py` | O-public-test | Project-authored evidence-gate tests and synthetic mutation cases | Apache-2.0 after ownership attestation; standard library only |
| `tests/release/__init__.py` | O-public-test | Project-authored test-package marker | Apache-2.0 after ownership attestation |
| `tests/release/test_release_tools.py` | O-public-test | Project-authored deterministic release-tooling tests | Apache-2.0 after ownership attestation; examples use reserved synthetic values |
| `tests/review/__init__.py` | A-private-adapted | Project tests adapted for portable repository-relative execution | Apache-2.0 only after ownership attestation; standard library only |
| `tests/review/fixtures/car-adversarial-input.json` | D-sanitized-derived | Byte-identical test copy of the sanitized-derived car adversarial input | Privacy removal does not settle ownership; no live IDs/raw project |
| `tests/review/fixtures/synthetic-safe-input.json` | S-synthetic | Byte-identical test copy of the project-authored synthetic safe input | Original synthetic data; no physical/live claim |
| `tests/review/test_prototype_review.py` | A-private-adapted | Project tests adapted for portable repository-relative execution | Apache-2.0 only after ownership attestation; standard library only |
| `tests/review/test_release_runtime.py` | A-private-adapted | Project tests adapted for portable repository-relative execution | Apache-2.0 only after ownership attestation; standard library only |
| `THIRD_PARTY.md` | O-legal-audit | Project-authored license/attribution decision record | Final copyright holder and relicensing rights require human approval |
| `VERSION` | O-repo-metadata | Project-authored repository configuration/version metadata | No third-party code or data |

## Audit conclusions

- No staged implementation file carries a third-party copyright header or upstream license marker. This negative text finding does not establish authorship.
- The executable Python code imports only the standard library; the PowerShell entry is a project wrapper. No third-party runtime, source tree, package, binary, or NOTICE file is bundled.
- Third-party platform names, public format/specification names, manufacturer names, MPNs, package strings, short document titles, URLs, and numeric facts are used for identification, interoperability, or evidence citation. They are not declared project trademarks or relicensed assets.
- `LICENSE` is standard Apache License 2.0 legal text. All other files are proposed for Apache-2.0 only after the maintainer completes the ownership gate in `LICENSE-DECISION.md`.
- The sanitized car fixture and all private-working-tree-derived code, schemas, tests, and rewrites require explicit confirmation that no employer, client, contractor, or prior-repository rights conflict exists.
- The release owner must identify AI-assisted material, confirm publication rights under the applicable tool terms, and approve the final authorship/copyright representation.

## Maintenance rule

Every newly public file must receive one row before packaging. Any source, prose, table, figure, schema, binary, fixture, or dataset copied from an external source must identify that source, exact license, modification status, and required notice; otherwise it remains excluded. Generated rows must be regenerated after their inputs change.
