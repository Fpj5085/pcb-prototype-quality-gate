# M2 live-evidence import gate

The M2 import gate turns an explicitly supplied, already-sanitized evidence
bundle into one commit-ready public summary. It is offline, deterministic and
idempotent. It never discovers a workstation directory, contacts an EDA tool,
or copies raw receipts, logs, screenshots, project identifiers or approvals.

## Trust boundary

The gate validates completeness, consistency, privacy and hashes of a sanitized
bundle. It does not manufacture evidence and it does not prove that a source
attestation is genuine. The maintainer must obtain the input from an independently
reviewed live run and preserve the private originals outside this repository.

The public synthetic fixture under `tests/m2_gate/fixtures/` exercises the gate's
positive branch. Its `live` fields are test values, not observations from JLCEDA.

## Required evidence

Both `before` and `after` must provide manifest-covered JSON documents for:

1. a successful live-delivery receipt attestation with its identifier redacted;
2. save, close, reload and post-reload readback;
3. independent readback with component and network counts;
4. completed DRC, board containment and connectivity;
5. a fresh Prototype review with the target finding state and regression result.

The repaired `after` state must have zero blockers, a
`suitable_for_low_risk_prototype` rating, a resolved target finding and no
increase in unrelated risk severity. Missing or incomplete evidence remains
`pending`; malformed, unhashed or privacy-bearing evidence is rejected.

## Input layout

```text
<sanitized-input>/
├── bundle.json
├── SHA256-MANIFEST.json
└── evidence/
    ├── before/
    │   ├── receipt.json
    │   ├── save-reload.json
    │   ├── independent-readback.json
    │   ├── drc.json
    │   └── prototype-review.json
    └── after/
        └── ...same five evidence classes...
```

Every JSON file except the SHA manifest must appear exactly once in the manifest.
Unlisted files, symbolic links, hash mismatches and path traversal are rejected.
The output directory must be separate from the input and may contain only the
deterministic public summary.

## Command

```powershell
python scripts/import_m2_evidence.py `
  --input-dir <sanitized-input> `
  --sha-manifest <sanitized-input>/SHA256-MANIFEST.json `
  --output-dir <commit-ready-public-output>
```

Stable outcomes:

| Exit | Gate | Meaning |
| ---: | --- | --- |
| `0` | `passed` | All evidence classes, hashes and privacy gates passed; one minimal summary was written. |
| `2` | `rejected` | The bundle is malformed, privacy-bearing, unhashed, hash-inconsistent or otherwise unsafe to import. |
| `3` | `pending` | Required live evidence is absent or has not reached the required successful state. |

On a repeated successful run, identical output bytes are retained and the file
timestamp is left unchanged. The single output file is
`m2-live-evidence-summary.json`; it contains only aggregate counts, review state,
DRC state and explicit privacy booleans.

## Publication rule

The current M2 bundle passed the offline hash and privacy gate, and the generated
minimal summary is published as `release-audit/m2-live-evidence-summary.json`.
The synthetic eval inputs remain offline replay fixtures; their manifests link to
the separate verified summary rather than pretending the fixture bytes came from
EDA. Raw receipts and private source evidence remain outside this repository.
A passing synthetic unit fixture alone never changes M2 publication status.
