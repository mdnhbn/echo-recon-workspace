param([switch]$NoBrowser, [switch]$NoToolSetup)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    & (Join-Path $PSScriptRoot 'install.ps1') -DashboardOnly
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $venvPython)) { throw 'Dashboard installation failed. Review the output above.' }
}
$appArgs = @()
if ($NoBrowser) { $appArgs += '--no-browser' }
if ($NoToolSetup) { $appArgs += '--no-tool-setup' }
& $venvPython app.py @appArgs
exit $LASTEXITCODE
