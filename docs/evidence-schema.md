# Evidence schema

The review engine consumes normalized engineering evidence rather than a raw EDA project. This keeps the deterministic rules portable and makes the trust boundary explicit: an environment adapter may collect evidence, but the review engine does not assume that an adapter acknowledgement proves a saved design.

## Published contracts

The repository includes reusable JSON Schemas for the review engine and the governed workflow around it:

| Contract | File | Purpose |
| --- | --- | --- |
| Prototype review input | [`prototype-review-input.schema.json`](../schemas/prototype-review-input.schema.json) | Normalized schematic, PCB, electrical and persistence evidence. |
| Component profiles | [`component-profiles.schema.json`](../schemas/component-profiles.schema.json) | Sourced limits and package facts used by generic rules. |
| Prototype review output | [`prototype-review-output.schema.json`](../schemas/prototype-review-output.schema.json) | Rating, counts, findings and unresolved assumptions. |
| Read-only project snapshot | [`project-snapshot.schema.json`](../schemas/project-snapshot.schema.json) | Captured project/schematic/PCB evidence with content integrity. |
| Circuit intent | [`circuit-dsl.schema.json`](../schemas/circuit-dsl.schema.json) | Offline design intent, constraints and unresolved items. |
| Component lockfile | [`component-lockfile.schema.json`](../schemas/component-lockfile.schema.json) | Component identity, package, pin map and source-document claims. |
| Hardware contract | [`hardware-contract.schema.json`](../schemas/hardware-contract.schema.json) | Board, signal, interface and power-domain contract. |
| Firmware pin manifest | [`firmware-pin-manifest.schema.json`](../schemas/firmware-pin-manifest.schema.json) | Firmware-side binding intent. |
| Pin consistency report | [`pin-consistency-report.schema.json`](../schemas/pin-consistency-report.schema.json) | Hardware/firmware binding comparison. |
| Immutable change set | [`change-set.schema.json`](../schemas/change-set.schema.json) | Preview-only, baseline-bound change intent. |
| Change preview | [`change-preview.schema.json`](../schemas/change-preview.schema.json) | Non-executable risk summary and review disposition. |

The Prototype engine versions its runtime payloads with `jlceda-prototype-review-input/1.0`, `jlceda-component-profiles/1.0`, `jlceda-prototype-review/1.0` and `jlceda-prototype-review-manifest/1.0`. The first three have standalone schemas; the generated evidence manifest is covered by runtime tests and the output-file contract below.

JSON Schema validates structure. It does not establish that a measurement, component profile or live readback is true. Provenance and independent revalidation remain required.

## Review input

The root object contains these stable groups:

- `schema`, `designName` and optional sanitized fixture metadata;
- `components` and `nets` with designators, roles, package/profile references and geometry needed by rules;
- `powerPaths`, `regulatorUses`, `protectedCircuits` and `hbridgeUses`;
- `decouplingRequirements`, `bulkCapRequirements` and `voltageDividers`;
- `pcb.traceCapacity`, `groundReview` and `schematicTopology`;
- `debugInterface`, `usability` and `firmwarePins`;
- `checks` for ERC/schematic errors, connectivity, containment, DRC and save/reload;
- `sourceEvidence`, containing sanitized provenance descriptions rather than private workstation paths.

Inputs must separate three kinds of information:

1. **Observed facts** — current adapter readback or a synthetic fixture value.
2. **Sourced facts** — manufacturer, MPN, package, pin-to-pad mapping, official document title/URL and relevant page/table.
3. **Assumptions** — conservative values that have not been measured on the physical device.

An unknown value should be omitted or marked as unknown according to the schema. It should not be replaced with a precise-looking guess.

## Component profiles

Generic rules refer to a profile key; they do not hard-code a fixture designator. A profile may contain electrical limits, package expectations and evidence metadata. Critical facts should include:

- manufacturer and exact MPN or a clearly identified generic profile;
- expected package and pin-to-pad evidence;
- limit value, units and operating conditions;
- official source title and URL;
- relevant page, section or table;
- confidence and any unresolved interpretation.

The repository links to source documents and does not redistribute third-party PDF files.

## Finding output

Every finding is intended to be understandable by both software and a non-specialist reviewer:

```json
{
  "id": "DECOUPLING_DISTANCE:LOAD_1:+5V",
  "severity": "blocker",
  "confidence": "high",
  "ruleFamily": "decoupling",
  "title": "Local bypass capacitor is too far away",
  "riskZh": "负载切换时电源脚可能跌落或振铃。",
  "locations": ["LOAD_1", "+5V", "C_BYPASS"],
  "evidence": [
    {"distanceMm": 12.4, "maxDistanceMm": 5.0}
  ],
  "calculation": "12.4 mm > 5.0 mm",
  "recommendationZh": "把已核验电容放到供电脚和回流脚附近。",
  "revalidation": "重新核验网络、数值、距离和保存重载。",
  "unresolvedAssumptions": []
}
```

Severity and confidence are independent. A high-confidence blocker yields `not_suitable_for_prototype`. Missing critical evidence can yield `suitable_after_corrections`; it is not silently converted into a pass.

## Persistence evidence

A live change is complete only when evidence records:

1. exact pre-write state;
2. plan-owned object identities;
3. immediate post-write readback;
4. save, close and reload completion;
5. independent post-reload readback;
6. fresh ERC/connectivity/containment/DRC and Prototype review results;
7. target-finding improvement with no unrelated regression.

The public M2 AFTER fixture currently describes an offline successor forecast. Its manifest remains `offline-successor-forecast-pending-live-evidence` until a real environment produces the complete sequence above.

## Privacy rules

Public evidence uses synthetic case IDs and repository-relative paths. It excludes project/page/object/library identifiers, approvals, receipts, checkpoints, workstation paths, private logs and account-bearing screenshots. See [Privacy](privacy.md).
