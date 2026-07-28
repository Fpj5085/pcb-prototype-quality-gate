# Demo: 20–25 minute review walkthrough

## Demo promise

Show one narrow claim: an editable or DRC-clean AI-generated design can still fail a conservative Prototype review, and an intended correction must remain clearly separated from a verified live save/reload result.

Use the product loop as orientation, not as a claim that every live step ships in this alpha:

> Ordinary-language need → real editable schematic/PCB → independent automated review → allow-listed correction → save/reload re-verification → plain-language prototype rating.

The Draft generator is replaceable. The independent review and bounded re-validation loop—not ownership of a particular generator—is the product's core value.

The demo uses only repository fixtures and the offline review engine. It does not operate JLCEDA, install an EDA extension or claim physical validation.

## Preparation

From the repository root:

```powershell
python -m unittest discover -s tests/review -p "test_*.py" -v
python scripts/run-evals.py
```

Keep these pages open:

- [Architecture](architecture.md)
- [Review model](review-model.md)
- [Supported repairs](supported-repairs.md)
- the generated `machine-review.json` for each fixture

## Script

### 0:00–2:00 — Positioning

Say:

> This is not another tool whose main claim is that AI can draw a PCB. It is a quality gate that asks whether the evidence supports a low-risk prototype and what must be revalidated after a bounded correction.

Point out the six-stage product loop, the three ratings and the rule that `DRC=0` is necessary but insufficient. Clarify that this repository demo starts from normalized evidence: the live Draft and EDA mutation adapters are replaceable environment integrations and are not bundled.

### 2:00–5:00 — Establish the strict semantic control

Run the complete-evidence semantic fixture at `tests/review/fixtures/synthetic-safe-input.json`. Show:

- machine rating `suitable_for_low_risk_prototype`;
- zero blockers and zero advisories;
- all six required gate fields explicitly present and passed;
- the remaining physical-test boundary.

This control demonstrates that the engine is not designed to reject every complete evidence set. Then contrast it with the public `evals/synthetic-safe` offline replay: its engineering forecast may pass, but contradictory offline/persistence metadata downgrades the strict rating to `suitable_after_corrections`.

### 5:00–10:00 — M2 BEFORE: one understandable blocker

Open the 5 V / 1 A distribution-board BEFORE fixture. Explain that it is synthetic and intentionally small:

- six components;
- one input and two outputs;
- a 1 A design target;
- one intended blocker: the output split lacks a qualified local bypass capacitor.

Show `DECOUPLING_DISTANCE:J2:+5V`. Walk through value range, `+5V`/`GND` pairing, geometry and revalidation. Emphasize that a nearby 10 µF capacitor does not satisfy the configured 80–220 nF local-bypass rule merely because it is a capacitor.

### 10:00–14:00 — M2 AFTER: keep the offline fixture separate from live evidence

Compare the AFTER successor:

- one additional 100 nF X7R capacitor;
- locked package and pin-to-pad intent;
- predicted 1.9 mm distance;
- forecast blocker delta `-1`.

Then show the manifest status. Say explicitly:

> The offline successor fixture's strict rating remains `suitable_after_corrections`; replaying fixture bytes is not live save/reload proof. Separately, the gate-generated public summary records a sanitized real transition with save/reload, independent readback, DRC and a fresh low-risk review.

Also state that the fixture and the live summary are different evidence classes. The manifest links them without claiming that the synthetic input bytes came from the EDA run.

### 14:00–20:00 — Why DRC=0 is not enough

Open the 28-component adversarial motor-controller fixture. Show that its source evaluation had containment and DRC=0, then group the review findings into understandable risks:

- regulator headroom/package evidence;
- protection and motor-driver current/thermal budget;
- narrow power paths;
- local decoupling and bulk storage;
- interface/debug usability;
- ground-return and topology evidence.

State the benchmark exactly:

> On this one fixture, the engine detected all 9 of 9 predefined manual benchmark risk families.

Do not call this general accuracy, recall or certification.

### 20:00–23:00 — Repair boundary

Open [Supported repairs](supported-repairs.md). Contrast:

- one scoped `live-evidence-gate-verified` M2 local-bypass case, with no bundled public mutation runtime;
- `planned-experimental` bulk-cap addition;
- report-only regulator, H-bridge, fuse and reroute items.

Explain why the project prefers a narrow truthful allow-list over broad mutation claims.

### 23:00–25:00 — Close and questions

Summarize:

1. ordinary-language intent can enter through a replaceable Draft adapter or an existing editable design;
2. a real schematic/PCB must be read back and normalized independently;
3. findings and the plain-language prototype rating are explainable and fixture-reproducible;
4. only allow-listed changes may enter a bounded repair plan;
5. live changes require save/close/reload, independent readback and regression proof;
6. physical testing and Manufacturing Release remain separate gates.

Useful Q&A answer: the engine is useful offline today; live EDA collection is an environment integration and automatic repair support is published one verified allow-list entry at a time.

## Fixture details

## 1. Positive pair: 5 V / 1 A distribution board

### User request

Build a NOT FOR MANUFACTURING, one-input/two-output 5 V / 1 A power distribution board.

### BEFORE

- six components on a 50 mm × 30 mm synthetic board;
- `+5V` and `GND` trunks are 1.2192 mm;
- three two-pin connectors and three 10 µF capacitors;
- sole intended blocker: output branch `J2` has no qualified 80–220 nF local bypass capacitor within 7 mm.

Expected rating: `not_suitable_for_prototype`.

### AFTER successor

- seven components;
- adds `C4`, 100 nF, X7R, 50 V, C0805;
- pad 1 to `+5V`, pad 2 to `GND`;
- predicted distance to output split: 1.9 mm.

Expected delta: close `DECOUPLING_DISTANCE:J2:+5V`, add pass `DECOUPLING_PASS:J2:+5V`, blocker delta `-1`.

The current public eval input is an offline successor fixture. Its engineering forecast may pass while its strict rating remains `suitable_after_corrections`. The separate gate-generated summary records the sanitized real save/reload, independent readback, connectivity, containment, DRC and fresh-review outcome; raw EDA identity and receipts remain outside the repository.

## 2. Adversarial case: two-motor controller

- 28 components, 27 nets, two layers, 90 mm × 70 mm;
- schematic and PCB were editable in the source evaluation;
- board containment passed and DRC reported zero findings;
- Prototype review still rejected the fixture.

Risk families include regulator headroom/package mismatch, fuse budget, H-bridge loss/thermal, narrow power traces, remote decoupling/missing bulk storage, interface/debug usability and ground-return concerns.

The benchmark statement is limited to: **9 of 9 seeded/manual benchmark risk families were detected on this fixture**. It does not generalize to arbitrary hardware.
