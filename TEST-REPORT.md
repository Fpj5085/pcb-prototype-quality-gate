# Test report — v0.1.0-alpha local candidate

Date: 2026-07-26  
Scope: offline release candidate only. No EDA, UI, service, network publication, upload or ordering operation was used.

## Environment

- Python 3.12.10; public runtime requirement remains Python 3.10+.
- Node.js 24.15.0 was used only for local JSON Schema validation through an already installed validator.
- Windows PowerShell 5.1.26100.8875.
- Git 2.54.0.windows.1.

The released review engine itself uses only the Python standard library. Node and the local schema validator are not bundled runtime dependencies.

## Results

| Gate | Result |
| --- | --- |
| Unit and release-runtime tests | **21/21 passed** |
| Sanitized evaluation replay | **4/4 passed** |
| Python CLI smoke — AFTER successor | Passed; `suitable_for_low_risk_prototype`, 4 pass / 0 advisory / 0 blocker |
| PowerShell wrapper smoke — BEFORE | Passed; `not_suitable_for_prototype`, 3 pass / 0 advisory / 1 blocker |
| Plugin manifest validator | Passed |
| Skill validator | Passed |
| UTF-8 text decoding | 87 files passed at validation time; no replacement character |
| JSON parsing | 36 files passed at validation time |
| YAML parsing | 1 file passed |
| Python AST syntax | 6 files passed |
| Markdown relative links | 75 links across 39 Markdown files; 0 missing |
| JSON Schema compilation | **11/11 schemas passed** with a local Draft 2020-12 validator |
| Schema instance validation | Component profiles plus four inputs and four outputs passed: 9 documents |

Final publication scans and file counts are recorded separately in `release-audit/PRIVACY-SCAN.md` and `FILE-MANIFEST.json` because release reports and manifests are generated after the functional tests.

## Verified commands

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/run-evals.py
python src/review/prototype_review.py --input evals/power-distribution-after/input.json --output <temporary-output>
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/prototype-review.ps1 -InputPath evals/power-distribution-before/input.json -OutputDirectory <temporary-output>
```

The repository-local plugin and skill validators were also run against `.codex-plugin/plugin.json` and `skills/jlceda-hardware-design/`.

## Evaluation replay

| Case | Evidence status | Rating | Pass | Advisory | Blocker |
| --- | --- | --- | ---: | ---: | ---: |
| `synthetic-safe` | synthetic unit fixture | `suitable_for_low_risk_prototype` | 20 | 0 | 0 |
| `power-distribution-before` | offline; live evidence pending | `not_suitable_for_prototype` | 3 | 0 | 1 |
| `power-distribution-after` | offline successor forecast; live evidence pending | `suitable_for_low_risk_prototype` | 4 | 0 | 0 |
| `car-controller-adversarial` | offline replay from sanitized evidence | `not_suitable_for_prototype` | 5 | 9 | 15 |

The adversarial `9/9` assertion means only that nine predefined/manual benchmark risk families were matched on this one sanitized 28-component fixture. It is not a general accuracy measurement.

The M2 AFTER rating is an offline rule-engine forecast. It is not a live EDA mutation, save/reload or physical-board claim.

## Privacy regression coverage

Tests verify that:

- source-evidence and screenshot paths do not emit workstation absolute paths;
- the CLI can run from an unrelated working directory with repository-relative defaults;
- duplicate component references fail with structured output and no traceback;
- evaluation files contain no concrete workstation path, private username, UUID or internal transaction value;
- BEFORE/AFTER manifests retain offline/pending status;
- the adversarial benchmark remains fixture-scoped.

`gitleaks` was not installed in the local environment. The final gate therefore uses deterministic repository scans for credential assignments, private-key headers, paths, concrete identifiers, forbidden file types, caches and large files, with results in `release-audit/PRIVACY-SCAN.md`.
