# Per-file provenance audit

This inventory classifies every file in the public candidate. "Project-authored" describes provenance within this project and is not a copyrightability determination.

## Class legend

- **A/R/O/S/D/F/G/T** retain the source-boundary meanings used by the v0.1.0 audit.
- **G-sanitized-result** is generated only from privacy-minimized evidence accepted by a deterministic gate.

## File inventory

| Path | Class | Source basis | Publication treatment |
| --- | --- | --- | --- |
| `.codex-plugin/plugin.json` | R-public-rewrite | Project-authored portable plugin metadata based on project concepts | Codex layout/names are interoperability only; no host schema/validator bundled |
| `.gitattributes` | O-repo-metadata | Project-authored repository configuration/version metadata | No third-party code or data |
| `.gitignore` | O-repo-metadata | Project-authored repository configuration/version metadata | No third-party code or data |
| `CHANGELOG.md` | O-governance-doc | Project-authored release history whose layout is inspired by Keep a Changelog | Source link retained; no template prose or implementation bundled; SemVer is reference-only |
| `CONTRIBUTING.md` | O-governance-doc | Project-authored release/governance documentation | Referenced tools/conventions are not bundled; verify generated facts after changes |
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
| `RELEASE-CHECKLIST.md` | O-governance-doc | Project-authored release/governance documentation | Referenced tools/conventions are not bundled; verify generated facts after changes |
| `SECURITY.md` | O-governance-doc | Project-authored release/governance documentation | Referenced tools/conventions are not bundled; verify generated facts after changes |
| `SHA256SUMS.txt` | G-integrity | Deterministically generated from repository-relative file bytes | Regenerate after any change; SHA values are integrity data |
| `TEST-REPORT.md` | G-audit | Locally generated release-validation summary | Regenerate or update after final tests/scans; no external report copied |
| `THIRD_PARTY.md` | O-legal-audit | Project-authored license/attribution decision record | Final copyright holder and relicensing rights require human approval |
| `VERSION` | O-repo-metadata | Project-authored repository configuration/version metadata | No third-party code or data |
| `docs/architecture.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `docs/demo.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `docs/evidence-schema.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `docs/limitations.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `docs/m2-evidence-gate.md` | O-public-doc | Project-authored public documentation for the deterministic sanitized-evidence gate | Explains synthetic fixtures and pending/live boundary; no raw M2 evidence copied |
| `docs/privacy.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `docs/pipeline.md` | O-public-doc | Project-authored adapter-neutral review pipeline documentation | No live EDA adapter or mutation runtime bundled |
| `scripts/run-review-pipeline.py` | O-project-code | Project-authored adapter-neutral orchestration entry that reuses the review and bounded-plan modules | Never connects to EDA or executes mutation |
| `scripts/build-readonly-adapter-envelope.py` | O-project-code | Project-authored offline assembler for explicit sanitized read-only capture facts | Derives only the normalized-design digest; never discovers EDA state or emits partial evidence |
| `scripts/validate-readonly-adapter-health.py` | O-project-code | Project-authored offline validator for external read-only adapter health receipts | Never performs network requests or accesses EDA |
| `src/review/readonly_adapter_export.py` | O-project-code | Project-authored fail-closed envelope assembly and contract reuse | Accepts explicit capture facts only; no Gateway/Bridge access |
| `src/review/readonly_adapter_health.py` | O-project-code | Project-authored fail-closed health receipt validator and safe summary | Classifies transport/session/protocol facts without contacting the environment |
| `src/spec/contract_to_review.py` | O-project-code | Project-authored offline fail-closed hardware-contract-to-prototype-review-input converter | Apache-2.0 after ownership attestation; standard library only; performs no EDA access, never guesses missing facts and re-validates its output with the review engine's own validator |
| `src/spec/requirements_gate.py` | O-project-code | Project-authored offline fail-closed requirements-to-hardware-contract gate | Apache-2.0 after ownership attestation; standard library only; performs no EDA access and never guesses missing facts |
| `tests/review/test_review_pipeline.py` | O-project-test | Project-authored regression coverage for the offline orchestration entry | Verifies zero EDA access and zero writes |
| `tests/review/test_closed_loop_demo.py` | O-project-test | Project-authored end-to-end regression coverage for the one-command closed-loop demo | Subprocess replay in an archived workspace; asserts the auto-converted fail-closed `PERSISTENCE` blocker plus three data-completeness advisories and the preserved `--design` prefab path; zero EDA access |
| `tests/spec/__init__.py` | O-public-test | Project-authored test-package marker | Apache-2.0 after ownership attestation |
| `tests/spec/test_contract_to_review.py` | O-public-test | Project-authored adversarial coverage for the offline hardware-contract-to-review-input converter | Apache-2.0 after ownership attestation; synthetic inputs only; re-validates converter output with the review engine and never guesses |
| `tests/spec/test_requirements_gate.py` | O-public-test | Project-authored adversarial coverage for the offline fail-closed requirements gate | Apache-2.0 after ownership attestation; synthetic inputs only; no EDA access |
| `tests/review/test_readonly_adapter_export.py` | O-project-test | Project-authored regression coverage for complete and failed envelope assembly | Verifies digest derivation, partial-state rejection and allow-listed failures |
| `tests/review/test_readonly_adapter_health.py` | O-project-test | Project-authored health gate regression coverage | Covers 502, diagnostic-only mode, target ambiguity and write-signal rejection |
| `docs/reproducible-release.md` | O-public-doc | Project-authored deterministic local release and verification instructions | Git, ZIP, SHA-256, and Python names are functional references; no tool code copied |
| `docs/resume.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `docs/review-model.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `docs/roadmap.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `docs/supported-repairs.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `evals/car-controller-adversarial/README.md` | O-public-doc | Project-authored public explanation for sanitized offline replay | No raw project, screenshot, log or vendor document |
| `evals/car-controller-adversarial/evidence/README.md` | O-public-doc | Project-authored public explanation for sanitized offline replay | No raw project, screenshot, log or vendor document |
| `evals/car-controller-adversarial/evidence/status.json` | G-status | Project-authored status/manifest for sanitized offline replay | States live evidence is not bundled |
| `evals/car-controller-adversarial/expected.json` | G-sanitized-result | Project-generated expected result for the sanitized-derived input | Fixture-scoped benchmark only; regenerate with reviewed engine changes |
| `evals/car-controller-adversarial/input.json` | D-sanitized-derived | Normalized adversarial input derived from a private fixture and stripped of live identity | Ownership attestation required; MPN/package strings are factual interoperability data |
| `evals/car-controller-adversarial/manifest.json` | G-status | Project-authored status/manifest for sanitized offline replay | States live evidence is not bundled |
| `evals/car-controller-adversarial/manifest.template.json` | S-template | Project-authored placeholder manifest | Placeholders only; no concrete live identifiers |
| `evals/communication-interface-after/expected.json` | G-synthetic-result | Project-authored expected output for an original synthetic communication benchmark | Offline fixture-only forecast; no live or general accuracy claim |
| `evals/communication-interface-after/input.json` | S-synthetic | Original synthetic communication-interface AFTER benchmark | Zero EDA writes; no real identifiers, vendor assets or manufacturing claim |
| `evals/communication-interface-after/manifest.json` | S-synthetic | Project-authored zero-write execution and privacy declaration | Offline benchmark scope only |
| `evals/communication-interface-before/expected.json` | G-synthetic-result | Project-authored expected output for an original synthetic communication benchmark | Fixture-scoped seeded-risk assertion only |
| `evals/communication-interface-before/input.json` | S-synthetic | Original synthetic communication-interface BEFORE benchmark | Zero EDA writes; no real identifiers, vendor assets or manufacturing claim |
| `evals/communication-interface-before/manifest.json` | S-synthetic | Project-authored zero-write execution and privacy declaration | Offline benchmark scope only |
| `evals/power-input-after/expected.json` | G-synthetic-result | Project-authored expected output for an original synthetic power benchmark | Offline fixture-only forecast; no live or general accuracy claim |
| `evals/power-input-after/input.json` | S-synthetic | Original synthetic power-input AFTER benchmark | Zero EDA writes; no real identifiers, vendor assets or manufacturing claim |
| `evals/power-input-after/manifest.json` | S-synthetic | Project-authored zero-write execution and privacy declaration | Offline benchmark scope only |
| `evals/power-input-before/expected.json` | G-synthetic-result | Project-authored expected output for an original synthetic power benchmark | Fixture-scoped seeded-risk assertion only |
| `evals/power-input-before/input.json` | S-synthetic | Original synthetic power-input BEFORE benchmark | Zero EDA writes; no real identifiers, vendor assets or manufacturing claim |
| `evals/power-input-before/manifest.json` | S-synthetic | Project-authored zero-write execution and privacy declaration | Offline benchmark scope only |
| `evals/power-distribution-after/README.md` | O-public-doc | Project-authored explanation of the synthetic M2 fixture | No live result or third-party asset |
| `evals/power-distribution-after/evidence/README.md` | O-public-doc | Project-authored explanation of the synthetic M2 fixture | No live result or third-party asset |
| `evals/power-distribution-after/evidence/status.json` | G-status | Project-authored fixture status linked to the separate gate-generated live summary | No real M2 project identity or raw evidence; does not relabel fixture bytes as live |
| `evals/power-distribution-after/expected.json` | G-synthetic-result | Project-generated expected result for a synthetic BEFORE/AFTER input | Offline forecast only; separate live conclusion is carried by the minimal summary |
| `evals/power-distribution-after/input.json` | S-synthetic | Project-authored synthetic M2 AFTER fixture | No real M2 project identity or raw evidence; zero EDA writes in this fixture |
| `evals/power-distribution-after/manifest.json` | G-status | Project-authored offline-fixture manifest linked to the separate gate-generated live summary | Preserves synthetic fixture provenance while recording the reviewed summary relationship |
| `evals/power-distribution-after/manifest.template.json` | S-template | Project-authored placeholder manifest | Placeholders only; no concrete live identifiers |
| `evals/power-distribution-before/README.md` | O-public-doc | Project-authored explanation of the synthetic M2 fixture | No live result or third-party asset |
| `evals/power-distribution-before/evidence/README.md` | O-public-doc | Project-authored explanation of the synthetic M2 fixture | No live result or third-party asset |
| `evals/power-distribution-before/evidence/status.json` | G-status | Project-authored fixture status linked to the separate gate-generated live summary | No real M2 project identity or raw evidence; does not relabel fixture bytes as live |
| `evals/power-distribution-before/expected.json` | G-synthetic-result | Project-generated expected result for a synthetic BEFORE/AFTER input | Offline baseline result only; separate live conclusion is carried by the minimal summary |
| `evals/power-distribution-before/input.json` | S-synthetic | Project-authored synthetic M2 BEFORE fixture | No real M2 project identity or raw evidence; zero EDA writes in this fixture |
| `evals/power-distribution-before/manifest.json` | G-status | Project-authored offline-fixture manifest linked to the separate gate-generated live summary | Preserves synthetic fixture provenance while recording the reviewed summary relationship |
| `evals/power-distribution-before/manifest.template.json` | S-template | Project-authored placeholder manifest | Placeholders only; no concrete live identifiers |
| `evals/sensor-interface-after/expected.json` | G-synthetic-result | Project-authored expected output for an original synthetic sensor benchmark | Offline fixture-only forecast; no live or general accuracy claim |
| `evals/sensor-interface-after/input.json` | S-synthetic | Original synthetic sensor-interface AFTER benchmark | Zero EDA writes; no real identifiers, vendor assets or manufacturing claim |
| `evals/sensor-interface-after/manifest.json` | S-synthetic | Project-authored zero-write execution and privacy declaration | Offline benchmark scope only |
| `evals/sensor-interface-before/expected.json` | G-synthetic-result | Project-authored expected output for an original synthetic sensor benchmark | Fixture-scoped seeded-risk assertion only |
| `evals/sensor-interface-before/input.json` | S-synthetic | Original synthetic sensor-interface BEFORE benchmark | Zero EDA writes; no real identifiers, vendor assets or manufacturing claim |
| `evals/sensor-interface-before/manifest.json` | S-synthetic | Project-authored zero-write execution and privacy declaration | Offline benchmark scope only |
| `evals/synthetic-safe/README.md` | O-public-doc | Project-authored explanation of the synthetic control | No third-party asset |
| `evals/synthetic-safe/evidence/README.md` | O-public-doc | Project-authored explanation of the synthetic control | No third-party asset |
| `evals/synthetic-safe/evidence/status.json` | S-synthetic | Project-authored generic synthetic control data or status | No product identity, vendor library record or physical claim |
| `evals/synthetic-safe/expected.json` | G-synthetic-result | Project-generated expected result for the synthetic safe input | Unit/eval evidence only; no live EDA claim |
| `evals/synthetic-safe/input.json` | S-synthetic | Project-authored generic synthetic control data or status | No product identity, vendor library record or physical claim |
| `evals/synthetic-safe/manifest.json` | S-synthetic | Project-authored generic synthetic control data or status | No product identity, vendor library record or physical claim |
| `evals/synthetic-safe/manifest.template.json` | S-template | Project-authored placeholder manifest | Placeholders only; no concrete live identifiers |
| `evidence/m3-independent-repetition/README.md` | O-public-doc | Project-authored public explanation of a privacy-minimized live repetition summary | No raw project identity, receipts, screenshots or adapter implementation |
| `evidence/m3-independent-repetition/m2-live-evidence-summary.json` | G-sanitized-result | Deterministic gate-generated minimum summary from explicitly sanitized M3 evidence | Legacy filename retained for gate compatibility; case field identifies M3; no private identifiers |
| `examples/README.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `examples/expected-output.zh-CN.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `examples/m2-closed-loop/CLOSED-LOOP-DEMO.zh.md` | O-public-doc | Project-authored public documentation for the M2 closed-loop demo | Claims are evidence-scoped; real EDA loop described, not replayed |
| `examples/m2-closed-loop/design-data.json` | S-synthetic | Project-authored synthetic/cleaned M2 review input | Synthetic coordinates/nets only; no private EDA identity or raw evidence |
| `examples/m2-closed-loop/requirements.zh.json` | S-synthetic | Project-authored cleaned Chinese requirements for the M2 case | Synthetic/example values only; missing facts are intentional gaps |
| `examples/ordinary-language-requests.zh-CN.md` | O-public-doc | Project-authored public-release documentation or example text | Third-party names/links are nominative/reference-only; claims remain evidence-scoped |
| `release-audit/DOCS-REVIEW.md` | G-audit | Locally authored release audit record | No third-party report or private raw evidence copied |
| `release-audit/FILE-PROVENANCE.md` | G-audit | Generated per-file provenance inventory plus release analysis | Regenerate/extend when public file set changes |
| `release-audit/M2-INTEGRATION-STATUS.md` | G-status | Locally authored M2 integration status summary | Records the sanitized gate outcome without copying raw M2 evidence or private identity |
| `release-audit/PRIVACY-SCAN-ALLOWLIST.json` | O-audit-config | Project-authored narrow allowlist for release scanning | Pattern vocabulary only; concrete secrets/IDs remain prohibited |
| `release-audit/SOURCE-BOUNDARY.md` | O-audit | Project-authored source-boundary audit from staged evidence | Chain of title still requires maintainer attestation |
| `release-audit/SOURCE-INVENTORY.md` | O-audit | Project-authored source-boundary audit from staged evidence | Chain of title still requires maintainer attestation |
| `release-audit/m2-live-evidence-summary.json` | G-sanitized-summary | Deterministically generated by the reviewed M2 evidence-import gate from a separately reviewed sanitized bundle | Minimal aggregate proof only; no raw receipt, workstation path, private identifier, approval value or primitive identity |
| `schemas/README.md` | O-public-doc | Project-authored public explanation of project schemas | JSON Schema name/meta-schema URI are reference-only |
| `schemas/change-preview.schema.json` | C-private-copied | Project schema copied from the private working tree | No upstream marker found; explicit Apache-2.0 relicensing attestation required |
| `schemas/change-set.schema.json` | C-private-copied | Project schema copied from the private working tree | No upstream marker found; explicit Apache-2.0 relicensing attestation required |
| `schemas/circuit-dsl.schema.json` | C-private-copied | Project schema copied from the private working tree | No upstream marker found; explicit Apache-2.0 relicensing attestation required |
| `schemas/component-lockfile.schema.json` | C-private-copied | Project schema copied from the private working tree | No upstream marker found; explicit Apache-2.0 relicensing attestation required |
| `schemas/component-profiles.schema.json` | O-public-schema | Project-authored runtime schema created for the release candidate | Apache-2.0 after ownership attestation; JSON Schema vocabulary is reference-only |
| `schemas/firmware-pin-manifest.schema.json` | C-private-copied | Project schema copied from the private working tree | No upstream marker found; explicit Apache-2.0 relicensing attestation required |
| `schemas/hardware-contract.schema.json` | C-private-copied | Project schema copied from the private working tree | No upstream marker found; explicit Apache-2.0 relicensing attestation required |
| `schemas/local-bypass-repair-plan.schema.json` | O-public-schema | Project-authored fail-closed repair-plan schema | Apache-2.0 after ownership attestation; contains no live project identity or vendor API schema |
| `schemas/m2-evidence-sha-manifest.schema.json` | O-public-schema | Project-authored evidence-gate schema created for this candidate | Apache-2.0 after ownership attestation; JSON Schema vocabulary is reference-only |
| `schemas/m2-live-evidence-bundle.schema.json` | O-public-schema | Project-authored evidence-gate schema created for this candidate | Apache-2.0 after ownership attestation; JSON Schema vocabulary is reference-only |
| `schemas/m2-live-evidence-document.schema.json` | O-public-schema | Project-authored evidence-gate schema created for this candidate | Apache-2.0 after ownership attestation; JSON Schema vocabulary is reference-only |
| `schemas/m2-public-evidence-summary.schema.json` | O-public-schema | Project-authored minimal-public-summary schema created for this candidate | Apache-2.0 after ownership attestation; contains no vendor API schema |
| `schemas/pin-consistency-report.schema.json` | C-private-copied | Project schema copied from the private working tree | No upstream marker found; explicit Apache-2.0 relicensing attestation required |
| `schemas/project-snapshot.schema.json` | C-private-copied | Project schema copied from the private working tree | No upstream marker found; explicit Apache-2.0 relicensing attestation required |
| `schemas/readonly-adapter-envelope.schema.json` | O-public-schema | Project-authored strict read-only adapter handoff schema | No live connector or mutation capability bundled |
| `schemas/readonly-adapter-health.schema.json` | O-public-schema | Project-authored strict health-probe receipt schema | Transport/session/protocol diagnostics only; no connector bundled |
| `schemas/prototype-review-input.schema.json` | O-public-schema | Project-authored runtime schema created for the release candidate | Apache-2.0 after ownership attestation; JSON Schema vocabulary is reference-only |
| `schemas/prototype-review-output.schema.json` | O-public-schema | Project-authored runtime schema created for the release candidate | Apache-2.0 after ownership attestation; JSON Schema vocabulary is reference-only |
| `schemas/requirements-input.schema.json` | O-public-schema | Project-authored fail-closed requirements-input schema created for this candidate | Apache-2.0 after ownership attestation; JSON Schema vocabulary is reference-only |
| `scripts/build-release.py` | O-public-code | Project-authored deterministic local archive builder created for this candidate | Apache-2.0 after ownership attestation; Git and Python are user-provided |
| `scripts/import_m2_evidence.py` | O-public-code | Project-authored deterministic M2 sanitized-evidence import gate | Apache-2.0 after ownership attestation; copies only a minimal summary |
| `scripts/plan-local-bypass.py` | O-public-code | Thin project-authored CLI for the deterministic local-bypass planner | Apache-2.0 after ownership attestation; standard library only and no live adapter |
| `scripts/prototype-review.ps1` | O-public-code | Thin project-authored release wrapper for repository-relative offline use | Apache-2.0 after ownership attestation; PowerShell is user-provided |
| `scripts/contract-to-review-cli.py` | O-public-code | Thin project-authored CLI for the offline hardware-contract-to-review-input converter | Apache-2.0 after ownership attestation; standard library only and no EDA access |
| `scripts/requirements-gate.py` | O-public-code | Thin project-authored CLI for the offline fail-closed requirements gate | Apache-2.0 after ownership attestation; standard library only and no EDA access |
| `scripts/release-verify.py` | O-public-code | Project-authored repository/privacy/integrity verifier created for this candidate | Apache-2.0 after ownership attestation; standard library only |
| `scripts/run-closed-loop-demo.py` | O-public-code | Thin project-authored offline demo CLI for the M2 closed-loop public example | Apache-2.0 after ownership attestation; standard library only, no EDA access and no automatic-repair claim |
| `scripts/run-evals.py` | O-public-code | Project-authored deterministic eval runner created for the release candidate | Apache-2.0 after ownership attestation; Python is user-provided |
| `scripts/update-integrity.py` | O-public-code | Project-authored deterministic manifest/checksum generator created for this candidate | Apache-2.0 after ownership attestation; standard library only |
| `skills/jlceda-hardware-design/SKILL.md` | R-public-rewrite | Public rewrite of project governance skill or host metadata | Private wrappers/runtime bindings excluded; host names are interoperability only |
| `skills/jlceda-hardware-design/agents/openai.yaml` | R-public-rewrite | Public rewrite of project governance skill or host metadata | Private wrappers/runtime bindings excluded; host names are interoperability only |
| `skills/jlceda-hardware-design/references/review-evidence.md` | R-public-rewrite | Public rewrite of project governance skill or host metadata | Private wrappers/runtime bindings excluded; host names are interoperability only |
| `skills/jlceda-hardware-design/references/safety-and-privacy.md` | R-public-rewrite | Public rewrite of project governance skill or host metadata | Private wrappers/runtime bindings excluded; host names are interoperability only |
| `skills/jlceda-hardware-design/references/supported-repair-policy.md` | R-public-rewrite | Public rewrite of project governance skill or host metadata | Private wrappers/runtime bindings excluded; host names are interoperability only |
| `skills/jlceda-hardware-design/references/work-modes.md` | R-public-rewrite | Public rewrite of project governance skill or host metadata | Private wrappers/runtime bindings excluded; host names are interoperability only |
| `src/repair/__init__.py` | O-public-code | Project-authored repair package marker | Apache-2.0 after ownership attestation |
| `src/repair/local_bypass_plan.py` | O-public-code | Project-authored fail-closed immutable repair planner | Apache-2.0 after ownership attestation; standard library only and no private integration binding |
| `src/review/component-profiles.json` | F-factual-profile | Project-authored profile structure and thresholds with manufacturer factual citations | Official links, names, MPNs and numeric facts only; no PDF/table/figure |
| `src/review/component_profile_audit.py` | O-public-code | Project-authored deterministic offline provenance and freshness auditor | Apache-2.0 after ownership attestation; standard library only; performs no network or EDA access |
| `src/review/prototype_review.py` | A-private-adapted | Project review engine adapted and portabilized from a private working tree | Apache-2.0 only after authorship/relicensing attestation; standard library only |
| `src/review/readonly_adapter_contract.py` | O-public-code | Project-authored fail-closed validator for sanitized read-only adapter evidence | Standard library only; validates files and never connects to EDA or writes designs |
| `tests/__init__.py` | A-private-adapted | Project tests adapted for portable repository-relative execution | Apache-2.0 only after ownership attestation; standard library only |
| `tests/m2_gate/__init__.py` | O-public-test | Project-authored test-package marker | Apache-2.0 after ownership attestation |
| `tests/m2_gate/fixtures/README.md` | O-public-doc | Project-authored declaration that all enclosed positive evidence is synthetic gate data | Retain next to fixtures; positive live flags are not live M2 proof |
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
| `tests/m2_gate/test_import_m2_evidence.py` | O-public-test | Project-authored evidence-gate tests and synthetic mutation cases | Apache-2.0 after ownership attestation; standard library only |
| `tests/release/__init__.py` | O-public-test | Project-authored test-package marker | Apache-2.0 after ownership attestation |
| `tests/release/test_release_tools.py` | O-public-test | Project-authored deterministic release-tooling tests | Apache-2.0 after ownership attestation; examples use reserved synthetic values |
| `tests/repair/__init__.py` | O-public-test | Project-authored test-package marker | Apache-2.0 after ownership attestation |
| `tests/repair/test_local_bypass_plan.py` | O-public-test | Project-authored adversarial tests for the local-bypass plan gate | Apache-2.0 after ownership attestation; synthetic inputs only |
| `tests/review/__init__.py` | A-private-adapted | Project tests adapted for portable repository-relative execution | Apache-2.0 only after ownership attestation; standard library only |
| `tests/review/fixtures/car-adversarial-input.json` | D-sanitized-derived | Byte-identical test copy of the sanitized-derived car adversarial input | Privacy removal does not settle ownership; no live IDs/raw project |
| `tests/review/fixtures/synthetic-safe-input.json` | S-synthetic | Byte-identical test copy of the project-authored synthetic safe input | Original synthetic data; no physical/live claim |
| `tests/review/test_component_profile_audit.py` | O-public-test | Project-authored adversarial coverage for deterministic provenance and freshness policy | Apache-2.0 after ownership attestation; synthetic metadata only; no network access |
| `tests/review/test_diverse_benchmarks.py` | O-public-test | Project-authored coverage for three original synthetic BEFORE/AFTER benchmark pairs | Apache-2.0 after ownership attestation; zero-write fixtures only |
| `tests/review/test_input_safety_boundaries.py` | O-public-test | Project-authored adversarial coverage for normalized-input numeric, confidence, range, container and assumption boundaries | Apache-2.0 after ownership attestation; synthetic inputs only; no EDA access |
| `tests/review/test_readonly_adapter_contract.py` | O-public-test | Project-authored adversarial coverage for read-only adapter target, digest, persistence and failure boundaries | Synthetic envelopes only; no EDA access or mutation |
| `tests/review/test_prototype_review.py` | A-private-adapted | Project tests adapted for portable repository-relative execution | Apache-2.0 only after ownership attestation; standard library only |
| `tests/review/test_release_runtime.py` | A-private-adapted | Project tests adapted for portable repository-relative execution | Apache-2.0 only after ownership attestation; standard library only |
