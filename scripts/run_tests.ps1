param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PytestArgs
)

$ErrorActionPreference = "Stop"

$LocalPython = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"

if (Test-Path $LocalPython) {
    & $LocalPython -m pytest @PytestArgs
    exit $LASTEXITCODE
}

if (-not (Get-Command pytest -ErrorAction SilentlyContinue)) {
    Write-Error "pytest is not installed or not on PATH. Create .venv and install test dependencies first."
}

pytest @PytestArgs
