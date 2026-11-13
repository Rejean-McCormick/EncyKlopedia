[CmdletBinding()]
param([switch]$InstallOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'

$repo = Split-Path -Parent $PSCommandPath
$payload = Join-Path $repo 'OVERLAY_CONTEXTE_UNESCO_V28'
$mainRel = 'tools\unesco_pilot\poste_chatgpt_v30.py'
$newRel = 'tools\unesco_pilot\contexte_revue_unesco_v28.py'
$files = @(
  @{ Rel=$mainRel; Old='9c9df40f755791854685387c98862277726b1fb8979d936631e8f1679f47fbdb'; New='76905995eb9b0039ce0458083c3f3d7e2796ec297d7475bf340f965cf6daaf97'; Required=$true },
  @{ Rel=$newRel; Old=''; New='886904873554df47f4f593f7e1f39346946ebd7ba02710e0146cf73aae3ba46a'; Required=$false }
)
function HashFile([string]$path) {
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return '' }
  return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
}
try {
  Write-Host '=== ENCYKLOPEDIA — CONTEXTE DOCUMENTAIRE UNESCO V28 ===' -ForegroundColor Cyan
  Write-Host 'Fermer le poste ChatGPT v30 avant cette installation.'
  $changes=@()
  foreach ($item in $files) {
    $src=Join-Path $payload $item.Rel
    $dst=Join-Path $repo $item.Rel
    if (-not (Test-Path -LiteralPath $src -PathType Leaf)) { throw "Fichier source de l overlay absent : $src" }
    if ((HashFile $src) -ne $item.New) { throw "Empreinte de l overlay incorrecte : $($item.Rel)" }
    $actual=HashFile $dst
    if ($actual -eq $item.New) {
      Write-Host "Déjà installé : $($item.Rel)" -ForegroundColor DarkGreen
      continue
    }
    if (($item.Required -and $actual -ne $item.Old) -or (-not $item.Required -and $actual -ne '')) {
      throw "Le fichier local a changé depuis le snapshot : $dst. Aucun remplacement automatique."
    }
    $changes+=@{ src=$src;dst=$dst;rel=$item.Rel;exists=($actual -ne '');sha=$item.New }
  }
  if ($changes.Count -gt 0) {
    $stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
    $backupRoot=Join-Path $repo ('_SAUVEGARDES_CODE_CONTEXTE_V28\'+$stamp)
    foreach ($f in $changes) {
      if ($f.exists) {
        $bak=Join-Path $backupRoot $f.rel
        New-Item -ItemType Directory -Force -Path (Split-Path $bak -Parent) | Out-Null
        Copy-Item -LiteralPath $f.dst -Destination $bak -ErrorAction Stop
        if (-not (Test-Path -LiteralPath $bak -PathType Leaf)) { throw "Sauvegarde impossible : $bak" }
      }
    }
    $done=@()
    try {
      foreach ($f in $changes) {
        New-Item -ItemType Directory -Force -Path (Split-Path $f.dst -Parent) | Out-Null
        $temp=$f.dst+'.INSTALLATION_TEMPORAIRE_'+[guid]::NewGuid().ToString('N')
        try {
          Copy-Item -LiteralPath $f.src -Destination $temp -ErrorAction Stop
          [System.IO.File]::Move($temp,$f.dst,$true)
        } finally {
          if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force }
        }
        $done+=,$f
        if ((HashFile $f.dst) -ne $f.sha) { throw "Empreinte incorrecte apres copie : $($f.rel)" }
        Write-Host "Installé : $($f.rel)" -ForegroundColor Green
      }
    } catch {
      Write-Host 'Erreur : retour arriere du code installe en cours.' -ForegroundColor Yellow
      $reverse = @($done)
      [array]::Reverse($reverse)
      foreach ($f in $reverse) {
        if ($f.exists) {
          Copy-Item -LiteralPath (Join-Path $backupRoot $f.rel) -Destination $f.dst -Force -ErrorAction Stop
        } elseif (Test-Path -LiteralPath $f.dst) {
          Remove-Item -LiteralPath $f.dst -Force -ErrorAction Stop
        }
      }
      throw
    }
    Write-Host "Sauvegardes du code : $backupRoot"
  } else {
    Write-Host 'Déjà à jour : aucun code remplacé.' -ForegroundColor Green
  }
  $xml='D:\EncyKlopedia\30_working\wikipedia_en_uncompressed\enwiki-latest-pages-articles-multistream.xml'
  $index='D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en_direct_pages_v21.sqlite'
  if ((Test-Path -LiteralPath $xml -PathType Leaf) -and (Test-Path -LiteralPath $index -PathType Leaf)) {
    Write-Host 'XML Wikipédia et index v21 présents : les extraits pourront être vérifiés lors du téléchargement.' -ForegroundColor Green
  } else {
    Write-Host 'ATTENTION : XML ou index v21 absent. Packs enrichis avec notes UNESCO/liens, sans extraits XML.' -ForegroundColor Yellow
  }
  Write-Host 'Bases et tâches v25/v27/v28/v30 : aucun reset ni migration.' -ForegroundColor Cyan
  if (-not $InstallOnly) {
    Write-Host 'Démarrage du poste v30...' -ForegroundColor Cyan
    & (Join-Path $repo 'LANCER_POSTE_CHATGPT_V30.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'Le poste v30 a retourné une erreur' }
  }
} catch {
  Write-Host "INSTALLATION_REFUSEE : $($_.Exception.Message)" -ForegroundColor Red
  exit 2
}
