# Synthetic safe fixture

Generic synthetic control case used to verify that the review engine can pass a fixture satisfying its configured gates.

Expected result: `suitable_for_low_risk_prototype`, with 20 passes and no blocker or advisory.

## Replay

```powershell
python scripts/run-evals.py --case synthetic-safe
```

This is unit/regression coverage, not evidence that an arbitrary physical board is safe. It uses synthetic profiles and generic package names, performs no EDA write and includes no live save/reload proof.

Files follow the same `input.json` / `expected.json` / `manifest.json` / `evidence/status.json` convention as the other cases. `manifest.template.json` is provided for authors of future synthetic fixtures.
