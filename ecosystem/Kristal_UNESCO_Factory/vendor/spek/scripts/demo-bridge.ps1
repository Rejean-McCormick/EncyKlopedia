# Offline Spek interoperability demo. Run from the root of the Spek repository.
$ErrorActionPreference = 'Stop'
function Run-Python {
  & python -m spek @args
  if ($LASTEXITCODE -ne 0) { throw "Spek command failed: $args" }
}
Run-Python bridge-import --adapter konstellation --input examples/bridge/konstellation-resultset.json --template examples/article.json --mapping examples/bridge/konstellation-mapping.json --out bridge-article.json
& python -m spek build --source bridge-article.json --out dist-bridge --formats 'html,pdf,tex'
if ($LASTEXITCODE -ne 0) { throw 'Spek build failed' }
Run-Python verify-site dist-bridge
Write-Host 'Run: python -m http.server 8000 --directory dist-bridge'
