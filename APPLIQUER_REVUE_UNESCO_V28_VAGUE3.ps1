[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

try {
    $root = Split-Path -Parent $PSCommandPath
    $runner = Join-Path $root 'DECOUVRIR_ARTICLES_RELIES_V28.ps1'
    $csv = Join-Path $root 'tools\unesco_pilot\v28_data\DECISIONS_ARTICLES_RELIES_V28_VAGUE3_1500.csv'
    $expectedSha256 = 'e830ffcc1b559f2cbcb1787232f69c4fc2ee515d9f6e750776203158a08553f9'

    if (-not (Test-Path -LiteralPath $runner -PathType Leaf)) {
        throw 'Moteur v28 introuvable a la racine.'
    }
    if (-not (Test-Path -LiteralPath $csv -PathType Leaf)) {
        throw 'CSV de revue v28 vague 3 introuvable dans tools\unesco_pilot\v28_data.'
    }
    if (-not (Get-Command -Name pwsh -CommandType Application -ErrorAction SilentlyContinue)) {
        throw 'PowerShell 7 (pwsh) est requis.'
    }
    $actualSha256 = (Get-FileHash -LiteralPath $csv -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualSha256 -ne $expectedSha256) {
        throw 'Controle SHA-256 du fichier de decisions refuse. Aucune integration.'
    }

    Write-Host 'V28_VAGUE3 : 1/3 Precontrole (sans modification)' -ForegroundColor Cyan
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $runner -Action Apply -DecisionsFile $csv -DryRun
    if ($LASTEXITCODE -ne 0) { throw 'Precontrole v28 refuse : consulter la sortie.' }

    Write-Host 'V28_VAGUE3 : 2/3 Integration incrementale des decisions' -ForegroundColor Cyan
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $runner -Action Apply -DecisionsFile $csv
    if ($LASTEXITCODE -ne 0) { throw 'Integration v28 refusee : consulter la sortie.' }

    Write-Host 'V28_VAGUE3 : 3/3 Statut de decouverte' -ForegroundColor Cyan
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $runner -Action Status
    if ($LASTEXITCODE -ne 0) { throw 'Verification du statut v28 impossible : consulter la sortie.' }

    Write-Host 'V28_VAGUE3_OK' -ForegroundColor Green
    exit 0
}
catch {
    Write-Host "V28_VAGUE3_REFUSEE : $($_.Exception.Message)" -ForegroundColor Red
    exit 2
}
