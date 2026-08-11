# Test report — v0.1.4-alpha local candidate

Date: 2026-08-11
Scope: the v0.1.4-alpha local candidate, based on the published v0.1.3-alpha baseline plus three increments: the offline contract→review-input converter (`src/spec/contract_to_review.py` + `scripts/contract-to-review-cli.py`), the closed-loop demo wired to that converter (`scripts/run-closed-loop-demo.py` now auto-converts the hardware contract into review input by default), and the schematic sheet-frame containment rule family (`schematicSheet` input block + `schematic_containment` rules in `src/review/prototype_review.py`). This run validated the offline runtime, sanitized M2/M3 evidence boundary, fail-closed local-bypass planner, requirements gate, contract→review conversion, schematic containment, profile audit, closed-loop demo and release tooling. The packaged test run itself performed no EDA mutation, network publication, upload, manufacturing, ordering or payment.

## Environment

- Python 3.12.10; public runtime requirement remains Python 3.10+.
- Windows host and Git were used only by existing standard-library release tests and repository inspection.
- The released review engine, M2 importer, converter and release scripts use only the Python standard library.

## Results

| Gate | Result |
| --- | --- |
| Complete Python test suite | **180/180 passed** |
| Prototype rule/runtime tests | **42/42 passed** (includes 10 new schematic sheet-frame containment tests and the release-runtime tests) |
| Normalized-input safety-boundary tests | **13/13 passed** |
| Component-profile provenance/freshness tests | **10/10 passed** |
| Diverse offline benchmark tests | **4/4 passed** |
| M2 evidence-import gate tests | **11/11 passed** |
| Local-bypass repair-plan tests | **7/7 passed** |
| Read-only adapter contract tests | **6/6 passed** |
| Read-only envelope exporter tests | **4/4 passed** |
| Read-only adapter health gate tests | **6/6 passed** |
| Adapter-neutral pipeline tests | **6/6 passed** |
| Requirements-gate tests | **33/33 passed** |
| Contract→review converter tests | **28/28 passed** |
| Closed-loop demo end-to-end tests | **4/4 passed** |
| Reproducible release-tool and no-delete archive tests | **6/6 passed** |
| Sanitized/synthetic evaluation replay | **10/10 passed** |
| Component-profile audit (`--as-of 2026-07-29`) | **11/11 fresh; 0 stale; 0 invalid** |
| Python CLI smoke — complete-evidence semantic fixture | Passed; `suitable_for_low_risk_prototype` (20 pass / 0 advisory / 0 blocker) |
| PowerShell wrapper smoke — synthetic-safe fixture | Passed; `suitable_for_low_risk_prototype` |
| PowerShell parser | Passed for every published `.ps1` entry |
| Plugin manifest JSON parse | Passed; `.codex-plugin/plugin.json` layout unchanged from the reviewed v0.1.3 structure apart from the version string |
| Skill layout | Unchanged from the reviewed v0.1.3 structure; bundled JSON/YAML parses via release-verify |
| JSON Schema parsing/runtime coverage | **19/19 schemas parsed**; health and envelope contracts covered by Python validators |
| UTF-8 and mojibake gate | 178 text files passed |
| JSON parsing | 78 files passed |
| Restricted YAML parsing | 1 file passed |
| Python AST syntax | 42 files passed |
| Markdown relative links | 125 links; 0 missing |
| Repository privacy/release gate | Passed; 178 files; 0 high-risk findings; 176 manifest / 177 checksum entries |
| Closed-loop demo determinism | Two runs at pinned `--now` produce byte-identical machine artifacts (only the embedded output path in `demo-summary.zh.md` differs) |

## Component-profile provenance and freshness

The audit is an independent, deterministic release/CI gate. It requires an
explicit `--as-of` date and performs no network or EDA access. The current profile
set contains 6 official datasheet sources and 5 synthetic fixtures; all 11 passed
on 2026-07-29. Adversarial tests cover missing provenance, invalid dates, future
retrieval dates, stale sources, invalid age bounds, missing revision basis,
official sources without HTTPS/location evidence, unclear synthetic origin and
output determinism.

The audit does not feed findings into `rating` or `engineeringForecastRating`,
does not change the stable three-value rating enum and does not widen the sole
public repair family `ADD_LOCAL_BYPASS_CAP`.

## Contract→review converter and closed-loop demo

The converter (`src/spec/contract_to_review.py`) projects a requirements-gate
`hardware-contract` into `jlceda-prototype-review-input/1.0`. It is fail-closed:
coordinates are parsed only from mechanical connector positions, capacitance only
from a fully anchored name pattern, and nets are derived only from declared power
domains when a component matches a connector position. Missing facts are omitted
and logged; nothing is guessed, and every output re-validates through the review
engine's own `validate_design`. The 28-test suite covers mapping, fail-closed
negatives, determinism, duplicate-position dedupe and a false-positive pattern
regression, plus an end-to-end review run.

`scripts/run-closed-loop-demo.py` now auto-converts the gate's hardware contract
into `review-input.json` by default, so the one-command
"中文需求 → 规格 → 自动转换 → 审核 → 评级" chain needs no prefab design data; the
explicit `--design` override keeps the old prefab path. The default run over
`examples/m2-closed-loop/requirements.zh.json` (pinned `--now`) produces rating
`not_suitable_for_prototype` with exactly one blocker — `PERSISTENCE` (an offline
conversion carries no save/reload evidence) — and three advisories:
`TRACE_DATA_MISSING:+5V`, `TRACE_DATA_MISSING:GND` and
`EVIDENCE_SCOPE:OFFLINE_FORECAST`. Two runs into different output directories with
the same pinned timestamp produced byte-identical machine artifacts; the only
difference was the embedded output directory path inside `demo-summary.zh.md`.

## Schematic sheet-frame containment

The review-input schema gains an additive `schematicSheet` block (A4 page frame,
origin and `unitsPerMm` coordinate conversion). The new fail-closed
`schematic_containment` rule family geometrically judges each component's x/y
against the page, emitting `SCHEMATIC_CONTAINMENT:<ref>` blockers or an aggregate
pass with mm-coordinate evidence, `CONTAINMENT_DATA_MISSING` advisories for
coordinates the check cannot see, and a short-circuit on an externally-decided
`schematicSheet.containment` bool. The 10 new tests cover the in-page pass, all
four out-of-bounds sides, units→mm conversion, silent absence of `schematicSheet`,
unguessed missing coordinates, external short-circuit and a real M2 BEFORE/AFTER
replay (old units span -355..335 → 5 blockers; corrected 280..890 / -620..-200
units → pass). This family is additive and does not change the public three-value
rating enum or the published repair allow-list.

## Normalized-input safety boundaries

The runtime rejects non-standard JSON numeric constants, non-finite values,
boolean-as-number values, missing calculation operands, physically inverted
ranges, invalid confidence/severity values and malformed optional containers
before any engineering rule executes. It also validates component-profile
numeric limits and ordering. Finding confidence cannot exceed the source profile
confidence, and explicitly declared assumptions remain visible at top level even
when the associated rule passes. Raw normalization remains compatible by omitting
absent optional object groups rather than injecting ambiguous empty objects.

## M2 import matrix

The M2 gate uses only an explicitly named sanitized directory and SHA manifest.
Tests cover:

- complete import with one minimal public summary;
- repeated byte- and timestamp-idempotent import;
- explicit pending bundle;
- missing required evidence;
- SHA-256 mismatch;
- unmanifested input;
- incomplete save/reload evidence;
- repaired state with a remaining blocker;
- output/input overlap;
- unrelated output-file rejection;
- private field, path, UUID and credential rejection.

Stable CLI outcomes are exit `0`/`passed`, exit `2`/`rejected`, and exit
`3`/`pending`. The positive unit fixture remains synthetic branch coverage.

## Schema instances

All 19 `schemas/*.json` files parse as JSON. The read-only adapter health and
envelope contracts are additionally covered by strict Python validators in the
test suite. `prototype-review-input`, `prototype-review-output`,
`hardware-contract` and `requirements-input` documents are exercised at runtime
through the engine's schema-backed validators in the 180-test suite and the
closed-loop demo. A separate generic Draft 2020-12 validator instance pass (Ajv)
was performed for the reviewed v0.1.3 baseline (24 documents); it was not re-run
in this environment because no Ajv dependency is available locally.

## Evaluation replay

The suite includes three original synthetic BEFORE/AFTER pairs. Every BEFORE
keeps a strict and forecast `not_suitable_for_prototype` rating. Every AFTER has
zero engineering blockers and a `suitable_for_low_risk_prototype` engineering
forecast, while strict current-state rating stays `suitable_after_corrections`
because offline fixtures deliberately omit live save/reload proof.

| Case | Evidence status | Rating | Pass | Advisory | Blocker |
| --- | --- | --- | ---: | ---: | ---: |
| `synthetic-safe` | offline synthetic unit; metadata conflicts with persistence claim | `suitable_after_corrections` | 20 | 2 | 0 |
| `power-input-before` | original offline synthetic benchmark | `not_suitable_for_prototype` | 1 | 2 | 6 |
| `power-input-after` | offline forecast; persistence evidence intentionally absent | `suitable_after_corrections` | 7 | 2 | 0 |
| `sensor-interface-before` | original offline synthetic benchmark | `not_suitable_for_prototype` | 2 | 3 | 2 |
| `sensor-interface-after` | offline forecast; persistence evidence intentionally absent | `suitable_after_corrections` | 5 | 2 | 0 |
| `communication-interface-before` | original offline synthetic benchmark | `not_suitable_for_prototype` | 2 | 5 | 2 |
| `communication-interface-after` | offline forecast; persistence evidence intentionally absent | `suitable_after_corrections` | 4 | 2 | 0 |
| `power-distribution-before` | offline replay; separate live summary gate verified | `not_suitable_for_prototype` | 3 | 2 | 1 |
| `power-distribution-after` | offline successor replay; separate live summary gate verified | `suitable_after_corrections` | 4 | 2 | 0 |
| `car-controller-adversarial` | offline replay from sanitized-derived evidence | `not_suitable_for_prototype` | 5 | 9 | 15 |

The adversarial `9/9` assertion means only that nine predefined/manual benchmark
risk families were matched on this one sanitized-derived 28-component fixture.
It is not a general accuracy measurement.

The offline M2 AFTER fixture keeps `engineeringForecastRating` =
`suitable_for_low_risk_prototype` and strict `rating` =
`suitable_after_corrections`; those fixture outputs are not live claims.

## Reproducibility and privacy coverage

Tests and the repository gate verify that:

- integrity generation is byte-idempotent for an unchanged tree;
- deterministic ZIP builds from the same committed Git tree are byte-identical;
- archive members are read back against committed Git blobs;
- `PUBLIC-FILES.md` and the per-file provenance table exactly cover the repository tree;
- source-evidence and screenshot paths do not emit workstation paths;
- duplicate component references fail with structured output and no traceback;
- public fixtures contain no concrete workstation path, private username, UUID
  or internal transaction value;
- BEFORE/AFTER fixture inputs remain explicitly offline while manifests link to a separate gate-verified minimal live summary;
- forbidden binaries, extension packages, PDFs, logs, caches, symbolic links and
  files over 1 MiB are absent.

`gitleaks` was not installed in the local environment. The final privacy gate
therefore uses deterministic repository-wide checks for credential assignments,
private-key headers, paths, concrete identifiers, forbidden file classes,
encoding and size, as recorded in `PRIVACY-SCAN.md`.

## Verified commands

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:WORKBUDDY_TEST_ARCHIVE_ROOT = "<external-test-archive>"
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/run-evals.py
python src/review/component_profile_audit.py --profiles src/review/component-profiles.json --as-of 2026-07-29
python scripts/run-closed-loop-demo.py --now 2026-08-11T00:00:00 --out <out-a>
python scripts/run-closed-loop-demo.py --now 2026-08-11T00:00:00 --out <out-b>
python scripts/release-verify.py --skip-integrity
python scripts/update-integrity.py
python scripts/release-verify.py
```

Archive build and archive-against-committed-tree verification are performed only
after the reviewed tree is committed. The resulting deterministic archive and
sidecar remain local until a separate public-upload decision.
