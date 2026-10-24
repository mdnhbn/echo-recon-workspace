# Optional assessment tools / বাইরের টুলের সেটআপ

The dashboard installer installs **only the dashboard**. The eight tools are independent third-party projects with their own licenses, dependencies and update policies. An existing Kali installation usually has several already. Do not move `/usr/bin` files into this project or reinstall working tools unnecessarily.

Dashboard-এর installer শুধু dashboard ইনস্টল করে। আটটি tool আলাদা project। আগে থেকে থাকলে আবার install করার প্রয়োজন নেই। System-এর executable সরাবেন না।

## Set up all missing tools / একসঙ্গে সেটআপ

On a Kali desktop, click **Setup all tools** beside the check/download controls. It opens this repository's fixed `setup_tools.py` in a visible terminal, runs local identity checks, skips ready tools and installs missing ones. Apt packages may ask for your sudo password in that terminal. The browser receives no password. Finish and close the terminal before starting an assessment; then click **Check installed tools** again.

For manual/headless Kali or Kali WSL2, first finish/stop any assessment. From the repository directory, as your normal user:

```bash
.venv/bin/python setup_tools.py --plan
.venv/bin/python setup_tools.py --install
```

The first line is a read-only plan; the second performs setup. The installer uses fixed Kali apt packages, exact Go module versions, an exact Photon commit and pinned isolated Python environments. Its pins live in `setup_tools.py`; these third-party dependencies are separate from the dashboard's hash lock. Custom tools live under `~/.local/share/echo-recon/tooling`, with managed launchers in `~/.local/bin`. Existing unrelated launchers are not overwritten; inspect any conflict it reports before retrying. Working system executables are kept in place. The helper supports normal-user Kali only; native Windows displays Kali/WSL instructions.

New Nuclei installations download current official templates (a changing upstream snapshot); existing ready installations/templates are left alone. To explicitly refresh an existing Nuclei's templates, use `.venv/bin/python setup_tools.py --install --update-templates` while no assessment is running. This downloads templates, not scan results. Installation does not create API accounts or keys.

বাংলায়: **Setup all tools** চাপলে আলাদা Kali terminal-এ যা হচ্ছে দেখতে পাবেন। ঠিক থাকা tool রেখে দেবে। Error হলে সফল ধরে নেবেন না—terminal-এর নির্দেশনা দেখুন। নিজের তৈরি wrapper-এর সঙ্গে নাম মিলে গেলে সেটা মুছে বা overwrite করবে না। Windows-এ tool setup করতে Kali WSL2-র terminal ব্যবহার করুন।

## First check / আগে যাচাই

From the repository folder, as your normal user:

The dashboard's **Download / Setup tools** button lists all eight official sources and this guide. It stays available even when a tool is missing. The **Check installed tools** button refreshes local diagnostics after manual setup; `unverified` means check the version/PATH rather than blindly reinstalling.

```bash
export PATH="$HOME/.local/bin:$HOME/go/bin:/usr/local/go/bin:$PATH"
.venv/bin/python doctor.py
```

`ready` means the executable's local help/identity check passed; it is not a full functional test or a version security audit. `missing` means not on PATH. `unverified` means identity/help failed. Check the path in the JSON output. No target is contacted by these checks, although third-party programs control their own help/version behavior.

`ready` পুরো পরীক্ষা নয়। `missing` হলে PATH দেখুন। `unverified` হলে ভুল program বা অসমর্থিত version হতে পারে।

## Kali-managed tools

Check available candidates before installing:

```bash
apt-cache policy dnsrecon theharvester nmap subfinder httpx-toolkit arjun nuclei
```

For missing packages, Kali's repository is the simplest managed source. For example:

```bash
sudo apt update
sudo apt install dnsrecon theharvester nmap
```

Install only the additional packages your Kali repository actually offers and which you need. Package versions vary with Kali rolling updates; they are not pinned by this application's lock file. We do not download and execute remote installation scripts.

Kali-এর package version সময়ের সঙ্গে বদলায়। এই project-এর `requirements.txt` scanner-গুলোকে pin করে না। কোন package সত্যিই missing তা দেখে install করুন।

## Tool references and compatibility

| Tool | Official source / guidance | Adapter expects |
|---|---|---|
| DNSRecon | [darkoperator/dnsrecon](https://github.com/darkoperator/dnsrecon) | Standard DNS enumeration (`-t std`). |
| Subfinder | [ProjectDiscovery installation](https://docs.projectdiscovery.io/tools/subfinder/install) | Domain input and silent output. |
| HTTPX | [ProjectDiscovery installation](https://docs.projectdiscovery.io/tools/httpx/install) | `-silent`, `-rl`, `-threads`, `-timeout`, `-retries`. |
| Nmap | [Nmap downloads](https://nmap.org/download.html) | TCP connect/service detection, top-port and rate bounds. |
| theHarvester | [laramies/theHarvester](https://github.com/laramies/theHarvester) | `crtsh,otx` sources; service availability can vary. |
| Photon | [s0md3v/Photon](https://github.com/s0md3v/Photon) | `photon` launcher, level/thread/delay/output options. |
| Arjun | [s0md3v/Arjun](https://github.com/s0md3v/Arjun) | Rate limit and `--disable-redirects` support. |
| Nuclei | [ProjectDiscovery installation](https://docs.projectdiscovery.io/tools/nuclei/install) | JSONL, redirect-disable, rate/concurrency and excluded-tag flags. |

After a separate installation, click **Check installed tools** again or run `doctor.py`. Restart the dashboard if its inherited PATH changed. The application checks required help flags before using an adapter; unsupported versions are not treated as working. Tests here use controlled responses rather than public scans. Unsupported tool versions may need a reviewed adapter change.

### HTTPX naming collision

Kali may have **Python HTTPX**, an HTTP client, and **ProjectDiscovery HTTPX**, a host probing utility. They are different programs. Kali's `httpx-toolkit` package may expose a differently named executable. This dashboard requires a `httpx` command that identifies as ProjectDiscovery and has the expected flags. Existing user-managed installations in `~/go/bin` can be used by `run.sh`.

Do not overwrite `/usr/bin/httpx` or delete another program to fix the name. If your package exposes `httpx-toolkit`, a normal-user wrapper can map it explicitly:

```bash
mkdir -p ~/.local/bin
command -v httpx-toolkit
```

Only if that command prints a valid installed path, and no file already exists at `~/.local/bin/httpx`, create a wrapper using a text editor:

```sh
#!/bin/sh
exec /usr/bin/httpx-toolkit "$@"
```

Save as `~/.local/bin/httpx`, check that the actual executable path matches your system, then `chmod +x ~/.local/bin/httpx`. Restart and recheck. If a wrapper already exists, inspect it instead of replacing it.

Python HTTPX মুছবেন না বা `/usr/bin` overwrite করবেন না। আলাদা user wrapper দিয়ে সঠিক tool নির্বাচন করা যায়।

### Photon isolated environment (when Kali does not provide it)

Use a separate tool directory and a separate virtual environment. Select and review an upstream commit first; do not blindly run an unknown script. The following downloads source into a new folder and installs its Python dependencies. It does not execute a scan:

```bash
mkdir -p ~/Tools/02-Custom
cd ~/Tools/02-Custom
git clone https://github.com/s0md3v/Photon.git photon-source
cd photon-source
git rev-parse HEAD
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Record the commit and review dependency changes before updating. Photon dependencies above are upstream-managed and are **not** covered by the dashboard's hash lock. If you already have a working Photon launcher, keep it. Otherwise create `~/.local/bin/photon` in your editor, without overwriting an existing file:

```sh
#!/bin/sh
exec "$HOME/Tools/02-Custom/photon-source/.venv/bin/python" "$HOME/Tools/02-Custom/photon-source/photon.py" "$@"
```

Make it executable with `chmod +x ~/.local/bin/photon`. `doctor.py` should now identify Photon. Run it as a normal user. Crawlers may follow redirects; explicit dashboard inputs are not a strict egress guarantee.

### Templates and data providers

Nuclei needs templates installed separately using its official instructions. This dashboard does not auto-download updates, provision third-party API keys or enable out-of-band interaction. Do not paste API keys into the dashboard or commit them. Template coverage and source-provider availability affect results; missing templates/errors must be reviewed, not interpreted as a clean assessment.

নতুন template, API account বা secret এই dashboard নিজে তৈরি করে না। কোনো key GitHub-এ upload করবেন না।
