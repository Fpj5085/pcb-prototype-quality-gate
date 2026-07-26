# M2 evidence-gate fixtures

Everything below this directory is **synthetic test data**. The `complete/`
bundle deliberately uses positive `live` and `verified` flags so the importer's
successful branch can be tested deterministically; those flags do not describe
an M2 EDA run, a real receipt, or save/reload evidence collected from hardware
design software.

The test suite copies this seed bundle into a temporary directory, creates a
temporary SHA-256 manifest, and mutates the copy to exercise pending, missing,
hash-error, privacy-rejection, and idempotent-success branches. No file in this
fixture is eligible to change an eval's `liveEdaVerified` or
`liveSaveReloadVerified` state by itself.
