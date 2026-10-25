# macOS installation and updates

[English README](../README.md) · [বাংলা macOS নির্দেশনা](MACOS.bn.md) · [Tool setup](TOOLS.md) · [Usage](USAGE.md)

Echo Recon runs as a local Python server and opens its interface in your Mac's browser at **http://127.0.0.1:8001**. Keep Terminal open while using it. This source installation does not create a signed `.app` bundle.

## 1. Check the prerequisites

Use your normal macOS account, internet access and **Python 3.12 or newer** for the full backend setup. Use a native terminal/Python/Homebrew combination:

| Mac | Native architecture | Homebrew location |
|---|---|---|
| Apple Silicon | `arm64` | `/opt/homebrew` |
| Intel | `x86_64` | `/usr/local` |

The installer provides paths for both architectures. That does not promise Homebrew packages for every macOS version: [Homebrew's current requirements](https://docs.brew.sh/Installation) and [support tiers](https://docs.brew.sh/Support-Tiers) determine which OS/architecture combinations receive bottles and support. Intel macOS currently has legacy Tier 3 support. On Apple Silicon, use a native terminal rather than a terminal configured to open using Rosetta.

If Homebrew is missing, install it yourself using the options on [brew.sh](https://brew.sh/) and follow its **Next steps**, including Command Line Tools if requested. Echo Recon does not download and run Homebrew's shell installer or change system security settings.

Once `brew --version` works, install the initial prerequisites in Terminal:

```bash
brew install python@3.12 git
git --version
```

The setup scripts look for a suitable native Homebrew Python as well as a suitable Python already on PATH. If you use another Python distribution, it must support `venv` and match your native architecture.

## 2. Download and install

Open Terminal and run each line in order:

```bash
mkdir -p ~/Tools
cd ~/Tools
git clone https://github.com/mdnhbn/echo-recon-workspace.git
cd echo-recon-workspace
bash install.sh
bash run.sh
```

`git clone` downloads the project. `install.sh` creates the project's `.venv`, installs the dashboard's dependencies with their reviewed hashes, and runs the fixed macOS backend installer. `run.sh` starts the local dashboard. Do not put `sudo` before these commands.

The installer checks all nine backends and skips tools that already pass local identity checks. Missing Nmap and Nikto use the official [Homebrew Nmap](https://formulae.brew.sh/formula/nmap) and [Nikto](https://formulae.brew.sh/formula/nikto) formulae. Subfinder, ProjectDiscovery HTTPX and Nuclei use pinned official Darwin releases with checksum verification. DNSRecon, theHarvester, Photon and Arjun use separate user-owned Python environments with pinned upstream versions/snapshots. A Go SDK is not required for this macOS download path.

Managed tool environments are stored under `~/.local/share/echo-recon/tooling`, and their launchers are under `~/.local/bin`. Existing working system tools stay in place. Source checkouts keep private reports and history in the project's `data/` folder unless you explicitly configure another data directory.

Once the server opens the browser, use **Check installed tools** to inspect readiness. **Setup all tools** retries the same fixed macOS setup and shows its worker log in the dashboard. Installation never starts an assessment or creates API accounts/keys. Keep Terminal open; press **Ctrl+C** there to stop Echo Recon.

## 3. Inspect or retry setup manually

Run these commands from the repository folder:

```bash
.venv/bin/python setup_tools_macos.py --plan
.venv/bin/python setup_tools_macos.py --install
.venv/bin/python doctor.py
```

Default/`--plan` prints the sources and paths without executing tools, downloading or writing. `--install` performs setup. Unknown folders, conflicting launchers and incomplete environments are preserved; read the reported error before deciding what to move yourself. Do not move a Python venv between folders or machines.

To refresh Nuclei's official templates deliberately:

```bash
.venv/bin/python setup_tools_macos.py --install --update-templates
```

The templates come from Nuclei's official updater and change upstream. A successful local version check does not verify every template file, provider or future scan.

For only the dashboard:

```bash
bash install.sh --dashboard-only
bash run.sh --no-tool-setup
```

Add `--no-browser` to `run.sh` if you want to open the printed local address yourself. These macOS setup scripts require a native Python 3.12+ even in dashboard-only mode.

## 4. Update an existing Mac installation

Stop the running server with Ctrl+C. Keep a private backup of `data/`, then open Terminal in your repository folder:

```bash
git status --short
git pull --ff-only
bash install.sh
bash run.sh
```

`git pull` updates Echo Recon's code; `install.sh` refreshes dashboard dependencies and fills missing backends. It keeps existing tools that pass their checks. Review local modifications if Git refuses to update; do not force-reset them.

macOS does not use this project's Kali APT feed. `sudo apt upgrade` will not update a native Mac installation. `brew upgrade` updates Homebrew-managed software; it does not update this cloned Echo Recon repository. ZIP users should extract the new ZIP into a fresh folder and deliberately transfer private history after stopping the old server.

## 5. Read errors before retrying

| Message/symptom | Next step |
|---|---|
| Homebrew or Command Line Tools missing | Complete the official prerequisite setup, reopen Terminal, then retry. |
| Architecture/Homebrew prefix mismatch | Use native Apple Silicon or native Intel tools consistently; do not mix a Rosetta Python with the other Homebrew prefix. |
| Python version too old | Install a suitable Python, then use a fresh project folder if the existing `.venv` belongs to another Python version. |
| Tool is `unverified` or a launcher conflicts | Read its resolved path in Tool health/`doctor.py`; inspect the old installation before changing files. |
| Browser does not open | Keep the server running and visit `http://127.0.0.1:8001` on that same Mac. |
| Port 8001 is already in use | Stop the earlier Echo Recon process before starting another copy. |

Local help/identity checks and automated fixtures do not certify a full fresh installation on every macOS release or live provider behavior. Only assess hosts you own or have explicit permission to test; see [SECURITY.md](../SECURITY.md).
