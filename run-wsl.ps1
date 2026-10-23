param([ValidatePattern('^[A-Za-z0-9._-]+$')][string]$Distro = 'kali-linux')
$ErrorActionPreference = 'Stop'
if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    throw 'WSL is not installed. Follow docs/WINDOWS.md first.'
}
# The project location is inside Linux HOME, not an interpolated Windows shell path.
$linuxCommand = 'cd ~/Tools/02-Custom/echo-recon-workspace || { echo Install the project inside Kali WSL first. See docs/WINDOWS.md. >&2; exit 1; }; exec bash run.sh'
& wsl.exe --distribution $Distro --exec bash -lc $linuxCommand
exit $LASTEXITCODE
