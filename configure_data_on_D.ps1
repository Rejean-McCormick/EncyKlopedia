#requires -Version 7.0
<#
 EncyK v0.13.4 — associer les données sans déplacer le code.
 Le dépôt Git est toujours le répertoire qui contient CE script.
 Par défaut : aperçu seulement. -Apply pour créer les jonctions.
 Ne supprime jamais de fichier ni ne copie de dump ou de SQLite.
#>
[CmdletBinding()]
param(
    [string]$CodeRoot = '',
    [string]$DataRoot = 'D:\EncyKlopedia',
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($CodeRoot)) { $CodeRoot = $PSScriptRoot }
$CodeRoot = [IO.Path]::GetFullPath($CodeRoot).TrimEnd('\')
$DataRoot = [IO.Path]::GetFullPath($DataRoot).TrimEnd('\')
if ($CodeRoot -eq $DataRoot -or $DataRoot.StartsWith($CodeRoot+'\',[StringComparison]::OrdinalIgnoreCase) -or $CodeRoot.StartsWith($DataRoot+'\',[StringComparison]::OrdinalIgnoreCase)) {
    throw 'Les deux racines doivent être distinctes et non imbriquées.'
}
if (-not (Test-Path -LiteralPath (Join-Path $CodeRoot '00_system') -PathType Container)) { throw 'Racine de code EncyK invalide : 00_system manquant.' }
if (-not (Test-Path -LiteralPath (Join-Path $DataRoot '10_sources') -PathType Container)) { throw 'Racine des données invalide : 10_sources manquant.' }
foreach ($base in @($CodeRoot, $DataRoot)) {
    if ((Get-Item -LiteralPath $base -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Refus d'une racine redirigée : $base" }
}

# Les seeds restent dans le dépôt. Toutes les zones dynamiques ci-dessous vont sur D:.
$links = @(
    '10_sources\lexical',
    '10_sources\wikidata\dumps',
    '20_evidence',
    '30_working',
    '90_runtime'
)
function IsCorrectJunction([string]$link,[string]$target) {
    if (-not (Test-Path -LiteralPath $link)) { return $false }
    $i = Get-Item -LiteralPath $link -Force
    if (-not ($i.Attributes -band [IO.FileAttributes]::ReparsePoint)) { return $false }
    foreach ($t in @($i.Target)) {
        if ([IO.Path]::GetFullPath([string]$t).TrimEnd('\') -ieq [IO.Path]::GetFullPath($target).TrimEnd('\')) { return $true }
    }
    return $false
}
Write-Host "Code (Git) : $CodeRoot" -ForegroundColor Cyan
Write-Host "Données     : $DataRoot" -ForegroundColor Cyan
Write-Host $(if ($Apply) {'MODE APPLICATION — seulement les jonctions autorisées'} else {'MODE APERCU (sans modification)'} )
$blockers = @()
foreach ($rel in $links) {
    $code = Join-Path $CodeRoot $rel
    $data = Join-Path $DataRoot $rel
    if (IsCorrectJunction $code $data) { Write-Host "[OK] $rel déjà lié"; continue }
    if (Test-Path -LiteralPath $code) {
        $item = Get-Item -LiteralPath $code -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { $blockers += "Liaison existante différente : $code"; continue }
        if (-not $item.PSIsContainer) { $blockers += "Fichier bloquant : $code"; continue }
        if (@(Get-ChildItem -LiteralPath $code -Force).Count -gt 0) {
            $blockers += "Dossier NON VIDE du dépôt, refus : $code"; continue
        }
    }
    if (Test-Path -LiteralPath $data) {
        $info = Get-Item -LiteralPath $data -Force
        if (-not $info.PSIsContainer -or ($info.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            $blockers += "Cible D invalide ou redirigée : $data"; continue
        }
    }
    Write-Host "[PLAN] $code -> $data"
    if (-not $Apply) { continue }
    if (-not (Test-Path -LiteralPath $data)) { New-Item -ItemType Directory -Path $data -Force | Out-Null }
    $parent = Split-Path -Parent $code
    if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    if (Test-Path -LiteralPath $code) {
        # Suppression du dossier VIDE seulement ; aucun fichier n'est touché.
        Remove-Item -LiteralPath $code -Force
    }
    New-Item -ItemType Junction -Path $code -Target $data -ErrorAction Stop | Out-Null
}
if ($blockers.Count) {
    foreach ($b in $blockers) { Write-Warning $b }
    throw "Configuration incomplète : $($blockers.Count) blocage(s). Résoudre manuellement, ne supprimer aucune donnée."
}
Write-Host $(if ($Apply) {'Jonctions configurées. Aucun dump déplacé.'} else {'Aperçu terminé. Relancer avec -Apply pour configurer.'}) -ForegroundColor Green
