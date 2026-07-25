# Roadmap

The roadmap is evidence-gated. A feature moves from planned to supported only after its public acceptance criteria are met.

## v0.1.0-alpha — local release candidate

- portable, deterministic Prototype review engine;
- normalized evidence and component-profile schemas;
- three machine-stable ratings with explainable findings;
- synthetic safe and adversarial evaluation fixtures;
- offline M2 BEFORE/AFTER successor evaluation;
- published allow-list policy and persistence gates;
- Codex plugin/skill structure for local review;
- live EDA treated as an external environment integration, not a bundled universal adapter.

The M2 AFTER result is an offline forecast. General automatic schematic/PCB repair is outside this milestone.

## Next: one public live bounded-repair proof

Exit criteria:

1. use a disposable NOT FOR MANUFACTURING fixture;
2. capture exact schematic and PCB baselines;
3. add only the allow-listed local bypass capacitor and necessary connections;
4. independently verify identity, package, pin-to-pad, nets and geometry;
5. save, close and reload both documents;
6. rerun ERC, connectivity, containment, DRC and the Prototype review;
7. show the one target finding closing and unrelated findings not worsening;
8. publish only the sanitized minimum evidence.

Until all eight gates pass, the repair remains `prepared-not-live-verified`.

## Later alpha milestones

- add diverse power, sensor and interface fixtures with declared benchmark scopes;
- expand boundary tests for confidence, missing evidence and conservative assumptions;
- publish an adapter contract for read-only collection from multiple EDA environments;
- validate additional addition-only repair families one at a time;
- improve component-profile provenance and freshness checks;
- add reproducible report localization without changing machine enums.

## Longer-term research

- cross-document transaction and compensation semantics on non-empty designs;
- broader placement and power-return geometry analysis;
- SI/PI and thermal-tool integration through separately audited adapters;
- Manufacturing Release governance with mechanical, procurement and production evidence;
- hardware-in-the-loop validation and measured-model feedback.

These items are research directions, not current capabilities. Upload, ordering, payment and manufacture remain explicit human gates.
