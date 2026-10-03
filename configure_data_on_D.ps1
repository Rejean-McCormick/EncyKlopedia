[CmdletBinding()]
param(
    [string]$CRoot = 'C:\mycode\EncyKlopedia\EncyKlopedia',
    [string]$DRoot = 'D:\EncyKlopedia',
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
$CRoot = [IO.Path]::GetFullPath($CRoot).TrimEnd('\\')
$DRoot = [IO.Path]::GetFullPath($DRoot).TrimEnd('\\')
if (-not (Test-Path -LiteralPath $CRoot -PathType Container)) { throw "CRoot introuvable: $CRoot" }
if (-not (Test-Path -LiteralPath $DRoot -PathType Container)) { throw "DRoot introuvable: $DRoot" }
if (-not (Test-Path -LiteralPath (Join-Path $CRoot '00_system'))) { throw 'CRoot ne ressemble pas à EncyKlopedia.' }
if (-not (Test-Path -LiteralPath (Join-Path $DRoot '10_sources'))) { throw 'DRoot ne contient pas les zones de données attendues.' }

$links = @(
 '10_sources\lexical',
 '10_sources\wikidata\dumps',
 '20_evidence\acquisition-snapshots',
 '20_evidence\scope-snapshots',
 '20_evidence\handoffs',
 '30_working',
 '90_runtime\checkpoints'
)

function Is-JunctionTo([string]$Path,[string]$Target) {
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    $i=Get-Item -LiteralPath $Path -Force
    if (-not ($i.Attributes -band [IO.FileAttributes]::ReparsePoint)) { return $false }
    $targets=@($i.Target) | ForEach-Object { [IO.Path]::GetFullPath("$_").TrimEnd('\\') }
    return $targets -contains ([IO.Path]::GetFullPath($Target).TrimEnd('\\'))
}

function Prepare-Destination([string]$Dest,[string]$Source,[string]$Rel) {
    if (-not (Test-Path -LiteralPath $Dest)) { return }
    if (Is-JunctionTo $Dest $Source) { return }
    $item=Get-Item -LiteralPath $Dest -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Junction existante vers une autre cible: $Dest" }
    $children=@(Get-ChildItem -LiteralPath $Dest -Force)
    $allowed=$children | Where-Object { $_.Name -ne 'README.md' }
    if ($allowed.Count -gt 0) { throw "Refus: données locales présentes sur C dans $Rel. Déplacer/fusionner avant de créer la junction." }
    $readme=Join-Path $Dest 'README.md'
    if (Test-Path -LiteralPath $readme) {
        New-Item -ItemType Directory -Path $Source -Force | Out-Null
        Copy-Item -LiteralPath $readme -Destination (Join-Path $Source 'README.md') -Force
    }
    Remove-Item -LiteralPath $Dest -Force -Recurse
}

Write-Host "C canonique : $CRoot"
Write-Host "D données    : $DRoot"
Write-Host ($(if($Apply){'MODE: APPLICATION'}else{'MODE: APERÇU seulement — relancer avec -Apply'}))
foreach($rel in $links) {
    $src=Join-Path $DRoot $rel; $dst=Join-Path $CRoot $rel
    if (-not (Test-Path -LiteralPath $src -PathType Container)) { Write-Host "[SKIP absent D] $rel"; continue }
    if (Is-JunctionTo $dst $src) { Write-Host "[OK déjà lié] $rel"; continue }
    Write-Host "[LINK] $dst -> $src"
    if (-not $Apply) { continue }
    $parent=Split-Path -Parent $dst; New-Item -ItemType Directory -Path $parent -Force | Out-Null
    Prepare-Destination $dst $src $rel
    if (-not (Test-Path -LiteralPath $dst)) { New-Item -ItemType Junction -Path $dst -Target $src | Out-Null }
}
if ($Apply) { Write-Host 'Junctions configurées. Le code reste sur C; les zones lourdes restent sur D.' }
