# Prototype review model

## Work modes

- **Draft** — prioritize editable artifacts and explicit assumptions.
- **Prototype** — require current evidence, engineering findings, EDA gates and persistence checks.
- **Manufacturing Release** — defined as a governance tier but not claimed complete by v0.1.0-alpha.

## Ratings

- `not_suitable_for_prototype`: at least one high-confidence blocker exists.
- `suitable_after_corrections`: no deterministic high-confidence blocker remains, but important evidence, assumptions or advisories still require work.
- `suitable_for_low_risk_prototype`: all required current-state Prototype gates are explicitly present, correctly typed and passed, with no contradictory or offline-only evidence; the rating still does not prove physical function.

`rating` is the strict current-state result. It requires explicit values for `schematicErrors`, `schematicWarnings`, `pcbDrcFindings`, `unroutedNets`, `containment` and `savedReloaded`. Missing or invalid fields create `EVIDENCE_INCOMPLETE:*`; contradictory live/persistence metadata creates `EVIDENCE_CONFLICT:*`; an explicitly offline fixture creates an evidence-scope finding. These findings prevent a low-risk rating.

`engineeringForecastRating` excludes only evidence-completeness, evidence-conflict and offline-scope findings. It preserves real engineering blockers and advisories, but it is a prediction rather than a live release decision. `evidenceCompleteness` records field-level gate states, missing/invalid fields, contradictions and whether all strict gates passed. The original three-value rating enum remains unchanged.

Non-zero schematic warnings pass only when detailed warning evidence exists and `schematicWarningDisposition` is explicitly `explained_and_accepted`. Merely reporting a warning count or claiming that details are available is insufficient.

## Finding structure

```json
{
  "id": "DECOUPLING_DISTANCE:LOAD_1:+5V",
  "severity": "blocker",
  "confidence": "high",
  "ruleFamily": "decoupling",
  "title": "Local bypass capacitor is too far away",
  "risk": "The supply pin may droop or ring during load transitions.",
  "locations": ["LOAD_1", "+5V", "C_BYPASS"],
  "evidence": [
    {"kind": "geometry", "distanceMm": 12.4, "maxDistanceMm": 5.0},
    {"kind": "component", "capacitanceUf": 0.1, "dielectric": "X7R"}
  ],
  "calculation": "12.4 mm > 5.0 mm",
  "recommendation": "Place the validated capacitor at the supply and return pins.",
  "revalidation": ["net_pair", "value", "distance", "save_reload"],
  "assumptions": []
}
```

Severity and confidence are orthogonal. A high-severity observation based on low-confidence evidence should trigger evidence collection rather than a false precise conclusion. A high-confidence blocker fails closed.

## Evidence provenance

Each critical conclusion should be traceable to one or more of:

- current EDA readback;
- manufacturer, title, official URL, relevant pages/tables and confidence;
- explicit calculation inputs and formula;
- conservative assumptions separated from measured facts;
- save/reload and post-reload checks.

Third-party PDFs are link-only and are not distributed in the repository.

The normalized groups and published workflow schemas are described in [Evidence schema](evidence-schema.md). Structural validation is not truth validation: a schema-valid number, `DRC=0`, offline replay or passing unit test still needs trustworthy current-document provenance and save/reload evidence.

## Rule families

- identity, package and pin-to-pad;
- power-path headroom and absolute maximum;
- regulator dissipation and temperature-rise estimate;
- fuse/PTC continuous and surge budget;
- motor-driver continuous/peak current and bridge loss;
- external-trace current capacity and neck-down risk;
- local decoupling and bulk energy storage;
- interface divider and absolute-maximum margin;
- debug, test-point, polarity and silkscreen usability;
- schematic topology, firmware pin conflicts and hidden power pins;
- PCB connectivity, containment, DRC, ground return and persistence.

## Why DRC=0 is insufficient

DRC is primarily a geometric and rule-deck check. It does not prove regulator dropout margin, component package evidence, load surge behavior, H-bridge thermal loss, capacitor placement quality, interface voltage safety, ground-current topology, saved persistence or physical performance.
