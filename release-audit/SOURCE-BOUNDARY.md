# Source and publication boundary

This document records the provenance boundary for the local v0.1.0-alpha
candidate. It intentionally uses repository-relative descriptions and contains
no workstation paths or live project identifiers.

## Included project work

| Area | Provenance finding | Publication treatment |
| --- | --- | --- |
| `src/review/prototype_review.py` | Project review engine adapted from a private working tree; staged copy is a portability-focused revision | Include after maintainer authorship and relicensing attestation |
| `tests/review/` | Project tests plus synthetic/sanitized fixtures | Include after fixture privacy scan and ownership attestation |
| `schemas/` | Byte-for-byte copies of project schemas from a private working tree; no source-tree license file was found | Include only after explicit owner confirms Apache-2.0 relicensing rights |
| `src/review/component-profiles.json` | Project profile structure and thresholds with factual manufacturer evidence | Include metadata and official links; exclude data-sheet prose, figures, tables, and PDFs |
| `skills/` and `.codex-plugin/` | Public rewrite of the project's governance skill and portable plugin metadata | Include only portable policy and relative paths; exclude private wrappers and runtime bindings |
| `README*`, `docs/`, examples, and release documents | Original public-release documentation | Include after claims, links, privacy, and attribution review |
| `evals/` | Synthetic or sanitized evaluation structures | Include with explicit `synthetic`, `sanitized`, `live`, or `pending` status; never imply pending evidence is live proof |

## Reference-only third parties

- Python is a user-installed runtime; no interpreter or standard-library source
  is bundled.
- JSON Schema is referenced by its public meta-schema URI; the specification
  text and validator implementations are not bundled.
- IPC-2221 is referenced by name for a conservative screening estimate; no
  standard text, table, or figure is bundled and no certification is claimed.
- OpenAI Codex and JLCEDA/EasyEDA are optional user-provided host platforms.
- EasyEDA Copilot is an optional historical draft adapter; no source, binary,
  extension package, cache, or log is included.
- Manufacturer and supplier names, MPNs, numeric facts, and official URLs are
  used for engineering evidence and interoperability. Copyrighted PDFs and
  catalog databases are excluded.

See `THIRD_PARTY.md` for the public attribution table.

## Always excluded

- third-party application or extension source and binaries;
- private bridge, gateway, wrapper, approval, recovery, supervisor, or daemon
  implementations;
- live EDA projects, object dumps, screenshots, logs, conversations, and machine
  state;
- credentials, tokens, cookies, authorization headers, service configuration,
  concrete internal identifiers, receipts, checkpoints, and nonces;
- manufacturer PDFs, copied figures/tables, supplier catalogs, and private
  component caches;
- generated caches, temporary smoke-test output, archives, executables, and
  unexplained large files.

## Required human release attestations

Before public distribution, the release owner must confirm:

1. authorship or Apache-2.0 relicensing rights for the review engine, schemas,
   tests, skill text, documentation, and fixtures;
2. absence of employer, client, contractor, or prior-repository claims;
3. factual-only treatment of manufacturer evidence;
4. synthetic/sanitized status of every evaluation fixture;
5. absence of all material listed in **Always excluded**.

These attestations are deliberately retained as human checklist items. A clean
privacy scan does not prove copyright ownership.
