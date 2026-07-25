# Schemas

This directory contains original, implementation-neutral data contracts for review evidence, project snapshots, component locks, immutable change previews and firmware pin consistency.

The `projectUuid`, `schematicUuid`, `pcbUuid` and `changeSetId` property names in some schemas are generic contract fields. The repository contains no real project identifier or transaction value. Public evaluation fixtures omit these internal integration identifiers.

Prototype review files use:

- `prototype-review-input.schema.json`;
- `prototype-review-output.schema.json`;
- `component-profiles.schema.json`.

The remaining schemas describe optional governed-adapter contracts. Shipping a schema does not claim that a general live mutation adapter is included or demonstrated.
