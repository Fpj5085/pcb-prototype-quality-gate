# Evidence boundary

This replay intentionally publishes no raw live evidence. The normalized `input.json` is the public test input, while `expected.json` records the fixture-scoped benchmark.

The source-to-public sanitization boundary excludes:

- real project/document/object/library identifiers;
- original EDA project files;
- screenshots and account navigation;
- private execution logs and historical conversations;
- internal approvals, receipts and checkpoints;
- bundled third-party source or data-sheet PDFs.

Future revisions may add a compact provenance statement or aggregate hash, but should not reintroduce private source material merely to make the fixture look more “real.”
