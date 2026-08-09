# Installation and removal

v0.1.3-alpha has five usable surfaces:

1. the offline Prototype review CLI, which runs without JLCEDA;
2. the fail-closed `ADD_LOCAL_BYPASS_CAP` repair-plan CLI, which emits an immutable public plan without private EDA IDs;
3. the adapter-neutral offline review Pipeline;
4. the strict read-only Adapter Envelope assembler and health validator for separately audited environment integrations;
5. a Codex plugin/skill that explains the governed workflow and invokes the offline review when normalized evidence is available.

Live EDA collection or mutation requires a separately installed and audited environment adapter. This repository does not bundle one and does not install any workstation service.

## Verify the release archive

After extracting the local release package, compare its digest with the published candidate checksum:

```powershell
Get-FileHash ./pcb-prototype-quality-gate-v0.1.3-alpha.zip -Algorithm SHA256
```

Then compare repository files with `SHA256SUMS.txt` before running them.

## Offline review CLI

Requirements:

- Python 3.10 or later;
- no Python packages beyond the standard library;
- PowerShell only if using the convenience wrapper.

From the repository root:

```powershell
python src/review/prototype_review.py `
  --input tests/review/fixtures/synthetic-safe-input.json `
  --profiles src/review/component-profiles.json `
  --output out/synthetic-safe
```

Or use the wrapper:

```powershell
./scripts/prototype-review.ps1 `
  -InputPath tests/review/fixtures/synthetic-safe-input.json `
  -OutputDirectory out/synthetic-safe
```

Run the test and evaluation gates described in [CONTRIBUTING.md](CONTRIBUTING.md) before changing rules or profiles.

The M2 evidence importer and release verification tools also use only the Python
standard library. Their commands and trust boundaries are documented in
[M2 evidence gate](docs/m2-evidence-gate.md) and
[Reproducible local release](docs/reproducible-release.md).

## Local Codex plugin

Codex installs plugins from a configured marketplace. The release archive is plugin source; it does not edit a user's marketplace configuration.

Prepare a local marketplace with this layout:

```text
<marketplace-root>/
├── .agents/plugins/marketplace.json
└── plugins/
    └── codex-jlceda-hardware-agent/
        ├── .codex-plugin/plugin.json
        ├── skills/
        ├── src/
        └── ...
```

Place the extracted repository contents in the plugin directory shown above. A minimal marketplace entry is:

```json
{
  "name": "local-hardware",
  "interface": {
    "displayName": "Local Hardware Tools"
  },
  "plugins": [
    {
      "name": "codex-jlceda-hardware-agent",
      "source": {
        "source": "local",
        "path": "./plugins/codex-jlceda-hardware-agent"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Developer Tools"
    }
  ]
}
```

Register and install it:

```text
codex plugin marketplace add <marketplace-root>
codex plugin add codex-jlceda-hardware-agent@local-hardware
```

Start a new Codex task after installation so the skill is loaded from a clean task boundary.

## Remove

Remove the plugin:

```text
codex plugin remove codex-jlceda-hardware-agent@local-hardware
```

If the local marketplace is no longer needed:

```text
codex plugin marketplace remove local-hardware
```

Deleting the local source directory is a separate manual action. Removal does not touch EDA projects, services or third-party extensions.

## Update a local candidate

Replace the plugin source only after reviewing the new `SHA256SUMS.txt`, then reinstall from the same local marketplace. Do not combine two different candidate trees or copy private adapter state into the public plugin directory.

## Live EDA integration

The public plugin contains no default MCP server, application manifest or workstation wrapper. An organization may connect an audited adapter that produces the normalized evidence described in [Evidence schema](docs/evidence-schema.md). Read-only review remains usable without that integration; live mutation support must be evaluated separately against [Supported repairs](docs/supported-repairs.md).
