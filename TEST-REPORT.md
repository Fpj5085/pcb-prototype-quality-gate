# Test report — v0.1.0-alpha hardened local candidate

Date: 2026-07-26  
Scope: offline release candidate only. EDA, UI, workstation services, network
publication, upload and ordering were outside this validation run.

## Environment

- Python 3.12.10; public runtime requirement remains Python 3.10+.
- Node.js 24.15.0 was used only with an exact cached Ajv 8.20.0 installation
  in a temporary directory for JSON Schema validation.
- Windows PowerShell 5.1.26100.8875.
- Git 2.54.0.windows.1.

The released review engine, M2 importer and release scripts use only the Python
standard library. Ajv and the external Codex validators are release-environment
tools and are not bundled dependencies.

## Results

| Gate | Result |
| --- | --- |
| Complete Python test suite | **37/37 passed** |
| Prototype rule/runtime tests | **21/21 passed** |
| M2 evidence-import gate tests | **11/11 passed** |
| Reproducible release-tool tests | **5/5 passed** |
| Sanitized evaluation replay | **4/4 passed** |
| Python CLI smoke — synthetic safe | Passed; `suitable_for_low_risk_prototype` |
| PowerShell wrapper smoke — M2 BEFORE | Passed; `not_suitable_for_prototype` |
| PowerShell parser | Passed for every published `.ps1` entry |
| Plugin manifest validator | Passed |
| Skill validator | Passed |
| JSON Schema compilation | **15/15 schemas passed** with Ajv 8.20.0, Draft 2020-12 |
| Schema instance validation | **22/22 documents passed** |
| UTF-8 and mojibake gate | 121 text files passed |
| JSON parsing | 52 files passed |
| Restricted YAML parsing | 1 file passed |
| Python AST syntax | 14 files passed |
| Markdown relative links | 104 links across 47 Markdown files; 0 missing |
| Repository privacy/release gate | Passed; 0 high-risk findings |

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
`3`/`pending`. The positive fixture is synthetic branch coverage. It does not
change either M2 live-verification flag.

## Schema instances

The 22 validated documents were:

- component profiles: 1;
- Prototype inputs: 4;
- generated Prototype machine outputs: 4;
- M2 SHA manifest: 1;
- M2 bundle index: 1;
- M2 evidence documents: 10;
- M2 minimal public summary: 1.

The exact Ajv package came from an existing local npm cache with offline mode;
the temporary validator directory was removed after validation.

## Evaluation replay

| Case | Evidence status | Rating | Pass | Advisory | Blocker |
| --- | --- | --- | ---: | ---: | ---: |
| `synthetic-safe` | synthetic unit fixture | `suitable_for_low_risk_prototype` | 20 | 0 | 0 |
| `power-distribution-before` | offline; live evidence pending | `not_suitable_for_prototype` | 3 | 0 | 1 |
| `power-distribution-after` | offline successor forecast; live evidence pending | `suitable_for_low_risk_prototype` | 4 | 0 | 0 |
| `car-controller-adversarial` | offline replay from sanitized-derived evidence | `not_suitable_for_prototype` | 5 | 9 | 15 |

The adversarial `9/9` assertion means only that nine predefined/manual benchmark
risk families were matched on this one sanitized-derived 28-component fixture.
It is not a general accuracy measurement.

The M2 AFTER rating remains an offline rule-engine forecast. It is not a live EDA
mutation, save/reload or physical-board claim.

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
- BEFORE/AFTER manifests retain offline/pending status;
- forbidden binaries, extension packages, PDFs, logs, caches, symbolic links and
  files over 1 MiB are absent.

`gitleaks` was not installed in the local environment. The final privacy gate
therefore uses deterministic repository-wide checks for credential assignments,
private-key headers, paths, concrete identifiers, forbidden file classes,
encoding and size, as recorded in `PRIVACY-SCAN.md`.

## Verified commands

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/run-evals.py
python scripts/release-verify.py --skip-integrity
python scripts/update-integrity.py
python scripts/release-verify.py
python scripts/build-release.py
python scripts/release-verify.py --archive ../codex-jlceda-hardware-agent-v0.1.0-alpha.zip
```

The final archive command is executed only after the local candidate commit is
clean. Exact archive identity is carried by the neighboring `.zip.sha256`
sidecar rather than embedded into the repository, avoiding a circular digest.
