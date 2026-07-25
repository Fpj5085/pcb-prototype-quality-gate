# Third-party notices

The staged v0.1.0-alpha candidate does **not** vendor a third-party runtime
dependency. The offline review engine uses only the Python standard library.
The items below are platforms, specifications, or evidence references.

| Item | Source/status | Use in this project | Distributed in this repository? |
| --- | --- | --- | --- |
| Python | Python Software Foundation; Python 3.10+ expected | Runs the offline review engine and tests | No interpreter or standard-library source bundled |
| JSON Schema | Public specification; 2020-12 meta-schema URI referenced | Declares data-contract vocabulary | No specification text or validator bundled; repository schemas are project files |
| IPC-2221 | IPC standard referenced by name | Conservative external-trace screening estimate | No standard text, table, or figure bundled; not represented as certification |
| OpenAI Codex | Optional user-provided host environment | Loads the project plugin/skill structure | No OpenAI software bundled |
| JLCEDA / 嘉立创EDA / EasyEDA | Proprietary user-provided application | Optional live EDA integration boundary | No application code, gateway, catalog, or project file bundled |
| EasyEDA Copilot | Optional third-party draft adapter | Historical/optional draft-generation reference | No source, binary, extension package, cache, or log bundled |
| Manufacturer data sheets | Official manufacturer sites | Numeric engineering-evidence citations | Links and factual metadata only; no PDF, figure, or copied table bundled |
| LCSC/JLC supplier metadata | Provider terms apply | Optional part/supplier interoperability | No catalog or database bundled |

## Manufacturer evidence references

`src/review/component-profiles.json` links to official documents from Advanced
Monolithic Systems, Vishay, Bourns, Texas Instruments, and STMicroelectronics.
The cited numeric facts remain subject to verification against the current
official revision. The repository does not redistribute the documents.

The trace-capacity rule labels its estimate as IPC-2221-based and conservative.
It does not reproduce the standard and does not replace board-fabricator stackup,
voltage-drop, temperature-rise, or physical validation.

## Original schemas and private source provenance

The schema documents in `schemas/` are project files, not copies of the JSON
Schema specification. The staging audit traced them to the project's private
working tree, where no project-level license file was present. Their inclusion
under Apache-2.0 therefore depends on the explicit maintainer ownership gate in
`LICENSE-DECISION.md`.

## Trademarks and independence

Names and marks belong to their respective rights holders. References are for
interoperability and identification. This repository is independent and does
not claim endorsement or certification by those parties.

## Dependency update rule

If a future release adds a package or bundled asset, record its exact version,
source URL, SPDX license, purpose, distribution status, modifications, and
license-text location. Material with unknown or incompatible terms does not
enter a release candidate.
