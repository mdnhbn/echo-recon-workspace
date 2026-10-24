param([string]$PythonExe = '', [switch]$DashboardOnly)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if ($PythonExe) {
    $pythonCommand = (Get-Command $PythonExe -ErrorAction Stop).Source
    $pythonArgs = @()
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCommand = (Get-Command py).Source
    $pythonArgs = @('-3.12')
    if ($DashboardOnly) {
        & $pythonCommand -3.12 -c 'import sys; sys.exit(0)' *> $null
        if ($LASTEXITCODE -ne 0) { $pythonArgs = @('-3') }
    }
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCommand = (Get-Command python).Source
    $pythonArgs = @()
} else {
    throw 'Install official Python 3.12 x64 first. See docs/WINDOWS.md.'
}
$versionCheck = 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)'
if (-not $DashboardOnly) { $versionCheck = 'import sys,struct; sys.exit(0 if sys.version_info[:2] == (3,12) and struct.calcsize("P")==8 else 1)' }
& $pythonCommand @pythonArgs -c $versionCheck
if ($LASTEXITCODE -ne 0) { throw 'Use Python 3.12 x64 for native backend setup; -DashboardOnly accepts Python 3.11+.' }
$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot '.venv')) {
    if (-not (Test-Path -LiteralPath $venvPython)) { throw 'Existing .venv is unrecognized and was preserved. Install in a fresh project folder.' }
    $selectedVersion = & $pythonCommand @pythonArgs -c 'import sys; print("%d.%d" % sys.version_info[:2])'
    if ($LASTEXITCODE -ne 0) { throw 'Cannot check the selected Python version.' }
    $existingVersion = & $venvPython -c 'import sys; print("%d.%d" % sys.version_info[:2])'
    if ($LASTEXITCODE -ne 0 -or $selectedVersion -ne $existingVersion) {
        throw 'Existing .venv uses a different Python version and was preserved. Install this update in a fresh folder; keep a private backup of data.'
    }
}
& $pythonCommand @pythonArgs -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $venvPython -m pip install --require-hashes --only-binary=:all: -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Review the output above.' }
if (-not $DashboardOnly) {
    & $venvPython setup_tools_windows.py --install
    if ($LASTEXITCODE -ne 0) {
        $setupExit = $LASTEXITCODE
        Write-Warning 'Backend setup needs attention; read the output above. Nmap uses its official interactive installer. Dashboard installed; Setup all tools can retry.'
        exit $setupExit
    }
}
Write-Host 'Windows dashboard installed. Run: .\run.ps1'
Write-Host 'First startup checks missing backends. Native tools use your Tools\EchoRecon\tooling folder.'
