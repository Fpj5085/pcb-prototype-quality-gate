# Power distribution BEFORE

Synthetic offline Prototype-review fixture for a NOT FOR MANUFACTURING 5 V / 1 A, one-input/two-output distribution board.

## Current truth status

| Field | Value |
| --- | --- |
| Components | 6 |
| Fixture execution | offline deterministic replay |
| Separate live-evidence gate | `verified` |
| Live EDA verified | Yes, via minimal public summary |
| Live save/reload verified | Yes, via minimal public summary |
| EDA writes represented by this fixture | 0 |

The fixture intentionally contains one high-confidence blocker: `DECOUPLING_DISTANCE:J2:+5V`. A nearby 10 µF capacitor does not satisfy the configured 80–220 nF local-bypass requirement.

Expected result: `not_suitable_for_prototype`, with 1 blocker, 0 advisories and 3 passes.

## Replay

From the repository root:

```powershell
python scripts/run-evals.py --case power-distribution-before
```

## Files

- `input.json` — normalized synthetic engineering evidence;
- `expected.json` — exact rating, counts and finding assertions;
- `manifest.json` — current executable fixture status;
- `manifest.template.json` — publication template for a future or derived case;
- `evidence/status.json` — machine-readable link to the verified minimal live-evidence summary;
- `evidence/README.md` — public evidence boundary and source requirements.

This case input remains an offline deterministic replay and is not a raw saved EDA project. The separate gate-generated public summary records that a matching six-component live BEFORE baseline, save/reload, independent readback, clean DRC and the intended blocker were verified.
