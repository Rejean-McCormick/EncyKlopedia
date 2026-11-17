function Invoke-PythonFixtureScript {
    param(
        [Parameter(Mandatory)]
        [string] $Code,

        [Parameter(Mandatory)]
        [string[]] $Arguments
    )

    $pythonCommand = Get-PythonCommand
    $exe = $pythonCommand[0]
    $exeArgs = @()

    if ($pythonCommand.Count -gt 1) {
        $exeArgs += $pythonCommand[1..($pythonCommand.Count - 1)]
    }

    if ([string]::IsNullOrWhiteSpace($script:TempRoot)) {
        throw "TempRoot has not been initialized."
    }

    $pythonTempDir = Join-Path $script:TempRoot "python_fixtures"
    New-Item -ItemType Directory -LiteralPath $pythonTempDir -Force | Out-Null

    $tempScript = Join-Path $pythonTempDir ("fixture_script_" + [guid]::NewGuid().ToString("N") + ".py")

    try {
        Set-Content -LiteralPath $tempScript -Value $Code -Encoding UTF8

        $allArgs = @($exeArgs + @($tempScript) + $Arguments)
        $output = & $exe @allArgs 2>&1
        $exitCode = $LASTEXITCODE
        $text = ($output | Out-String).Trim()

        if ($exitCode -ne 0) {
            throw "Python fixture script failed with exit code $exitCode.`n$text"
        }

        return $text
    }
    finally {
        if (Test-Path -LiteralPath $tempScript) {
            Remove-Item -LiteralPath $tempScript -Force -ErrorAction SilentlyContinue
        }
    }
}