# Third-party notices

The staged v0.1.0-alpha candidate does **not** vendor a third-party runtime
dependency. The offline review engine uses only the Python standard library.
The items below are user-provided tools, public conventions, interoperability
names, specifications, or engineering-evidence references.

| Item | Source/status | Use in this project | Distributed in this repository? |
| --- | --- | --- | --- |
| Apache License 2.0 | Apache Software Foundation standard license text | Proposed license for project-owned material | The standard text is intentionally included as root `LICENSE`; no Apache software is bundled |
| Python | Python Software Foundation; Python 3.10+ expected | Runs the offline review engine and tests | No interpreter or standard-library source bundled |
| PowerShell | Microsoft; optional user-provided shell | Runs the convenience wrapper | No PowerShell runtime or module bundled |
| Git and GitHub | Git project / GitHub, Inc.; local tool and possible future host | Local version control and publication wording | No Git software, GitHub service content, or repository action bundled |
| JSON Schema | Public specification; 2020-12 meta-schema URI referenced | Declares data-contract vocabulary | No specification text or validator bundled; repository schemas are project files |
| YAML and Markdown | Public data/markup formats | Stores one host configuration and project documentation | No parser, renderer, or specification text bundled |
| Mermaid | Renderer-provided diagram syntax | Embeds original project architecture diagrams in Markdown | No Mermaid runtime or copied example bundled |
| Keep a Changelog | Public changelog convention linked from `CHANGELOG.md` | Inspires the section layout; the introduction and release entries use project-authored wording | Link/reference only; no template prose or implementation bundled |
| Semantic Versioning | Public versioning convention referenced in `CHANGELOG.md` | Supplies the version-label convention | Name/reference only; no specification prose or implementation bundled |
| IPC-2221 | IPC copyrighted standard referenced by name | Supplies commonly published empirical coefficients for a conservative external-trace screening estimate | No standard prose, table, or figure bundled; not represented as certification or authoritative compliance |
| OpenAI Codex | Optional user-provided host environment and interoperability vocabulary | Loads the project-authored plugin/skill files | No OpenAI software, validator, schema, or documentation asset bundled |
| JLCEDA / 嘉立创EDA / EasyEDA | Proprietary user-provided application | Optional live EDA integration boundary | No application code, gateway, catalog, or project file bundled |
| EasyEDA Copilot | Optional third-party draft adapter | Historical/optional draft-generation reference | No source, binary, extension package, cache, or log bundled |
| Manufacturer data sheets | Official manufacturer sites | Numeric engineering-evidence citations | Links and factual metadata only; no PDF, figure, or copied table bundled |
| LCSC/JLC supplier metadata | Provider terms apply | Optional part/supplier interoperability | No catalog or database bundled |
| Generic module and package identifiers | Names such as HC-05, HC-SR04, C0805, and descriptive package strings | Sanitized fixture identification and compatibility checks | No symbol artwork, footprint geometry, library record, or supplier database bundled |

## Manufacturer evidence references

`src/review/component-profiles.json` links to official documents from Advanced
Monolithic Systems, Vishay, Bourns, Texas Instruments, and STMicroelectronics.
Manufacturer names, MPNs, short document titles, package identifiers, and cited
numeric facts are used as factual/nominative evidence. The cited facts remain
subject to verification against the current official revision. The repository
does not redistribute the documents, copied prose, drawings, tables, or package
geometry. The word `Arm` appears only inside a cited manufacturer document
title and remains a mark of its respective rights holder.

The trace-capacity rule implements a commonly published empirical equation with
IPC-2221 coefficients and labels the result conservative. The equation and
numeric coefficients are treated as functional facts, not as a redistribution
of the standard. The project does not reproduce standard prose, tables, figures,
or acceptance criteria, and the estimate does not replace an authorized copy of
the standard, board-fabricator stackup, voltage-drop analysis, temperature-rise
analysis, or physical validation.

## Interface and example-data boundary

The `.codex-plugin` layout, `agents/openai.yaml`, JLCEDA/EasyEDA names, and
normalized fields such as `projectUuid` are used for interoperability. The
repository does not copy a host SDK, vendor API implementation, official schema,
or validator. Reserved `.invalid` schema identifiers are local project
identifiers and are not vendor endpoints.

Evaluation inputs are project-authored synthetic data or a sanitized-derived
adversarial replay. Short component names, net names, pin labels, package names,
and MPNs are functional facts. The fixtures contain no component-library UUID,
catalog record, symbol graphic, footprint geometry, screenshot, or raw project
export. The sanitized-derived fixture remains subject to the maintainer ownership
attestation even though its private identifiers were removed.

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

No third-party NOTICE file is required by a bundled dependency because there is
no bundled dependency. This file records reference-only attributions and does
not grant rights in third-party marks, software, standards, or documentation.

## Dependency update rule

If a future release adds a package or bundled asset, record its exact version,
source URL, SPDX license, purpose, distribution status, modifications, and
license-text location. Material with unknown or incompatible terms does not
enter a release candidate.
