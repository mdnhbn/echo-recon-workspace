# Echo Recon 6.5.0

A local assessment dashboard with eight fixed tool adapters, explicit host scope, cancellable processes, saved history and evidence reports. Based on [Ahammed's Echo Recon / Auto-Recon](https://github.com/ahammed18122002-art/auto-rec), upgraded for the mdnhbn collaboration.

**[বাংলা নির্দেশনা](README.bn.md)** · [Kali APT updates](docs/APT.md) · [Windows / WSL](docs/WINDOWS.md) · [Tool setup](docs/TOOLS.md) · [Complete usage guide](docs/USAGE.md) · [Contribute](CONTRIBUTING.md) · [Security](SECURITY.md)

## What 6.5.0 changes

- The installer sets up the dashboard and missing backends together. Normal startup also checks local tools and starts automatic setup when needed; verified working tools are kept.
- Native Windows tools use a stable user folder, `~/Tools/EchoRecon/tooling`, so installation from a packaged application remains visible when a desktop shortcut starts the dashboard.
- Native Windows, Kali VirtualBox, WSL and supported Linux package-manager families have dedicated setup paths. Windows no longer requires WSL for its native adapters.
- Both layouts keep the same form and evidence controls. The Light/Dark button switches in one click; both include Matrix animation and respect reduced-motion preferences.
- History starts empty. There are no generated demo findings. Reports retain errors, timeouts, incomplete output and unverified findings.

The eight tools are **DNSRecon, Subfinder, ProjectDiscovery HTTPX, Nmap, theHarvester, Photon, Arjun and Nuclei**. Installing them does not start an assessment, create API accounts or provide API keys.

## Requirements and support

Use a normal user account and internet access. The dashboard refuses root on Linux. The source-checkout path also needs Git; the Kali APT path installs as a signed system package and stores reports in the user's data folder.

| Environment | Setup path and requirements | Verification limits |
|---|---|---|
| Native Windows x64 | Python **3.12 x64** for bundled backend setup; `install.ps1` and `run.ps1`. Seven backends install automatically; Nmap uses its official installer. | Native installation/local help checks and local process/cancellation fixtures have been checked. No public-target scan certification. |
| Kali Linux, including VirtualBox and Kali WSL | Signed APT package needs sudo once for feed/package setup; source checkout needs Git, Python and venv support. Missing compiled Go tools require Go **1.26+**. | Kali local tool checks and regression tests; provider/network availability still varies. |
| Other supported glibc Linux families | Debian/Ubuntu (`apt`), Fedora/RHEL (`dnf`), Arch (`pacman`), openSUSE (`zypper`); portable assets for x86_64/aarch64. Python **3.12+** is required when installing pinned DNSRecon/theHarvester sources. | Installer logic is tested with mocked downloads/package managers. A fresh full installation on every distribution is **not** claimed. |
| Other distributions/architectures | Dashboard requires Python 3.11+; install compatible backend tools manually. Alpine/musl is not an automatic-install target. | Not an automatically provisioned platform. |

A dashboard-only installation supports Python 3.11+. For that workflow use `--dashboard-only` / `-DashboardOnly`, then start with `--no-tool-setup` / `-NoToolSetup` if you want to avoid automatic backend setup.

## Download, install and run

### Kali APT-managed installation and updates

The signed Kali/Debian APT feed is the automatic update path: install its signing key and source once using [Kali APT updates](docs/APT.md), then run `sudo apt update && sudo apt upgrade` to receive the latest **published release**. It does not fetch every Git commit. The feed becomes installable after the repository signing key is configured and the first matching release tag is published.

If you already use the source checkout, close it before migrating. The package keeps future report history in `~/.local/share/echo-recon`; the guide explains how to copy saved history and switch to the `/usr/bin/echo-recon` launcher. Keep the old checkout until you verify your reports.

### Kali / Linux from a Git checkout

On Kali, install the initial prerequisites if absent:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv
```

Then, as your normal user:

```bash
mkdir -p ~/Tools/02-Custom
cd ~/Tools/02-Custom
git clone https://github.com/mdnhbn/echo-recon-workspace.git
cd echo-recon-workspace
bash install.sh
bash run.sh
```

`git clone` downloads the repository. `install.sh` creates the project's `.venv`, verifies dashboard dependency hashes and sets up missing tools together. Fixed system packages may request sudo **in your terminal**. Do not run `sudo bash install.sh` or `sudo python app.py`.

On another supported Linux family, install Git, a suitable Python and its venv support using that distribution's package manager first, then use the same clone/install/run commands. See [TOOLS.md](docs/TOOLS.md) for package-manager and Python limits.

### Native Windows

On Windows 10 (version 1809 or later) or Windows 11, open Windows Terminal or PowerShell as your normal user and check whether WinGet is available:

```powershell
winget --version
```

If it prints a version, install the prerequisites with these commands. Review and accept any installer prompts:

```powershell
winget install --id Python.Python.3.12 --exact --source winget
winget install --id Git.Git --exact --source winget
```

Close and reopen the terminal, then verify both commands:

```powershell
py -3.12 --version
git --version
```

The project needs Python **3.12 x64** for its bundled Windows backends. Git is only needed to clone/update the repository; no separate compiler or Linux layer is required. If `winget` is unavailable, install or update **App Installer** by Microsoft from Microsoft Store, reopen the terminal and try again. If App Installer is already present but WinGet has not registered for this Windows user, run this in PowerShell, then reopen the terminal:

```powershell
Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe
```

You can also install Python from [Python.org](https://www.python.org/downloads/windows/) and Git from [Git for Windows](https://git-scm.com/downloads/win). After installing the prerequisites, open normal PowerShell:

```powershell
git clone https://github.com/mdnhbn/echo-recon-workspace.git
cd echo-recon-workspace
.\install.ps1
.\run.ps1
```

If needed, choose the installed Python explicitly with `.\install.ps1 -PythonExe 'C:\Path\To\Python312\python.exe'`. Seven compatible tools install in separate user-owned environments. **Nmap is the manual exception:** follow its [official Windows installer](https://nmap.org/download.html), complete its license/administrator confirmations yourself, then use **Check installed tools** or **Setup all tools** again. The app does not silently accept terms or install drivers.

If PowerShell blocks scripts, keep your policy and use the direct Python commands in [WINDOWS.md](docs/WINDOWS.md). You can also choose **Code → Download ZIP** on GitHub and extract into a new folder instead of cloning. Do not extract over an existing installation.

### Open the dashboard

The desktop launcher opens **http://127.0.0.1:8001** after the server binds. Keep its terminal open; use Ctrl+C to stop the server. The address belongs to the machine/environment running the server. A VirtualBox guest's loopback is separate from the Windows host's loopback.

Headless Linux/WSL runs the fixed setup directly in its terminal so sudo prompts remain visible. Open the printed address in your browser afterward. WSL users should keep the repository in Linux HOME and keep Windows/WSL environments separate; [WINDOWS.md](docs/WINDOWS.md) explains the launcher.

## Automatic setup and deliberate retry

1. On a normal startup, local help/identity checks run. If everything is ready, nothing is downloaded.
2. Missing backends are set up together through the repository's fixed installer. Windows progress appears in the dashboard; a Linux desktop opens a visible setup terminal.
3. An identical unsuccessful desktop automatic attempt is remembered in private `data/auto-setup.json` so each restart does not repeat the same failure. Read the error and click **Setup all tools** for a deliberate retry.
4. **Check installed tools** refreshes readiness. `ready` means local help/identity passed; for Nuclei it also means the local official template version was found. This does not verify every template file, API credentials, upstream services or scan results. `unverified` means inspect the found path/version before reinstalling; **Setup all tools** can refresh Nuclei's official templates without reinstalling its engine.
5. To skip startup setup, use `bash run.sh --no-tool-setup`, `.\run.ps1 -NoToolSetup`, or `python app.py --no-tool-setup`. To suppress browser opening too, add `--no-browser` / `-NoBrowser`.

Working system tools stay in place. Unknown folders, conflicting wrappers and incomplete tool environments are preserved rather than overwritten. See [the tool setup and retry guide](docs/TOOLS.md).

## Use the assessment form

Read [the English usage guide](docs/USAGE.md) or [বাংলা ব্যবহারবিধি](docs/USAGE.bn.md) for each field and setting.

1. Enter a hostname you own or have explicit permission to assess, without a URL scheme/path/port.
2. List exact authorized hosts, including the primary domain, one per line; maximum five. Extra names must be its subdomains.
3. Select checks, rate ceiling and time per tool/host. Photon/Arjun require HTTPX-confirmed live scoped hosts in the same run.
4. Confirm permission and network limitations, then start deliberately. Setup and assessments cannot start together.
5. Read progress and evidence. Stop cancels the current process group on Linux or the contained process tree on Windows. Reports label incomplete work honestly; Nuclei findings remain **unverified** until human review.

The rate is a ceiling for tools that support it, not one global traffic budget. The 120-second default is per tool/host attempt, not the whole job. Nmap uses limited top-100 TCP connect/service detection; Windows also skips raw-packet host discovery with `-Pn`.

This is an application-level scope boundary, **not a network sandbox**. Third-party tools may resolve DNS independently, follow secondary requests or contact public data services. An empty finding list is not proof of safety. Review [SECURITY.md](SECURITY.md).

## Update, backups and data

Stop the server first, keep private backups of `data/`, and inspect local changes:

```bash
git status
git pull --ff-only
bash install.sh
bash run.sh
```

Windows uses `.\install.ps1` and `.\run.ps1` after the pull. Do not force-reset local work or reuse a Linux venv on Windows. An existing broken/unknown venv or one made with a different Python major/minor is preserved and refused before recreation; keep a private data backup and use a fresh project folder or deliberately rebuild the environment after inspection. Private history, setup logs and raw evidence live under `data/`; do not commit or publish them. Common secret redaction is best effort. Reports are not sent to an AI service.

### Remove saved demos from an earlier edition

Production demo generation is removed. With the server stopped, run `.venv/bin/python maintenance.py remove-demo` on Linux or `.\.venv\Scripts\python.exe maintenance.py remove-demo` on Windows. Only explicitly marked legacy demo jobs are removed; real history is preserved. Do not delete the whole data directory to clear demos.

Moving the repository to Trash does not uninstall externally managed backend tools. Keep any needed history backup privately first; inspect installer-owned tool folders before removal.

## Development and contribution

```bash
.venv/bin/python -m unittest discover -s tests -v
bash -n install.sh run.sh
```

Windows: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`. Tests use simulated DNS/tool output, mocked downloads and local child-process fixtures. They do not scan public targets or seed production history. See [architecture](docs/ARCHITECTURE.md) for the fixed adapter and setup boundaries.

**Students, classmates and other contributors are welcome.** Fork → create a branch → change code/tests/docs → submit a pull request. Maintainers review changes before merging. See [CONTRIBUTING.md](CONTRIBUTING.md), [বাংলায় অবদান](CONTRIBUTING.bn.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Attribution and licensing

Original concept/project: **Ahammed**, [ahammed18122002-art/auto-rec](https://github.com/ahammed18122002-art/auto-rec), source snapshot `f3fbf45`. This edition was requested by **mdnhbn**, who states the original author is a collaborating classmate and supplied the project. Original attribution is retained. The maintainer selected **[MIT](LICENSE)** for this collaboration; see [NOTICE.md](NOTICE.md). Third-party tools retain their own licenses.
