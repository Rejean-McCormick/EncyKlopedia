# EncyKlopedia v27 — Lot 084–088 : un seul lancement depuis la racine du depot.
# Import cumulatif PRIVE, aucun fichier canonique modifie.
$ErrorActionPreference = 'Stop'
$repo = $PSScriptRoot
$work = 'D:\EncyKlopedia\30_working\production_kristals_v27'
$source = Join-Path $repo 'tools\unesco_pilot\v27_data\lot_084_088'
$destination = Join-Path $work 'deltas'
$engine = Join-Path $repo 'PRODUIRE_KRISTALS_V27.ps1'

try {
    if (-not (Test-Path -LiteralPath $engine -PathType Leaf)) { throw "Moteur v27 absent : $engine" }
    if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw "Dossier de deltas absent : $source" }
    $manifestFile = Join-Path $source 'MANIFEST_SHA256.json'
    if (-not (Test-Path -LiteralPath $manifestFile -PathType Leaf)) { throw 'Manifeste des empreintes absent' }
    $manifest = Get-Content -LiteralPath $manifestFile -Raw -Encoding UTF8 | ConvertFrom-Json
    Write-Host 'V27_LOT_084_088 : 1/3 Precontrole de tous les fichiers et packs'
    foreach ($entry in $manifest.files.PSObject.Properties) {
        $path = Join-Path $source $entry.Name
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Fichier manquant : $path" }
        $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne ([string]$entry.Value).ToLowerInvariant()) { throw "Empreinte du fichier incorrecte : $path" }
    }
    for ($n = 84; $n -le 88; $n++) {
        $id = '{0:D6}' -f $n
        $packName = "PACK_V27_$id.zip"
        $pack = Join-Path $work "packs\$packName"
        $delta = Join-Path $source "DELTA_KRISTAL_PACK_V27_$id.json"
        if (-not (Test-Path -LiteralPath $pack -PathType Leaf)) { throw "Pack introuvable : $pack" }
        if (-not (Test-Path -LiteralPath $delta -PathType Leaf)) { throw "Delta introuvable : $delta" }
        $expectedPack = [string]$manifest.packs.$packName
        if ([string]::IsNullOrWhiteSpace($expectedPack)) { throw "Empreinte de pack absente : $packName" }
        $actualPack = (Get-FileHash -LiteralPath $pack -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualPack -ne $expectedPack.ToLowerInvariant()) { throw "Pack source modifie : $pack" }
        $data = Get-Content -LiteralPath $delta -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($data.pack_sha256 -ne $expectedPack -or $data.pack_id -ne "PACK_V27_$id" -or $data.canonical_admissions -ne 0 -or $data.publication_authorized -ne $false) {
            throw "Delta incoherent ou pretendument canonique : $delta"
        }
        $destDelta = Join-Path $destination "DELTA_KRISTAL_PACK_V27_$id.json"
        if (Test-Path -LiteralPath $destDelta -PathType Leaf) {
            $existingHash = (Get-FileHash -LiteralPath $destDelta -Algorithm SHA256).Hash.ToLowerInvariant()
            $newHash = (Get-FileHash -LiteralPath $delta -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($existingHash -ne $newHash) { throw "Un delta different existe deja : $destDelta" }
        }
    }
    New-Item -ItemType Directory -Force -Path $destination | Out-Null
    Write-Host 'V27_LOT_084_088 : 2/3 Import cumulatif dans la base privee'
    for ($n = 84; $n -le 88; $n++) {
        $id = '{0:D6}' -f $n
        $pack = Join-Path $work "packs\PACK_V27_$id.zip"
        $deltaSource = Join-Path $source "DELTA_KRISTAL_PACK_V27_$id.json"
        $deltaDest = Join-Path $destination "DELTA_KRISTAL_PACK_V27_$id.json"
        if (-not (Test-Path -LiteralPath $deltaDest -PathType Leaf)) {
            Copy-Item -LiteralPath $deltaSource -Destination $deltaDest -ErrorAction Stop
        }
        Write-Host "V27_LOT_084_088 : import $id"
        & pwsh -NoProfile -ExecutionPolicy Bypass -File $engine -Action Import -Pack $pack -Delta $deltaDest
        if ($LASTEXITCODE -ne 0) { throw "Echec d'import du pack $id (code $LASTEXITCODE)" }
    }
    Write-Host 'V27_LOT_084_088 : 3/3 Statut cumulatif'
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $engine -Action Status
    if ($LASTEXITCODE -ne 0) { throw "Echec du statut final (code $LASTEXITCODE)" }
    Write-Host 'V27_LOT_084_088_OK'
} catch {
    Write-Error "V27_LOT_084_088_ECHEC : $_"
    exit 1
}
