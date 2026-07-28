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
| Fixture execution | offline deterministic successor replay |
| Separate live-evidence gate | `verified` |
| Live EDA verified | Yes, via minimal public summary |
| Live save/reload verified | Yes, via minimal public summary |
| EDA writes represented by this fixture | 0 |

Expected strict result: `suitable_after_corrections`, with 0 blockers, 2 evidence advisories and 4 passes. The separate `engineeringForecastRating` is `suitable_for_low_risk_prototype`; it is not a live repair-closure claim.

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

The fixture input remains offline and keeps its fail-closed replay rating. Separately, the gate-generated public summary verifies a seven-component live AFTER state with save/reload, independent readback, clean DRC, resolved target finding, no unrelated risk-severity increase and a fresh low-risk Prototype rating.
