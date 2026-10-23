$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    throw 'First run .\install.ps1, or use the manual Python commands in docs/WINDOWS.md.'
}
& $venvPython app.py
exit $LASTEXITCODE
