# Security policy

## Supported version

`0.1.0-alpha` is a pre-release evaluation candidate. Security and privacy fixes
may be applied only to the latest alpha revision.

## Reporting

Use the repository host's private security-advisory feature. Do not put live
project files, credentials, private logs, screenshots, or third-party extension
packages in a public issue. Prefer a minimal synthetic reproduction.

## High-impact integration boundary

Live EDA mutation adapters are high-impact integrations. A compliant adapter
should:

- bind to the intended current document;
- use an exact baseline and immutable allow-listed plan;
- distinguish acknowledgement from verified readback;
- avoid automatic mutation retry after timeout or unknown state;
- retain a complete compensation path before cross-document mutation;
- verify save, close, reload, and current-state readback;
- re-run ERC, connectivity, containment, DRC, and engineering review;
- keep upload, ordering, payment, and manufacturing outside this alpha.

The staged alpha does not bundle a live mutation bridge or approval service.

## Public-release privacy gate

A release must contain no concrete live values for:

- API keys, access or refresh tokens, passwords, authorization headers, cookies,
  or private keys;
- workstation paths, usernames, machine names, ports, process details, or
  private service endpoints;
- project, page, object, library, or device identifiers;
- approval identifiers, transaction receipts, checkpoints, nonces, or runtime
  state;
- private logs, conversations, screenshots, or raw EDA project identity.

It must also contain no extension package, third-party source archive,
data-sheet PDF, vendored catalog, unexplained executable/archive, generated
binary cache, or undocumented large file.

Schema property names and security-policy vocabulary are not concrete secrets.
They remain scanner findings and require the narrow classifications recorded in
`release-audit/PRIVACY-SCAN-ALLOWLIST.json`.

See [PRIVACY-SCAN.md](PRIVACY-SCAN.md) and
[RELEASE-CHECKLIST.md](RELEASE-CHECKLIST.md) before a public tag.
