param(
    [Parameter(Mandatory = $true)][string]$InputPath,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [string]$ProfilesPath
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$engine = Join-Path $repoRoot 'src/review/prototype_review.py'
if (-not $ProfilesPath) {
    $ProfilesPath = Join-Path $repoRoot 'src/review/component-profiles.json'
}

python $engine --input $InputPath --profiles $ProfilesPath --output $OutputDirectory
exit $LASTEXITCODE
