# Contributing

Contributions should strengthen the quality gate without expanding claims beyond evidence.

## Good contribution areas

- deterministic review rules with boundary tests;
- sanitized synthetic fixtures;
- component profiles with official-source provenance;
- evidence schemas and validation;
- report clarity and localization;
- adapter-neutral persistence and compensation contracts;
- documentation of limitations and measured failure modes.

A live EDA adapter is a separate integration surface. Do not add workstation-specific commands, private service assumptions or opaque mutation endpoints to the portable skill.

## Development setup

Requirements: Python 3.10+; the review core uses the standard library.

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/run-evals.py
python scripts/release-verify.py --skip-integrity
python src/review/prototype_review.py `
  --input tests/review/fixtures/synthetic-safe-input.json `
  --profiles src/review/component-profiles.json `
  --output out/contributor-smoke
```

Run commands from the repository root. Generated `out/` content is not committed.

See [Reproducible local release](docs/reproducible-release.md) before updating
integrity files or constructing a ZIP. Run `scripts/update-integrity.py` only
after functional and privacy checks pass; build the ZIP only from a clean local
commit.

## Adding or changing a rule

Include all of the following:

1. a stable rule family and finding-ID convention;
2. explicit inputs, units, formula and boundary behavior;
3. severity and confidence rationale;
4. user-facing risk, recommendation and revalidation text;
5. a passing boundary test and a failing boundary test;
6. a fixture showing that unrelated rule families do not regress;
7. documentation updates in [Review model](docs/review-model.md).

Do not key a generic rule to a current fixture designator or product name.

## Component-profile evidence

- prefer the manufacturer and exact MPN;
- record package and pin-to-pad mapping;
- cite official document title, HTTPS URL, page/section/table and retrieval date;
- state operating conditions and confidence;
- link to the source document rather than committing its PDF;
- mark generic or estimated profiles clearly.

Procurement availability and supplier identifiers are optional evidence, not substitutes for manufacturer limits.

## Evaluation fixtures

Fixtures must declare whether they are synthetic, sanitized-derived, offline-forecast or live-save-reload-verified. Keep the minimum evidence needed for the assertion. Remove project identities, workstation paths, private logs, screenshots and internal transaction values.

Benchmark numbers must state their denominator and scope. In particular, `9/9` means that all nine predefined manual benchmark risk families were detected on the single 28-component adversarial fixture; it is not general accuracy.

Future M2 evidence must enter through the explicit, hashed and privacy-rejecting
[M2 evidence gate](docs/m2-evidence-gate.md). Gate-test fixtures with `live: true`
are synthetic branch coverage and must never be promoted as field evidence.

## Repair support

A new automatic repair status requires more than a planner or test:

- exact baseline and plan-owned objects;
- locked component, symbol, footprint, pin-to-pad and net evidence;
- complete failure compensation;
- immediate and post-reload independent readback;
- fresh ERC/connectivity/containment/DRC and Prototype review;
- a public fixture showing target improvement and no unrelated regression.

Until those gates pass, use `planned-experimental`, `prepared-not-live-verified` or `review-only` as appropriate.

## Privacy and third-party material

Before submitting a change, follow [Privacy](docs/privacy.md) and [Third-party notices](THIRD_PARTY.md). Do not commit:

- third-party Copilot source or extension packages;
- data-sheet PDFs without redistribution permission;
- credentials, cookies or authorization headers;
- private logs, conversations, screenshots or real EDA exports;
- usernames, absolute workstation paths, UUIDs, approvals, receipts or checkpoints.

## Pull-request checklist

- [ ] Scope and claims match the evidence.
- [ ] Tests and evaluation replay pass.
- [ ] JSON/YAML parse and Markdown links resolve.
- [ ] No unrelated generated artifacts are included.
- [ ] Privacy and secret scans have no unexplained high-risk hits.
- [ ] Third-party provenance and license impact are documented.
- [ ] User-facing behavior is described before internal implementation details.

By contributing, you represent that you have the right to submit the material under the repository license. See [LICENSE-DECISION.md](LICENSE-DECISION.md) for the release ownership gate.
