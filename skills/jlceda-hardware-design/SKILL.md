---
name: jlceda-hardware-design
description: Use when reviewing a JLCEDA or EasyEDA schematic/PCB from ordinary-language requirements, deciding Prototype sample readiness, explaining electrical and layout risks, or planning a bounded allow-listed repair with independent save/reload revalidation.
---

# JLCEDA Hardware Design Review

Use this skill as a quality gate, not as a promise that an AI-drawn board is ready to manufacture.

## Workflow

1. Classify the request as **Draft**, **Prototype**, or **Manufacturing Release** using `references/work-modes.md`.
2. Collect current design evidence through an audited adapter. Treat adapter mutation acknowledgements as untrusted until independently read back.
3. Normalize evidence for the read-only Prototype engine in [`../../src/review/prototype_review.py`](../../src/review/prototype_review.py).
4. Review identity and footprint, electrical headroom, thermal margin, protection, current capacity, decoupling, bulk energy storage, interface levels, return paths, mechanical usability, and persistence.
5. Report one of three machine-stable ratings:
   - `not_suitable_for_prototype`
   - `suitable_after_corrections`
   - `suitable_for_low_risk_prototype`
6. If a repair is requested, consult [`references/supported-repair-policy.md`](references/supported-repair-policy.md). Apply only a demonstrated allow-listed mutation with an exact baseline, immutable plan, readback, compensation boundary, save/close/reload, and a fresh review.
7. State assumptions and required physical measurements. DRC/ERC success is necessary but not sufficient.

## Hard Boundaries

- Do not describe this alpha as a general autonomous PCB repair or manufacturing-release system.
- Do not treat code, a report, an acknowledgement, or DRC=0 as proof that a live design changed or persisted.
- Treat live EDA access as an environment integration. This plugin ships no MCP server, workstation wrapper or third-party extension, and offline review must remain usable without them.
- Do not bundle third-party EDA extensions, data-sheet PDFs, private logs, screenshots, credentials, or project identifiers.
- Do not upload, order, pay for, or manufacture a board as part of this public workflow.

Read [`references/review-evidence.md`](references/review-evidence.md) and [`references/safety-and-privacy.md`](references/safety-and-privacy.md) before publishing results. Use repository-relative paths in public evidence and never ask an ordinary user for adapter-internal identifiers.
