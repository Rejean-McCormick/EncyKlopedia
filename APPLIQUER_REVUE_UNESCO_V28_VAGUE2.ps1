[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

try {
    $root = Split-Path -Parent $PSCommandPath
    $runner = Join-Path $root 'DECOUVRIR_ARTICLES_RELIES_V28.ps1'
    $csv = Join-Path $root 'tools\unesco_pilot\v28_data\DECISIONS_ARTICLES_RELIES_V28_VAGUE2_1500.csv'
    $expectedHash = 'b22be4deeda96627df084b314cd037d462ec7d9db5cde3e8d10142c8cb2f1f5a'
    if (-not (Test-Path -LiteralPath $runner -PathType Leaf)) { throw 'Moteur v28 absent.' }
    if (-not (Test-Path -LiteralPath $csv -PathType Leaf)) { throw 'CSV de decisions de vague 2 absent.' }
    if ((Get-FileHash -LiteralPath $csv -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) {
        throw 'CSV de decisions modifie ou incomplet : aucune integration autorisee.'
    }
    if (-not (Get-Command -Name pwsh -CommandType Application -ErrorAction SilentlyContinue)) {
        throw 'PowerShell 7 est requis.'
    }

    Write-Host 'V28_VAGUE2 : 1/3 Verification des decisions (lecture seule)' -ForegroundColor Cyan
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $runner -Action Apply -DecisionsFile $csv -DryRun
    if ($LASTEXITCODE -ne 0) { throw 'Precontrole refuse. Catalogue inchange.' }

    Write-Host 'V28_VAGUE2 : 2/3 Integration incrementale' -ForegroundColor Cyan
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $runner -Action Apply -DecisionsFile $csv
    if ($LASTEXITCODE -ne 0) { throw 'Integration refusee : consulter le diagnostic ci-dessus.' }

    Write-Host 'V28_VAGUE2 : 3/3 Statut de la decouverte' -ForegroundColor Cyan
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $runner -Action Status
    if ($LASTEXITCODE -ne 0) { throw 'Impossible de confirmer le statut.' }

    Write-Host 'V28_VAGUE2_OK' -ForegroundColor Green
    exit 0
}
catch {
    Write-Host "V28_VAGUE2_REFUSEE : $($_.Exception.Message)" -ForegroundColor Red
    exit 2
}
