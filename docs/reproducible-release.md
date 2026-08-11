# Reproducible local release

The release scripts keep integrity generation, repository validation and ZIP
construction deterministic. They operate only on the local candidate and do not
publish or upload anything.

## 1. Functional gates

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/run-evals.py
python src/review/component_profile_audit.py `
  --profiles src/review/component-profiles.json `
  --as-of 2026-07-29
python scripts/release-verify.py --skip-integrity
```

The component-profile command is a deterministic, network-free provenance and
freshness gate. It fails closed for missing, invalid, future-dated or stale
metadata. The last command checks UTF-8, JSON, the package's restricted YAML
subset, Python syntax, Markdown links, plugin/skill structure, privacy patterns,
forbidden file classes, symbolic links and the 1 MiB size limit.

## 2. Integrity files

After all public files are final and generated caches have been removed:

```powershell
python scripts/update-integrity.py
python scripts/update-integrity.py
```

The second run must report both `manifestChanged: false` and
`sumsChanged: false`. `FILE-MANIFEST.json` omits wall-clock time and excludes its
own bytes plus `SHA256SUMS.txt`, so the same tree produces the same output.

Run the complete repository gate:

```powershell
python scripts/release-verify.py
```

## 3. Commit and archive

Commit the reviewed tree locally, confirm it is clean, then build from Git
objects rather than mutable working-tree files:

```powershell
git status --short
python scripts/build-release.py
python scripts/release-verify.py `
  --archive ../pcb-prototype-quality-gate-v0.1.4-alpha.zip
```

The builder sorts paths, stores every committed blob under one top-level
directory, uses a fixed ZIP timestamp and writes files without compression.
Those choices make repeated builds from the same commit byte-identical. It also
writes a neighboring `.zip.sha256` sidecar and reads every archive member back
against the committed Git blob.

## External validators

The Codex plugin and skill validators and a Draft 2020-12 JSON Schema validator
remain separate release-environment checks. Their versions and results belong in
`TEST-REPORT.md`; validator implementations are not bundled as runtime
dependencies.
