# Echo Recon 6.3

A local assessment dashboard with explicit host scope, cancellable processes, persistent history and evidence-first reports. Based on [Ahammed's Echo Recon / Auto-Recon](https://github.com/ahammed18122002-art/auto-rec); upgraded for the mdnhbn collaboration.

**[বাংলা নির্দেশনা / Bengali guide →](README.bn.md)** · [Windows / WSL2](docs/WINDOWS.md) · [Contribute](CONTRIBUTING.md) · [বাংলায় অবদান](CONTRIBUTING.bn.md) · [Tool setup](docs/TOOLS.md) · [Security](SECURITY.md)

**New to the form?** Open **How to use** in the dashboard or read the [complete English usage guide](docs/USAGE.md) / [বাংলা ব্যবহারবিধি](docs/USAGE.bn.md). Every field, rate limit, timeout and report state is explained. The header's **Light layout / Dark layout** button switches layouts without losing form values; both include Matrix animation and respect reduced-motion preferences.

**Students, classmates and other contributors are welcome.** Fork this public repository, create a branch and submit a pull request. Maintainers review and merge changes; contributors do not need direct write access. Bug/feature issue forms and a PR template are included. See [CONTRIBUTING.md](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md).

Licensed under **[MIT](LICENSE)**, with original attribution retained. You may use, modify and redistribute under its terms.

The original eight tools remain: **DNSRecon, Subfinder, ProjectDiscovery HTTPX, Nmap, theHarvester, Photon, Arjun and Nuclei**. This edition improves how they are controlled and how results are interpreted. It does not add password attacks, WAF evasion, exploitation or autonomous AI actions.

## What changed

- Distinguishes `done`, `missing`, `unverified`, `error`, `timeout`, `output_limit`, `skipped`, `cancelled` and interrupted work. Failed commands cannot produce a clean success result.
- Explicit 1–5-host scope. Discovered subdomains remain evidence and are not automatically added to active targets.
- One assessment at a time; per-tool/per-host timeouts; low rate/concurrency settings where each tool supports them; Stop kills the current Linux process group.
- SQLite history survives restarts. In-progress work becomes `interrupted`, not resumed or marked safe.
- HTML and JSON reports include phase evidence, stderr, exit status, limitations and unverified Nuclei findings with template-provided remediation where available.
- Loopback-only listener, local-client/Host checks, CSRF protection, HTML escaping and a private data directory. A fixed setup action opens a separate normal-user Kali terminal; the browser never receives sudo credentials or arbitrary commands.
- Restored the original-style dark dashboard and report presentation while retaining scope controls and honest result states.
- No demo generator, preloaded findings or sample scan history. Tests keep mock results in temporary directories only.
- **Download / setup tools** opens official sources and setup guidance beside the health check. Installation stays in your terminal, under your control.

## Requirements

- Kali Linux or another current Linux distribution, Python **3.11+**, Git and `python3-venv`.
- A normal user account. Do **not** run the application as root.
- Network access for installation. Optional assessment tools are installed separately; opening the dashboard does not start an assessment.

### Windows support

| Environment | Supported workflow |
|---|---|
| Kali Linux / Kali VirtualBox | Full Linux dashboard and eight separately installed tool adapters. |
| Windows with Kali WSL2 | Full Linux workflow, opened in a Windows browser. |
| Native Windows with Python 3.11+ | Dashboard, saved history, report exports and development tests. Live scanning requires Kali WSL2. |

Follow the **[English/Bengali Windows guide](docs/WINDOWS.md)**. Native Windows includes `install.ps1` and `run.ps1`; `run-wsl.ps1` starts an already installed Linux copy. Environments/data remain separate. No WSL installation, reboot, admin change or execution-policy weakening happens automatically.

## Download and install on Kali

Open Terminal and run each block in order:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv
mkdir -p ~/Tools/02-Custom
cd ~/Tools/02-Custom
git clone https://github.com/mdnhbn/echo-recon-workspace.git
cd echo-recon-workspace
bash install.sh
```

Only the first two commands need administrator permission. `install.sh` creates `.venv` inside this project and installs the **pinned, SHA-256-verified dashboard dependencies**. It does not install scanners globally, change Java/Go, remove an earlier copy or modify the original Echo project.

Alternative: use **Code → Download ZIP** on GitHub, extract it into a new folder, open a terminal there and run `bash install.sh`. Do not extract over an existing installation.

## Run and check your tools

```bash
cd ~/Tools/02-Custom/echo-recon-workspace
bash run.sh
```

Leave the terminal open. On a desktop session, the launcher opens **http://127.0.0.1:8001** in your default browser once the server is ready. If no browser opens, visit that address manually. Port 8001 keeps this edition separate from older Echo instances on port 8000.

For a headless session or automated development test, use `bash run.sh --no-browser` (Windows: `.\run.ps1 -NoBrowser`). Headless WSL prints the address for your Windows browser rather than opening a terminal text browser.

1. Click **Check installed tools** to inspect local executable identity and help output.
2. If a tool is missing or unverified, use its setup link or **Download / setup tools** beside the check button.
3. For automatic setup on a Kali desktop, click **Setup all tools**. A separate visible terminal opens the fixed installer, skips verified working tools and installs what is missing. Enter a sudo password only in that terminal if asked. Finish and close it, then check tools again. Individual official sources remain available in [the tool setup guide](docs/TOOLS.md).
4. Click **Check installed tools** again after setup to refresh results. Restart the dashboard if you changed the shell's PATH or other inherited environment variables.
5. The dashboard and history remain empty until an assessment is created. No example findings are generated.

Press **Ctrl+C** in the terminal to stop the dashboard. The Stop button cancels an assessment, not the dashboard itself.

## Optional real assessment: your authorized systems only

First use [the tool setup guide](docs/TOOLS.md). Check **Tool health** or run:

```bash
.venv/bin/python doctor.py
```

This runs local help/identity checks; it does not scan a target. Help verification is not a guarantee of compatibility with every tool version. `missing` means the executable is not on PATH; `unverified` means an executable was found but failed identification or required-help checks. Review the path/version before reinstalling anything.

1. Enter the primary hostname without `https://`, a path, a port or a wildcard.
2. List exact authorized hostnames, one per line, including the primary domain. Maximum five; additional hosts must be subdomains of that primary domain.
3. Select checks deliberately. DNS, subdomain discovery and HTTP probing are preselected; other checks are opt-in. Select HTTPX along with Photon/Arjun, since crawling and parameter checks require a confirmed live in-scope host in the same run.
4. Choose a rate ceiling and per-tool/per-host time limit. These are **not** a single global request budget.
5. Confirm permission and the network limitations. Start, monitor, and Stop if needed.
6. Read each phase's status and evidence. A green completed command does not certify website security. Nuclei findings remain **unverified** until reviewed.
7. Open **View report** after the run, or export HTML/JSON. Use **Saved history** to reopen a real saved assessment.

There is no automatic HTTPS fallback for Photon/Arjun when probing fails. Discovery checks use the primary domain; active host checks use the explicit scope. Nmap examines the top 100 ports using TCP connect/service detection, rather than the old top-1000 scan.

## Scope and privacy limits you must understand

This is an application-level input boundary, **not a network sandbox**. Each host is preflight-checked for public-only DNS answers before a phase, but third-party tools resolve independently. DNS can change, and crawlers/templates may request secondary destinations. Some tools also contact public data services. If strict egress isolation is required, use an independently configured lab/firewall; do not rely on this dashboard alone.

Redaction hides common secret patterns and URL credentials on a best-effort basis. It cannot identify every secret or personal record. Reports, DNS answers and raw Photon crawl files remain private under `data/`; review before sharing. `data/` is excluded from Git. The HTML report does not embed a third-party AI provider; no reports are sent to an LLM.

## Update, back up and remove

Stop the dashboard before updates. Preserve `data/` privately if history matters; it can contain sensitive evidence. Then:

```bash
git pull --ff-only
bash install.sh
bash run.sh
```

Use `git status` before pulling if you edited source files. Avoid force-resetting local work. The new edition does not import old Echo reports automatically.

### Remove saved demos from an earlier edition

The production demo button and generation API are removed in 6.2. To remove old demo history, stop the dashboard with **Ctrl+C**, then run from the repository folder:

```bash
.venv/bin/python maintenance.py remove-demo
```

This offline maintenance command removes only legacy jobs explicitly marked as demos; real assessment history is preserved. It does not scan targets or uninstall tools. Do not delete the entire `data/` folder to clear demos, and do not run cleanup while the server is active. Keep any private backup outside Git.

To uninstall, stop the dashboard and use the file manager to move **only this repository folder** to Trash. Its `.venv` is local. This does not uninstall the eight external tools. Keep a private backup of `data/` first if needed.

## Troubleshooting

| Symptom | What to do |
|---|---|
| Root-user refusal | Close the root terminal and use your normal Kali user. |
| `venv` creation fails | Install the distribution's `python3-venv` package. |
| Port 8001 already in use | Stop your earlier copy; do not launch multiple instances sharing `data/`. |
| HTTPX `unverified` | Check `command -v httpx`; Python HTTPX is different from ProjectDiscovery HTTPX. See tool guide. |
| Tool is missing/unverified | Open **Download / setup tools**, review its path/version and official guide, then recheck. Restart after changing PATH. |
| CSRF/reload error | Reload the page after restarting the server. |
| Timeout or partial report | Read stderr and evidence; it is incomplete coverage, not a clean security result. |
| No live hosts | Review HTTPX diagnostics; Photon/Arjun intentionally skip rather than guess a target. |
| History is `interrupted` | The server restarted during the run. It did not automatically resume. |

## Development and validation

```bash
.venv/bin/python -m unittest discover -s tests -v
bash -n install.sh run.sh
```

Tests use mocked scanner responses, simulated DNS and local child processes in temporary directories. They do not create fake rows in the production history. They cover command failures, cancellation, output bounds, DNS/scope validation, persistent state, CSRF/Host controls and report escaping. They do not scan public targets. Live adapter compatibility depends on installed tool versions; this release is not a certification that every external scanner works on every environment.

On native Windows use `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`. CI covers Ubuntu and Windows on Python 3.11 and 3.13. Full Kali WSL provisioning/network integration is not claimed as covered by that matrix.

## Attribution and licensing

Original concept/project: **Ahammed**, [ahammed18122002-art/auto-rec](https://github.com/ahammed18122002-art/auto-rec), source snapshot `f3fbf45`. This edition was requested by **mdnhbn**, who states the original author is a collaborating classmate and supplied the project. Attribution is retained. The maintainer selected the [MIT license](LICENSE) for this collaboration. See [NOTICE.md](NOTICE.md). Third-party tools keep their own licenses.
