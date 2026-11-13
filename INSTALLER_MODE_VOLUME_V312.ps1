[CmdletBinding()]
param(
  [string]$Repo='C:\mycode\EncyKlopedia\EncyKlopedia',
  [string]$Python='C:\Users\rejea\AppData\Local\Programs\Python\Python312\python.exe'
)
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$manifest=Get-Content -LiteralPath (Join-Path $root 'MANIFEST_MODE_VOLUME_V312.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.format -ne 'encyklopedia.mode-volume.v31.2/1') {throw 'Manifeste de version incorrect'}
if (-not (Test-Path -LiteralPath $Repo -PathType Container)) {throw "Depot introuvable: $Repo"}
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {throw "Python introuvable: $Python"}
$seen=@{}
foreach ($f in $manifest.files) {
  $rel=[string]$f.path
  if ($rel -notmatch '^[a-zA-Z0-9_./-]+$' -or $rel.Contains('..') -or $rel.StartsWith('/')) {throw "Chemin interdit: $rel"}
  if ($seen.ContainsKey($rel.ToLowerInvariant())) {throw "Chemin double: $rel"}
  $seen[$rel.ToLowerInvariant()]=$true
  $sub=$rel.Replace('/','\')
  $from=Join-Path $root $sub
  $to=Join-Path $Repo $sub
  if (-not (Test-Path -LiteralPath $from -PathType Leaf)) {throw "Fichier manquant: $rel"}
  $srcHash=(Get-FileHash -LiteralPath $from -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($srcHash -ne [string]$f.sha256) {throw "Fichier du ZIP modifie: $rel"}
  if ($f.require_existing -and -not (Test-Path -LiteralPath $to -PathType Leaf)) {throw "Code natif absent: $rel"}
  if (Test-Path -LiteralPath $to -PathType Leaf) {
    $current=(Get-FileHash -LiteralPath $to -Algorithm SHA256).Hash.ToLowerInvariant()
    $allowed=@($f.allowed_previous_sha256)
    if ($current -ne $srcHash -and $current -notin $allowed) {throw "Version locale differente: $rel. Ne pas ecraser les modifications locales."}
  }
}
# Le module v27 est deja corrige pour XML; ce paquet ne le remplace PAS.
if (-not (Test-Path -LiteralPath (Join-Path $Repo 'tools\unesco_pilot\production_kristals_v27.py'))) {throw 'Kristal v27 manquant'}
& $Python -m compileall -q (Join-Path $root 'tools') (Join-Path $root 'tests')
if ($LASTEXITCODE -ne 0) {throw 'Compilation Python impossible'}
foreach ($f in $manifest.files) {
  $rel=[string]$f.path;$sub=$rel.Replace('/','\')
  $from=Join-Path $root $sub;$to=Join-Path $Repo $sub
  [void](New-Item -ItemType Directory -Force -Path (Split-Path -Parent $to))
  $tmp=$to+'.install_v312_tmp'
  [System.IO.File]::WriteAllBytes($tmp,[System.IO.File]::ReadAllBytes($from))
  [System.IO.File]::Move($tmp,$to,$true)
  Write-Host "INSTALLÉ: $rel"
}
$env:PYTHONPATH=Join-Path $Repo 'tools\unesco_pilot'
& $Python -m unittest discover -s (Join-Path $Repo 'tests') -p 'test_*v31*.py' -q
if ($LASTEXITCODE -ne 0) {throw "Tests v31 echoues: $LASTEXITCODE"}
Write-Host 'ENCYKLOPEDIA_MODE_VOLUME_V312_OK - 880 UNESCO / 24 articles Kristal / 80000 mots'
Write-Host 'Le poste doit etre redemarre pour charger les nouveaux reglages. Aucune tache existante modifiee.'
