# Power distribution AFTER successor

Synthetic offline successor for the 5 V / 1 A distribution-board BEFORE fixture.

## Intended delta

- component count changes from 6 to 7;
- add `C4`, 100 nF, X7R, 50 V, C0805;
- connect pad 1 to `+5V` and pad 2 to `GND`;
- predicted local distance to `J2`: 1.9 mm;
- close `DECOUPLING_DISTANCE:J2:+5V` and add `DECOUPLING_PASS:J2:+5V`.

## Current truth status

| Field | Value |
| --- | --- |
| Execution | `offline-successor-forecast-pending-live-evidence` |
| Live EDA verified | No |
| Live save/reload verified | No |
| EDA writes represented by this fixture | 0 |

Expected offline result: `suitable_for_low_risk_prototype`, with 0 blockers, 0 advisories and 4 passes. That result is a rule-engine forecast, not a live repair-closure claim.

## Replay

```powershell
python scripts/run-evals.py --case power-distribution-after
```

## Files

- `input.json` — synthetic successor evidence;
- `expected.json` — exact expected finding delta;
- `manifest.json` — current offline/pending status;
- `manifest.template.json` — future publication template;
- `evidence/status.json` and `evidence/README.md` — live-evidence gate.

The fixture must remain pending until a real environment proves identity, schematic/PCB persistence and fresh review without unrelated regression.
