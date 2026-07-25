# Car controller adversarial fixture

Sanitized offline replay of a 28-component, 27-net two-motor controller evaluation fixture.

## Why it exists

The source evaluation represented an editable schematic/PCB, board containment and EDA DRC with zero findings. The Prototype review still identified electrical, thermal, protection, routing, decoupling, interface and return-path risks.

Expected result:

- rating: `not_suitable_for_prototype`;
- 15 blockers, 9 advisories and 5 passes;
- all 9 of 9 predefined manual benchmark risk families matched.

The `9/9` statement applies only to the risk-family benchmark encoded in this fixture's `expected.json`. It is not general accuracy, recall, certification or evidence that arbitrary boards are reviewed correctly.

## Replay

```powershell
python scripts/run-evals.py --case car-controller-adversarial
```

## Privacy and evidence

Project, page, library and object identities were removed or replaced. Raw projects, screenshots, private logs and third-party documents are not bundled. `evidence/status.json` records this boundary.

`manifest.template.json` is a structure template only; the replay runner consumes `manifest.json`.
