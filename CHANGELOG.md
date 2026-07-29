# Project release history

This project-authored history records release-relevant changes. Its section
layout is inspired by [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and version labels follow Semantic Versioning conventions.

## [Unreleased]

### Added

- three original synthetic BEFORE/AFTER benchmark pairs for power input, sensor interface and low-speed communication, with fixture-scoped expected findings and zero-write execution metadata;
- deterministic tests for BEFORE risk detection, AFTER engineering forecasts, input-order stability and explicit non-manufacturing/non-mutation boundaries;
- deterministic, network-free component-profile provenance and freshness audit with an explicit reproducible as-of date;
- fail-closed checks for missing provenance, invalid or future dates, stale sources, official HTTPS links and declared synthetic origin;
- profile metadata and schema constraints for source type, document revision, retrieval date and review interval;
- fail-closed normalized-input validation for non-finite numbers, boolean-as-number values, missing calculation operands, inverted physical ranges and malformed optional containers;
- profile-bounded finding confidence and top-level retention of explicitly declared assumptions, including assumptions attached to passing rules;
- adapter-neutral offline pipeline entry for normalized input → independent review → optional immutable repair-plan preview, with explicit zero-write receipt and regression coverage.

### Compatibility

- the audit is an independent release/CI gate and does not change the public three-value Prototype rating enum;
- no EDA mutation capability or repair family was added.

## [0.1.1-alpha] - 2026-07-28

Status: published as a GitHub prerelease; the remote main branch and tag point to the verified release commit.

### Added

- independent M3 NOT FOR MANUFACTURING sensor-adapter BEFORE→`ADD_LOCAL_BYPASS_CAP`→AFTER live repetition;
- gate-generated, privacy-minimized M3 public evidence summary;
- persisted schematic and PCB proof for locked `CL21B104KBCNNNC` near J2, including fresh ERC, connectivity, containment and strict DRC checks.

### Changed

- roadmap now records M3 repetition complete while keeping the public repair allow-list limited to `ADD_LOCAL_BYPASS_CAP`;
- repeatability wording is limited to two fixture-scoped live closures and does not imply general autonomous layout or Manufacturing Release.


### Added

- deterministic, fail-closed `ADD_LOCAL_BYPASS_CAP` repair-plan CLI and schema;
- tests for missing evidence, failed gates, multiple/unknown findings, uncertain networks, existing bypass rejection and idempotent output.

### Planned

- publish additional fixture-scoped benchmarks;
- graduate repair families only after their public persistence and regression gates pass.

## [0.1.0-alpha] - 2026-07-26

Status: local release candidate; no GitHub publication is implied by this entry.

### Added

- deterministic, standard-library Prototype review engine;
- component-profile evidence and normalized input/output contracts;
- Draft, Prototype and Manufacturing Release governance model;
- machine-stable three-level rating with explainable Chinese findings;
- synthetic safe fixture and 28-component adversarial fixture;
- offline 5 V / 1 A distribution-board BEFORE/AFTER successor evaluation;
- bounded repair allow-list and save/close/reload revalidation policy;
- portable Codex plugin and `jlceda-hardware-design` skill structure;
- architecture, evidence, privacy, security, limitations and demo documentation;
- deterministic M2 sanitized-evidence import gate with pending, hash, privacy and idempotence tests;
- reproducible integrity generation, repository verification and Git-tree ZIP builder;
- per-file provenance inventory and expanded third-party/source boundary.

### Changed

- Prototype readiness now fails closed when any of the six required EDA gate fields is missing, malformed or contradicted by live/persistence metadata;
- strict current-state `rating` is separated from `engineeringForecastRating`, while the original three-value rating enum remains stable;
- M2 AFTER and offline synthetic evals remain evidence-pending instead of presenting an offline prediction as current sample readiness.

### Evidence boundaries

- the adversarial `9/9` result is limited to nine predefined human-benchmark risk families on one fixture;
- the M2 AFTER engineering forecast is separate from its strict evidence-pending rating until real save/reload proof exists;
- live EDA adapters, third-party draft generators and manufacturing workflows are not bundled;
- no general autonomous repair or Manufacturing Release capability is claimed.
