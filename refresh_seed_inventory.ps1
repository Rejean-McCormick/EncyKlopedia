$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Script = Join-Path $Root '00_system\tools\seed-manager\refresh_seed_inventory.py'
python $Script
