# Schemas

This directory contains original, implementation-neutral data contracts for review evidence, project snapshots, component locks, immutable change previews and firmware pin consistency.

The `projectUuid`, `schematicUuid`, `pcbUuid` and `changeSetId` property names in some schemas are generic contract fields. The repository contains no real project identifier or transaction value. Public evaluation fixtures omit these internal integration identifiers.

Prototype review files use:

- `prototype-review-input.schema.json`;
- `prototype-review-output.schema.json`;
- `component-profiles.schema.json`.

The only current public repair-plan contract is:

- `local-bypass-repair-plan.schema.json` for fail-closed, immutable
  `ADD_LOCAL_BYPASS_CAP` planning. It contains no live project identity or
  executable approval.

The future M2 live-evidence import gate uses:

- `m2-evidence-sha-manifest.schema.json`;
- `m2-live-evidence-bundle.schema.json`;
- `m2-live-evidence-document.schema.json`;
- `m2-public-evidence-summary.schema.json`.

These contracts describe already-sanitized input and a minimal public output.
The positive documents under `tests/m2_gate/fixtures/` are synthetic validation
fixtures rather than observations from a live EDA run.

The remaining schemas describe optional governed-adapter contracts. Shipping a schema or a passing synthetic gate test does not claim that a general live mutation adapter is included or demonstrated.
