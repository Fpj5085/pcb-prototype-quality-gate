# Test report — v0.1.1-alpha baseline and post-release hardening

Date: 2026-07-29
Scope: the published v0.1.1-alpha baseline plus local post-release hardening for
component-profile provenance, diverse offline benchmarks, normalized-input
safety boundaries, the adapter-neutral offline pipeline entry, the fail-closed read-only adapter evidence envelope, its offline-only explicit-capture assembler and its offline health gate for external adapter failures. This run validated the offline runtime, sanitized M2/M3
evidence boundary, fail-closed local-bypass planner, profile audit and release
tooling. It performed no EDA mutation, network publication, upload,
manufacturing, ordering or payment.

## Environment

- Managed Python 3.13.12; public runtime requirement remains Python 3.10+.
- Managed Node.js 22.22.2 used an existing project-local Ajv 8.20.0 dependency
  read-only for JSON Schema validation; no package was installed.
- Windows host and Git were used only by existing standard-library release tests
  and repository inspection.

The released review engine, M2 importer and release scripts use only the Python
standard library. Ajv and the external Codex validators are release-environment
tools and are not bundled dependencies.

## Results

| Gate | Result |
| --- | --- |
| Complete Python test suite | **104/104 passed** |
| Prototype rule/runtime tests | **32/32 passed** |
| Normalized-input safety-boundary tests | **13/13 passed** |
| Component-profile provenance/freshness tests | **10/10 passed** |
| Diverse offline benchmark tests | **4/4 passed** |
| M2 evidence-import gate tests | **11/11 passed** |
| Local-bypass repair-plan tests | **7/7 passed** |
| Read-only adapter contract tests | **6/6 passed** |
| Read-only envelope exporter tests | **4/4 passed** |
| Read-only adapter health gate tests | **6/6 passed** |
| Adapter-neutral pipeline tests | **6/6 passed** |
| Reproducible release-tool tests | **5/5 passed** |
| Sanitized/synthetic evaluation replay | **10/10 passed** |
| Component-profile audit (`--as-of 2026-07-28`) | **11/11 fresh; 0 stale; 0 invalid** |
| Python CLI smoke — complete-evidence semantic fixture | Passed; `suitable_for_low_risk_prototype` |
| PowerShell wrapper smoke — M2 BEFORE | Passed; `not_suitable_for_prototype` |
| PowerShell parser | Passed for every published `.ps1` entry |
| Plugin manifest validator | Passed |
| Skill validator | Passed |
| JSON Schema parsing/runtime coverage | **17/17 schemas parsed**; health and envelope contracts covered by Python validators |
| Previously published Schema instance validation baseline | **24/24 documents passed** |
| UTF-8 and mojibake gate | 158 text files passed |
| JSON parsing | 74 files passed |
| Restricted YAML parsing | 1 file passed |
| Python AST syntax | 27 files passed |
| Markdown relative links | 116 links; 0 missing |
| Repository privacy/release gate | Passed; 165 files; 0 high-risk findings; 163 manifest / 164 checksum entries |

## Component-profile provenance and freshness

The new audit is an independent, deterministic release/CI gate. It requires an
explicit `--as-of` date and performs no network or EDA access. The current profile
set contains 6 official datasheet sources and 5 synthetic fixtures; all 11 passed
on 2026-07-28. Adversarial tests cover missing provenance, invalid dates, future
retrieval dates, stale sources, invalid age bounds, missing revision basis,
official sources without HTTPS/location evidence, unclear synthetic origin and
output determinism.

The audit does not feed findings into `rating` or `engineeringForecastRating`,
does not change the stable three-value rating enum and does not widen the sole
public repair family `ADD_LOCAL_BYPASS_CAP`.

## Normalized-input safety boundaries

The runtime now rejects non-standard JSON numeric constants, non-finite values,
boolean-as-number values, missing calculation operands, physically inverted
ranges, invalid confidence/severity values and malformed optional containers
before any engineering rule executes. It also validates component-profile
numeric limits and ordering. Finding confidence cannot exceed the source profile
confidence, and explicitly declared assumptions remain visible at top level even
when the associated rule passes. A reproduced `NaN` power-path input had
previously emitted `POWER_HEADROOM_PASS`; the same input is now rejected before
review. Raw normalization remains compatible by omitting absent optional object
groups rather than injecting ambiguous empty objects.

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
`3`/`pending`. The positive unit fixture remains synthetic branch coverage. A
separately reviewed real sanitized M2 bundle returned `passed` and an identical
second run returned `changed: false`; only its generated minimal summary is
included in the candidate.

## Schema instances

The 24 validated documents were:

- component profiles: 1;
- Prototype inputs: 4;
- generated Prototype machine outputs: 4;
- M2 SHA manifest: 1;
- M2 bundle index: 1;
- M2 evidence documents: 10;
- M2 minimal public summary: 1;
- M3 independent minimal public summary: 1;
- immutable local-bypass repair plan: 1.

The exact Ajv package came from the existing local Bridge dependency tree and
was used read-only; the temporary generated review outputs were removed after
validation.

## Evaluation replay

The suite now includes three original synthetic BEFORE/AFTER pairs. Every BEFORE
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
`suitable_after_corrections`; those fixture outputs are not live claims. The
separate gate-generated summary verifies the real persisted transition and fresh
low-risk Prototype review, but it is still not a physical-board or Manufacturing
Release claim.

Fail-closed tests cover empty checks, each missing gate, invalid types and values,
explicit gate failures, warning disposition, live/persistence contradictions,
DRC=0 without save/reload evidence and raw normalization without injected zeros.

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
python -S -m unittest discover -s tests -p "test_*.py" -v
python scripts/run-evals.py
python src/review/component_profile_audit.py --profiles src/review/component-profiles.json --as-of 2026-07-28
python scripts/release-verify.py --skip-integrity
python scripts/update-integrity.py
python scripts/release-verify.py
```

WorkBuddy injects a host `sitecustomize` safe-delete hook that could not recycle
three test temporary directories on this Windows workspace. The first full run
therefore completed every assertion but reported three cleanup errors. Because
the candidate uses only the Python standard library, the complete suite was
rerun with `python -S`, which disables external site hooks; the current full
suite passed and all temporary directories were removed. No test assertion or product code was
changed to obtain that result.

Archive build and archive-against-committed-tree verification are performed only
after the reviewed tree is committed. The resulting deterministic archive and
sidecar remain local until a separate public-upload decision.
