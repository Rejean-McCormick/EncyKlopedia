[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

try {
    $root = Split-Path -Parent $PSCommandPath
    $runner = Join-Path $root 'DECOUVRIR_ARTICLES_RELIES_V28.ps1'
    $csv = Join-Path $root 'tools\unesco_pilot\v28_data\DECISIONS_ARTICLES_RELIES_V28_1500.csv'
    $expectedSha256 = '998218481a532a8fb1dddbaba7730d12eb382014914c61a7726295c6261cd8cb'

    if (-not (Test-Path -LiteralPath $runner -PathType Leaf)) {
        throw 'Lanceur DECOUVRIR_ARTICLES_RELIES_V28.ps1 absent : overlay v28.1 requis.'
    }
    if (-not (Test-Path -LiteralPath $csv -PathType Leaf)) {
        throw 'CSV de decisions introuvable dans tools\unesco_pilot\v28_data.'
    }
    $actualSha256 = (Get-FileHash -LiteralPath $csv -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualSha256 -ne $expectedSha256) {
        throw 'Integrite du CSV non conforme (SHA-256). Rien ne sera importe.'
    }
    if (-not (Get-Command -Name pwsh -CommandType Application -ErrorAction SilentlyContinue)) {
        throw 'PowerShell 7 (pwsh) introuvable.'
    }

    Write-Host 'V28_REVUE_1500 : 1/3 Precontrole (aucune modification)' -ForegroundColor Cyan
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $runner -Action Apply -DecisionsFile $csv -DryRun
    if ($LASTEXITCODE -ne 0) {
        throw 'Le precontrole v28 a refuse le CSV. Catalogue inchange.'
    }

    Write-Host 'V28_REVUE_1500 : 2/3 Integration des decisions approuvees' -ForegroundColor Cyan
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $runner -Action Apply -DecisionsFile $csv
    if ($LASTEXITCODE -ne 0) {
        throw 'L integration v28 a ete refusee. Examiner le journal ci-dessus.'
    }

    Write-Host 'V28_REVUE_1500 : 3/3 Statut' -ForegroundColor Cyan
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $runner -Action Status
    if ($LASTEXITCODE -ne 0) {
        throw 'Import termine mais impossible de confirmer le statut : consulter le journal.'
    }

    Write-Host 'V28_REVUE_1500_OK' -ForegroundColor Green
    exit 0
}
catch {
    Write-Host "V28_REVUE_1500_REFUSEE : $($_.Exception.Message)" -ForegroundColor Red
    exit 2
}
