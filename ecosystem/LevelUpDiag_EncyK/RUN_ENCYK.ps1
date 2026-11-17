param(
    [string]$TargetRepo = 'C:\mycode\EncyKlopedia\EncyKlopedia',
    [ValidateSet('doctor','reader','quick','repository','bridge','standard')][string]$Campaign = 'reader'
)
$ErrorActionPreference = 'Stop'
$tool = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($Campaign -eq 'doctor') {
    & python -B (Join-Path $tool 'levelupdiag.py') --target $TargetRepo doctor
} else {
    & python -B (Join-Path $tool 'levelupdiag.py') --target $TargetRepo run $Campaign
}
exit $LASTEXITCODE
