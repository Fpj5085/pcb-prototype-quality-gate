# M2 evidence integration status

Last local evidence-gate check: 2026-07-27.

## Result

A real M2 BEFORE/AFTER loop was independently reviewed outside this repository,
reduced to the ten exact sanitized evidence documents required by the existing
gate, and covered by an exact SHA-256 manifest. The gate returned
`passed / LIVE_EVIDENCE_VERIFIED`; an identical second run returned
`changed: false`.

The candidate contains only the generated minimal summary:

- BEFORE: 6 components, 2 networks, one target blocker present;
- AFTER: 7 components, 2 networks, zero blockers, target finding resolved;
- both stages: receipt, save/reload, independent readback, containment,
  connectivity and zero-error DRC verified;
- AFTER fresh Prototype rating: `suitable_for_low_risk_prototype`;
- unrelated risk severity did not worsen.

The synthetic eval inputs remain offline deterministic replays and still represent
zero EDA writes. Their manifests link to the separate public summary instead of
pretending that fixture bytes are raw live captures.

No raw external artifact, screenshot, log, workstation path, private identifier,
approval, ChangeSet or receipt was copied into this repository.

## Import path and boundary

The candidate includes `scripts/import_m2_evidence.py`, four public M2 evidence
schemas and synthetic gate tests. Any future replacement input must still be
explicitly named, fully covered by a SHA-256 manifest and contain complete
BEFORE/AFTER receipt, persistence, independent-readback, DRC and fresh-review
evidence. The importer returns `pending` for incomplete evidence and rejects hash
or privacy failures.

The synthetic successful fixture exercises code coverage only. The current M2
status changed because a separately reviewed real sanitized bundle passed the
gate, not because the synthetic fixture passed.
