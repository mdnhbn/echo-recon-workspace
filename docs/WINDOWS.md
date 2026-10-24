# Windows, WSL and VirtualBox setup / Windows-এ চালানো

[English README](../README.md) · [বাংলা README](../README.bn.md) · [Tool setup](TOOLS.md)

## Choose the environment

| Environment | Where to install/run |
|---|---|
| Native Windows x64 | Windows Python **3.12 x64**, `install.ps1`, `run.ps1`; native backend executables/venvs. WSL is optional. |
| WSL Linux | Clone into Linux HOME; run `bash install.sh` and `bash run.sh` inside that distribution. |
| VirtualBox Kali | Clone/install/run inside Kali; use the browser inside the guest for its own loopback server. |

These are separate installations. Do not share a Windows venv with Linux, reuse databases across running instances, or assume a tool in VirtualBox is installed in Windows/WSL.

সরাসরি Windows-এও native tool setup ও adapter আছে; WSL বাধ্যতামূলক নয়। Windows, WSL এবং VirtualBox-এর tool/environment আলাদা। যে environment-এ dashboard চালাবেন, সেখানেই backend ইনস্টল হবে।

## Native Windows: download → install → run

Use Windows Terminal or PowerShell as your normal user (not an Administrator terminal). On Windows 10 version 1809 or later, and Windows 11, check that WinGet is available:

```powershell
winget --version
```

WinGet is provided by Microsoft's App Installer. Install the supported prerequisites by their exact package IDs, reviewing any installer prompts:

```powershell
winget install --id Python.Python.3.12 --exact --source winget
winget install --id Git.Git --exact --source winget
```

Close and reopen the terminal after installation, then verify:

```powershell
py -3.12 --version
git --version
```

The bundled native Windows backend setup requires Python **3.12 x64**. Git is needed to clone or update this repository; Windows Terminal, PowerShell and Python's bundled `pip` are sufficient for the documented install, so no separate compiler or WSL is required. WinGet itself comes with Microsoft's **App Installer**. If `winget` is not recognized, install/update App Installer from Microsoft Store, reopen the terminal and check again. If App Installer is installed but WinGet is not registered for this user, request its registration from PowerShell:

```powershell
Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe
```

If Microsoft Store/WinGet is unavailable, install [Python 3.12 x64](https://www.python.org/downloads/windows/) and [Git for Windows](https://git-scm.com/downloads/win) directly. Then use normal PowerShell:

```powershell
git clone https://github.com/mdnhbn/echo-recon-workspace.git
cd echo-recon-workspace
.\install.ps1
.\run.ps1
```

The installer prefers Python 3.12. If you have several interpreters:

```powershell
.\install.ps1 -PythonExe 'C:\Path\To\Python312\python.exe'
```

A normal launch opens **http://127.0.0.1:8001**. Automatic startup help checks keep ready tools and start the fixed setup when needed. Progress appears under **Tool health** / **Download / Setup**. An identical unsuccessful automatic attempt is remembered to prevent restart loops; click **Setup all tools** after fixing its error.

### Seven original automatic backends, Nikto and Nmap

Subfinder, ProjectDiscovery HTTPX and Nuclei use verified official Windows x64 ZIPs. DNSRecon, theHarvester, Photon and Arjun have separate versioned Python environments. Nikto source is pinned to its upstream 2.6.1 release and runs through Perl. Install [Strawberry Perl](https://strawberryperl.com/) yourself, then open a new terminal and confirm `perl.exe` is on `PATH`; **Setup all tools** will download Nikto's source and perform the local help check. Echo Recon does not download or silently install a Perl runtime. Nikto retains its own GPL-3.0-only license. Storage is:

```text
C:\Users\YOUR-USER\Tools\EchoRecon\tooling
```

This location is shared by ordinary desktop launches and packaged-application launches. Older copies in virtualized AppData are not moved or deleted automatically. Windows tools are resolved using explicit managed paths without changing the global PATH.

Nmap uses its [official Windows installer](https://nmap.org/download.html). Complete the license and any administrator confirmations yourself, then recheck. The application does not install Npcap drivers or accept agreements unattended. The Windows adapter uses TCP connect `-sT`, service detection and `-Pn`; this does not add UDP, OS detection or raw-packet scanning.

Nikto is an active web-server scanner. Selecting it with Nuclei makes it a fallback only when Nuclei is missing, unverified or fails; selecting Nikto alone runs a standalone check. The adapter limits its checks to information, configuration/default-file and software-identification groups. Use exact hosts only with permission.

`ready` proves a local help/identity check, not all upstream network/API behavior. Native cancellation uses a Windows Job Object to contain the tool process tree and fails rather than running a tool uncontained if assignment is unavailable. Local process fixtures exercise this behavior; no public assessment has been used as a release certification.

### Dashboard-only and startup controls

```powershell
.\install.ps1 -DashboardOnly
.\run.ps1 -NoToolSetup -NoBrowser
```

Dashboard-only accepts Python 3.11+. Full bundled Windows backend setup requires **3.12 x64**. `-NoToolSetup` skips automatic startup installation; the explicit setup button remains available. `-NoBrowser` only suppresses browser opening.

### If PowerShell blocks scripts

Read the scripts and respect your local policy. Do not weaken execution policy. Direct Python works without venv activation:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes --only-binary=:all: -r requirements.txt
.\.venv\Scripts\python.exe setup_tools_windows.py --plan
.\.venv\Scripts\python.exe setup_tools_windows.py --install
.\.venv\Scripts\python.exe app.py
```

The plan is read-only. The install command performs setup but accepts no target. Use a full interpreter path if `py` is unavailable. Stop the app with Ctrl+C in its original terminal.

## WSL: use Linux tools inside Linux

If WSL is not installed, follow [Microsoft's WSL installation guide](https://learn.microsoft.com/windows/wsl/install). WSL installation, administrator approval and any reboot are separate manual system steps; this project does not perform them.

For an existing Kali WSL installation, open it, use a normal Linux account and run:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv
mkdir -p ~/Tools/02-Custom
cd ~/Tools/02-Custom
git clone https://github.com/mdnhbn/echo-recon-workspace.git
cd echo-recon-workspace
bash install.sh
bash run.sh
```

Headless `run.sh` runs setup in the same terminal so sudo prompts remain visible; it then starts the app without launching another setup window. If setup needs attention, read its output and use the explicit CLI retry below:

```bash
.venv/bin/python setup_tools.py --plan
.venv/bin/python setup_tools.py --install
```

In Windows, open **http://127.0.0.1:8001** when WSL localhost forwarding is available; see [Microsoft's WSL networking guide](https://learn.microsoft.com/windows/wsl/networking). Do not expose the dashboard on `0.0.0.0` or disable its local checks to work around networking.

The Windows-side launcher for an already installed Linux copy is:

```powershell
.\run-wsl.ps1 -Distro kali-linux
.\run-wsl.ps1 -Distro kali-linux -NoToolSetup -NoBrowser
```

Its default Linux project is `~/Tools/02-Custom/echo-recon-workspace`. It does not install WSL or copy Windows environments into Linux. Other supported Linux families use their own package-manager/Python requirements from [TOOLS.md](TOOLS.md).

## VirtualBox Kali

Run the Linux commands **inside Kali**, as the normal user. A Windows-host copy is separate from the guest. Inside the Kali browser, `127.0.0.1:8001` reaches the Kali app. Opening the same address in Windows reaches a Windows listener, not the guest automatically.

VirtualBox-এর Kali-তে সাধারণ user দিয়ে installer/app চালান। Linux package-এর sudo password শুধু Kali Terminal-এ দিন। নতুন চালু app-এ **Check installed tools** ও **Setup all tools** দেখে নয়টি tool-এর অবস্থা যাচাই করুন।

## Updates, private data and troubleshooting

Stop the app first and keep a private backup of `data/`. For a native Windows Git checkout, open PowerShell in the repository folder and run:

```powershell
git status --short
git pull --ff-only
.\install.ps1
.\run.ps1
```

For Kali/WSL installed from the signed APT package, run `sudo apt update && sudo apt upgrade`; this works after the feed was added once and installs the latest published release. APT does not update a Git checkout. For a Linux or WSL Git checkout, use `git pull --ff-only`, `bash install.sh`, then `bash run.sh`. Native Windows does not use `sudo apt upgrade`. If you installed from a ZIP, download/extract a fresh copy instead of overwriting an existing folder. Both host and WSL may need port 8001; avoid conflicting listeners.

Windows inherits NTFS permissions; Unix `chmod` is not a Windows ACL setup. Keep data private. Do not commit history, raw evidence, tokens, logs or venvs. Reports need review before sharing.

| Symptom | Check |
|---|---|
| Only Nmap appears after a packaged-app installation | Update to 6.6.0 and run **Setup all tools**; it rebuilds missing managed tools in `~/Tools/EchoRecon/tooling` rather than moving old venvs. |
| Python version/setup error | Use Python 3.12 x64 for Windows bundled backends. An existing broken/unknown/different-Python venv is preserved: back up private data and use a fresh project folder or deliberately recreate the environment after inspection. Dashboard-only is separate. |
| HTTPX unverified | ProjectDiscovery HTTPX and Python HTTPX are different programs; inspect the resolved path. |
| Setup failed or partial | Read progress/stderr. Existing unrelated/partial folders are preserved, not silently replaced. Retry deliberately after fixing the issue. |
| CSRF error after restart | Reload the dashboard to get the new session. |
| Port in use | Stop the other app instance; do not share a running data directory. |

Tests: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`. Tests use mocked downloads/tool responses and local process fixtures. Full fresh provisioning on every Windows/WSL configuration or external API compatibility is not guaranteed.
