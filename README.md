# Echo Recon 6.0

A local assessment dashboard with explicit host scope, cancellable processes, persistent history and evidence-first reports. Based on [Ahammed's Echo Recon / Auto-Recon](https://github.com/ahammed18122002-art/auto-rec); upgraded for the mdnhbn collaboration.

**[বাংলা নির্দেশনা / Bengali guide →](README.bn.md)** · [Tool setup](docs/TOOLS.md) · [Architecture](docs/ARCHITECTURE.md) · [Security and limitations](SECURITY.md) · [Changes](CHANGELOG.md)

The original eight tools remain: **DNSRecon, Subfinder, ProjectDiscovery HTTPX, Nmap, theHarvester, Photon, Arjun and Nuclei**. This edition improves how they are controlled and how results are interpreted. It does not add password attacks, WAF evasion, exploitation or autonomous AI actions.

## What changed

- Distinguishes `done`, `missing`, `unverified`, `error`, `timeout`, `output_limit`, `skipped`, `cancelled` and interrupted work. Failed commands cannot produce a clean success result.
- Explicit 1–5-host scope. Discovered subdomains remain evidence and are not automatically added to active targets.
- One assessment at a time; per-tool/per-host timeouts; low rate/concurrency settings where each tool supports them; Stop kills the current Linux process group.
- SQLite history survives restarts. In-progress work becomes `interrupted`, not resumed or marked safe.
- HTML and JSON reports include phase evidence, stderr, exit status, limitations and unverified Nuclei findings with template-provided remediation where available.
- Loopback-only listener, local-client/Host checks, CSRF protection, HTML escaping and a private data directory. No dashboard-triggered installer, root account or sudo session.
- Offline simulated demo. No scanner, DNS lookup or target request is made by the demo.

## Requirements

- Kali Linux or another current Linux distribution, Python **3.11+**, Git and `python3-venv`.
- A normal user account. Do **not** run the application as root.
- Network access for installation. Optional assessment tools are separate; the demo does not require them.

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

## Run and learn with the demo

```bash
cd ~/Tools/02-Custom/echo-recon-workspace
bash run.sh
```

Leave the terminal open. Open Firefox and visit **http://127.0.0.1:8001**. Port 8001 keeps this edition separate from older Echo instances on port 8000.

1. Click **Open demo / ডেমো দেখুন**.
2. Watch the phase states. The demo deliberately simulates a Nuclei timeout.
3. The final state is **partial**. This is intentional: incomplete work must not appear safe.
4. Open **View report**, or download HTML/JSON. Demo output is labelled **SIMULATED**.
5. Select the run in **Saved history** to reopen it later.

Press **Ctrl+C** in the terminal to stop the dashboard. The Stop button cancels an assessment, not the dashboard itself.

## Optional real assessment: your authorized systems only

First use [the tool setup guide](docs/TOOLS.md). Check **Tool health** or run:

```bash
.venv/bin/python doctor.py
```

This runs local help/identity checks; it does not scan a target. Help verification is not a guarantee of compatibility with every tool version. Refresh results by restarting the dashboard after installing tools.

1. Enter the primary hostname without `https://`, a path, a port or a wildcard.
2. List exact authorized hostnames, one per line, including the primary domain. Maximum five; additional hosts must be subdomains of that primary domain.
3. Select checks deliberately. DNS, subdomain discovery and HTTP probing are preselected; other checks are opt-in. Select HTTPX along with Photon/Arjun, since crawling and parameter checks require a confirmed live in-scope host in the same run.
4. Choose a rate ceiling and per-tool/per-host time limit. These are **not** a single global request budget.
5. Confirm permission and the network limitations. Start, monitor, and Stop if needed.
6. Read each phase's status and evidence. A green completed command does not certify website security. Nuclei findings remain **unverified** until reviewed.

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

To uninstall, stop the dashboard and use the file manager to move **only this repository folder** to Trash. Its `.venv` is local. This does not uninstall the eight external tools. Keep a private backup of `data/` first if needed.

## Troubleshooting

| Symptom | What to do |
|---|---|
| Root-user refusal | Close the root terminal and use your normal Kali user. |
| `venv` creation fails | Install the distribution's `python3-venv` package. |
| Port 8001 already in use | Stop your earlier copy; do not launch multiple instances sharing `data/`. |
| HTTPX `unverified` | Check `command -v httpx`; Python HTTPX is different from ProjectDiscovery HTTPX. See tool guide. |
| Tool is missing/unverified | Install the correct tool or deselect that check; restart after changing PATH. |
| CSRF/reload error | Reload the page after restarting the server. |
| Timeout or partial report | Read stderr and evidence; it is incomplete coverage, not a clean security result. |
| No live hosts | Review HTTPX diagnostics; Photon/Arjun intentionally skip rather than guess a target. |
| History is `interrupted` | The server restarted during the run. It did not automatically resume. |

## Development and validation

```bash
.venv/bin/python -m unittest discover -s tests -v
bash -n install.sh run.sh
```

Tests use mocked scanner responses, simulated DNS and local child processes. They cover command failures, cancellation, output bounds, DNS/scope validation, persistent state, CSRF/Host controls and report escaping. They do not scan public targets. Live adapter compatibility depends on installed tool versions; this release is not a certification that every external scanner works on every environment.

## Attribution and licensing

Original concept/project: **Ahammed**, [ahammed18122002-art/auto-rec](https://github.com/ahammed18122002-art/auto-rec), source snapshot `f3fbf45`. This edition was requested by **mdnhbn**, who states the original author is a collaborating classmate and supplied the project. Attribution is retained. See [NOTICE.md](NOTICE.md). No new open-source license has been assigned on behalf of the original author; being public does not imply unrestricted reuse. Agree on a license together before inviting general redistribution.
