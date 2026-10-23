param([string]$PythonExe = '')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

if ($PythonExe) {
    $pythonCommand = (Get-Command $PythonExe -ErrorAction Stop).Source
    $pythonArgs = @()
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCommand = (Get-Command py).Source
    $pythonArgs = @('-3')
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCommand = (Get-Command python).Source
    $pythonArgs = @()
} else {
    throw 'Install Python 3.11+ first. See docs/WINDOWS.md.'
}

& $pythonCommand @pythonArgs -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 or newer is required.' }
& $pythonCommand @pythonArgs -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $venvPython -m pip install --require-hashes --only-binary=:all: -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Review the output above.' }
Write-Host 'Windows dashboard installed. Run: .\run.ps1'
Write-Host 'Native Windows: demo/history/reports. Full scanners: Kali WSL2 (docs/WINDOWS.md).'
