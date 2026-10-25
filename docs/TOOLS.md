# Backend tool setup / নয়টি টুল একসঙ্গে সেটআপ

[Install and run](../README.md) · [বাংলা নির্দেশনা](../README.bn.md) · [Windows / WSL](WINDOWS.md) · [macOS](MACOS.md) · [Usage](USAGE.md)

These are nine independent third-party tools with their own licenses and dependencies. The repository installs missing backends together and preserves tools that already pass local help/identity checks. Downloading source, finishing installation and passing a local check are different steps. No installer accepts a target or starts an assessment.

## Automatic installation

- **Install entry point:** `bash install.sh` or `.\install.ps1` creates the dashboard venv and sets up backends. Use `--dashboard-only` / `-DashboardOnly` for the dashboard alone.
- **Normal app startup:** local checks run asynchronously. Missing backends use the fixed setup launcher. Ready tools cause no download. Desktop automatic attempts are recorded privately so identical failures do not reopen setup on every restart; **Setup all tools** is the deliberate retry.
- **Linux desktop:** a visible local terminal opens. Fixed OS package installation may ask for sudo there.
- **Headless Linux/WSL:** `run.sh` uses the same interactive terminal for CLI setup; it rechecks ready tools on subsequent runs. Use `--no-tool-setup` to skip that step.
- **Windows:** the seven original compatible backends install as a normal user, with progress in the dashboard. Nikto's pinned source also installs when Strawberry Perl is already on PATH. Nmap requires its official Windows installer and the user's license/administrator confirmations; Perl itself is a separate manual prerequisite.
- **macOS:** native Apple Silicon/Intel setup uses an already installed Homebrew and Python 3.12+. Nmap/Nikto use fixed Homebrew formulae only when missing; seven other tools use pinned official Darwin releases or isolated Python environments. Dashboard setup shows the worker log. Follow the [macOS prerequisite guide](MACOS.md); Homebrew itself is not installed unattended.
- **Check installed tools:** refreshes local health. A displayed error or incomplete setup is not success.

বাংলায়: installer একসঙ্গে কাজগুলো করে, কিন্তু tool ইনস্টল হলেই scan হয় না। ঠিক থাকা tool আবার নামায় না। Windows-এর progress dashboard-এ, Linux desktop-এর progress আলাদা Terminal-এ দেখা যায়। Sudo password শুধু ওই Terminal-এ দিন। একই desktop automatic চেষ্টা ব্যর্থ হলে error পড়ে **Setup all tools** চাপুন; শুধু restart দিয়ে সমস্যাটি ঢাকবেন না।

## Fixed manual commands

Finish/stop any assessment before installing. Run as your normal user.

**Native Windows, Python 3.12 x64:**

```powershell
.\.venv\Scripts\python.exe setup_tools_windows.py --plan
.\.venv\Scripts\python.exe setup_tools_windows.py --install
.\.venv\Scripts\python.exe doctor.py
```

**Linux / WSL, from the Linux repository:**

```bash
export PATH="$HOME/.local/bin:$HOME/go/bin:/usr/local/go/bin:$PATH"
.venv/bin/python setup_tools.py --plan
.venv/bin/python setup_tools.py --install
.venv/bin/python doctor.py
```

**Native macOS, from a native Terminal:**

```bash
.venv/bin/python setup_tools_macos.py --plan
.venv/bin/python setup_tools_macos.py --install
.venv/bin/python doctor.py
```

Use `bash install.sh` / `bash run.sh` for normal installation and launch; they select the native macOS setup and tool paths. See [MACOS.md](MACOS.md) or [বাংলা macOS guide](MACOS.bn.md).

Default/`--plan` is read-only: it prints sources and local paths without probing help, running commands, downloading or writing. `--install` performs the actual fixed setup. The browser API accepts no custom commands, paths, versions or passwords. Never use `sudo python setup_tools.py`; the normal-user installer invokes the needed package manager separately.

To suppress automatic startup installation: `bash run.sh --no-tool-setup`, `.\run.ps1 -NoToolSetup` or `python app.py --no-tool-setup`. Explicit setup controls remain available.

## Platform-specific storage and prerequisites

| Platform | Installation method and location |
|---|---|
| Windows x64 | Python **3.12 x64**; separate versioned folders under `~/Tools/EchoRecon/tooling`. Three official ProjectDiscovery Windows ZIPs have pinned archive/checksum-manifest hashes; Python tool sources and runtime pins live in `setup_tools_windows.py`. No global PATH/profile/registry change. |
| Native macOS arm64/x86_64 | Python **3.12+** and native Homebrew already installed under `/opt/homebrew` (Apple Silicon) or `/usr/local` (Intel). Missing Nmap/Nikto use Homebrew; other backends use versioned `~/.local/share/echo-recon/tooling` folders and `~/.local/bin` launchers. Existing working tools are kept. Current Homebrew OS/architecture support and package availability apply. |
| Kali Linux | Fixed distro packages for DNSRecon, theHarvester and Nmap. Go **1.26+** for missing compiled Go tools; exact public Go module versions/checksums. Isolated Python environments for Arjun/Photon. |
| Other supported glibc Linux | Debian/Ubuntu `apt`, Fedora/RHEL `dnf`, Arch `pacman`, openSUSE `zypper`. Nmap/necessary prerequisites use the fixed distro package manager. Official Linux x86_64/aarch64 ProjectDiscovery ZIPs use the reviewed checksum manifest. Pinned DNSRecon/theHarvester source installs require Python **3.12+**; their upstream dependencies resolve for that interpreter/platform from PyPI. |
| Linux managed storage | `~/.local/share/echo-recon/tooling`, with exact installer-owned wrappers in `~/.local/bin`. Working system executables remain in place. |
| Other distro/architecture | Manual compatible upstream installation. Alpine/musl is not an automatic portable-install target. |

Other-distro package-manager/download paths are covered by mocked tests; fresh end-to-end installation on every distribution is not claimed. OS repositories, PyPI, data providers and templates may change or be unavailable. Dashboard dependency hashes do not lock every external tool/transitive dependency.

Unrelated files, unknown ownership markers, symlinks/junctions, conflicting wrappers and incomplete version folders are preserved. Read the reported path and inspect it before deciding what to move yourself. Do not move an existing Python venv to another folder: entry points can embed absolute paths. An old Windows install under virtualized AppData is left in place; setup creates the missing environments at the stable user path.

## Nmap on Windows

Use [Nmap's official Windows installer](https://nmap.org/download.html). License/admin confirmation is an interactive user step; this helper does not launch drivers or accept agreements unattended. After installation, **Setup all tools** can skip Nmap and complete its final checks.

The native adapter runs limited TCP connect/service detection (`-sT -sV`, top 100 ports) with `-Pn`, so this path avoids raw-packet host discovery. It does not provide UDP/OS/raw-packet modes. Installing Npcap or elevating the dashboard is not part of this setup.

## Interpret readiness

| Status | Meaning | What to do |
|---|---|---|
| `ready` | Local identity/help checks passed, including required adapter flags; Nuclei also reports its local official template version. | This does not verify every template file or provider. Select only the checks needed; it is not a full compatibility or security audit. |
| `missing` | No suitable command was found in the server's managed paths/PATH. | Install in that same environment and recheck. |
| `unverified` | A command exists but identity/help requirements failed. | Inspect its path/version before reinstalling. |

Run `doctor.py` with the environment's venv Python to see resolved paths/commands. Help checks are local; upstream programs still control their own help/version behavior.

**HTTPX:** ProjectDiscovery HTTPX is the required probing tool. Python HTTPX is a separate HTTP client with the same command name. Managed native Windows prefixes take priority without changing PATH. On Linux, inspect `command -v httpx` and the tool guide before creating any normal-user wrapper. Do not delete Python HTTPX or overwrite `/usr/bin/httpx`.

## Official tools

| Tool | Official source | Adapter purpose |
|---|---|---|
| DNSRecon | [darkoperator/dnsrecon](https://github.com/darkoperator/dnsrecon) | Standard DNS records for the primary domain. |
| Subfinder | [ProjectDiscovery/subfinder](https://github.com/projectdiscovery/subfinder) | Public-source subdomain discovery; results do not expand active scope. |
| HTTPX | [ProjectDiscovery/httpx](https://github.com/projectdiscovery/httpx) | Live origins, bounded requests/concurrency and exact returned-host filtering. |
| Nmap | [Nmap downloads](https://nmap.org/download.html) | Limited TCP connect/service detection. |
| theHarvester | [laramies/theHarvester](https://github.com/laramies/theHarvester) | Configured `crtsh,otx` information sources. |
| Photon | [s0md3v/Photon](https://github.com/s0md3v/Photon) | Shallow crawl of HTTPX-confirmed scoped hosts. |
| Arjun | [s0md3v/Arjun](https://github.com/s0md3v/Arjun) | HTTP parameter discovery with bounded adapter settings. |
| Nuclei | [ProjectDiscovery/nuclei](https://github.com/projectdiscovery/nuclei) | Selected-severity template checks; findings require human verification. |
| Nikto | [sullo/nikto](https://github.com/sullo/nikto) | Selected web-server checks; GPL-3.0-only source stays separate and keeps its own license. |

Select both Nuclei and Nikto to use Nikto as a fallback: it runs only if the Nuclei phase is missing, unverified or fails. A completed Nuclei phase does not trigger fallback, even when it reports no matches. Select Nikto without Nuclei to run it by itself. The adapter checks only Nikto tuning groups **1, 2, 3 and b** (interesting files, misconfiguration/default files, information disclosure and software identification); it excludes the other groups. These are active web requests and can be visible in server logs. Use it only on exact hosts you are authorized to assess.

On Kali, the setup uses the distro's `nikto` package. Other supported Linux package families install Perl prerequisites and the pinned official Nikto 2.6.1 source. Native macOS uses the official Homebrew `nikto` formula and its dependencies. Native Windows setup needs Strawberry Perl already installed and `perl.exe` on `PATH`; Echo Recon downloads the pinned source but does not install the Perl runtime for you. Nikto's own license remains separate from Echo Recon's MIT license.

Fixed releases/commits and their pins are visible in the installer source. Keep original license notices when contributing or redistributing.

## Templates, accounts and retry

New Nuclei engines download current official templates; existing ready engines/templates are kept by default. The readiness check separately reads Nuclei's local template version without updating or scanning. If its engine is healthy but the template version is missing or cannot be checked, **Setup all tools** retries only the official template download rather than reinstalling the Nuclei engine. This confirms the version metadata, not every template file or upstream provider. An explicit refresh is:

```bash
.venv/bin/python setup_tools.py --install --update-templates
```

Windows equivalent:

```powershell
.\.venv\Scripts\python.exe setup_tools_windows.py --install --update-templates
```

macOS equivalent:

```bash
.venv/bin/python setup_tools_macos.py --install --update-templates
```

Templates are changing upstream content, not a pinned template snapshot or saved findings. Installation does not create paid accounts/API keys or enable out-of-band interaction. Configure needed accounts privately with the upstream tool's own instructions; do not paste secrets in the dashboard or commit them.

If setup fails, read its progress, fix the stated Python/package/path/network issue, then use **Setup all tools** or the CLI `--install` command. Exit zero/final local checks is installation evidence, not proof that every template file, provider or assessment works. Do not treat missing templates or failed providers as a clean security result.
