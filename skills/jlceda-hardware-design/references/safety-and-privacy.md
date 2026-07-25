# Safety and privacy

- Treat live EDA mutations as high-impact operations even on a prototype fixture.
- Bind reads and writes to the intended design and current document through the adapter.
- On timeout or ambiguous acknowledgement, read back first and do not automatically repeat the mutation.
- Keep original artifacts recoverable and verify restoration after save/reload.
- Exclude absolute paths, usernames, project identities, internal object IDs, approvals, receipts, checkpoints, private logs and screenshots from public evidence.
- Exclude third-party source code, EDA extension packages and data-sheet PDFs unless their licenses explicitly permit redistribution and the release records that permission.
- A software rating does not replace physical power-up, load, thermal, EMC, mechanical or environmental testing.
