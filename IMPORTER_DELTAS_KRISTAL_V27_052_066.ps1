# EncyKlopedia v27 — importer les deltas 052 a 066 dans le Kristal prive.
# Un seul lancement depuis la racine du depot; pas d'admission canonique.
$ErrorActionPreference = 'Stop'
$repo = $PSScriptRoot
$work = 'D:\EncyKlopedia\30_working\production_kristals_v27'
$source = Join-Path $repo 'tools\unesco_pilot\v27_data\lot_052_066'
$dest = Join-Path $work 'deltas'
$engine = Join-Path $repo 'PRODUIRE_KRISTALS_V27.ps1'

try {
    if (-not (Test-Path -LiteralPath $engine -PathType Leaf)) { throw "Moteur v27 introuvable : $engine" }
    if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw "Deltas introuvables : $source" }
    # Verifier tous les fichiers avant de commencer les importations.
    for ($n = 52; $n -le 66; $n++) {
        $id = '{0:D6}' -f $n
        $pack = Join-Path $work "packs\PACK_V27_$id.zip"
        $delta = Join-Path $source "DELTA_KRISTAL_PACK_V27_$id.json"
        if (-not (Test-Path -LiteralPath $pack -PathType Leaf)) { throw "Pack source introuvable : $pack" }
        if (-not (Test-Path -LiteralPath $delta -PathType Leaf)) { throw "Delta introuvable : $delta" }
    }
    New-Item -ItemType Directory -Path $dest -Force | Out-Null
    for ($n = 52; $n -le 66; $n++) {
        $id = '{0:D6}' -f $n
        $pack = Join-Path $work "packs\PACK_V27_$id.zip"
        $deltaSource = Join-Path $source "DELTA_KRISTAL_PACK_V27_$id.json"
        $deltaDest = Join-Path $dest "DELTA_KRISTAL_PACK_V27_$id.json"
        if (Test-Path -LiteralPath $deltaDest -PathType Leaf) {
            $h1 = (Get-FileHash -LiteralPath $deltaSource -Algorithm SHA256).Hash
            $h2 = (Get-FileHash -LiteralPath $deltaDest -Algorithm SHA256).Hash
            if ($h1 -ne $h2) {
                throw "Delta different deja present : $deltaDest ; aucun remplacement automatique"
            }
        } else {
            Copy-Item -LiteralPath $deltaSource -Destination $deltaDest -ErrorAction Stop
        }
        Write-Host "V27_LOT_052_066 : import $id"
        & pwsh -NoProfile -ExecutionPolicy Bypass -File $engine -Action Import -Pack $pack -Delta $deltaDest
        if ($LASTEXITCODE -ne 0) { throw "Echec import pack $id (code $LASTEXITCODE)" }
    }
    Write-Host 'V27_LOT_052_066 : statut final'
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $engine -Action Status
    if ($LASTEXITCODE -ne 0) { throw "Echec du statut final (code $LASTEXITCODE)" }
    Write-Host 'V27_LOT_052_066_OK'
} catch {
    Write-Error "V27_LOT_052_066_ECHEC : $_"
    exit 1
}
