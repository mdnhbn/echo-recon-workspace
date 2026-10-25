# Architecture

```text
Normal-user CLI / launcher
  ├─ dashboard dependency setup
  └─ startup local tool checks → fixed platform setup when missing
                                   │
Browser (127.0.0.1:8001)             ├─ Windows user-local worker + bounded log
  │ same-origin session + CSRF      └─ Linux terminal / fixed OS packages
  ▼
Flask API → input/scope validation → one assessment manager
                                      ├─ fixed tool adapters (no shell)
                                      ├─ output-capped runner + cancellation (no assessment deadline)
                                      └─ SQLite snapshots + redacted evidence
                                                     └─ HTML / JSON report
```

## Components

| File | Responsibility |
|---|---|
| `app.py` | Normal-user entry point; bind loopback before browser/setup startup; signals; `--no-tool-setup`; optional per-user data directory for packages. |
| `echo_recon/bootstrap.py` | Asynchronous help checks, skip-ready behavior and owned automatic-attempt fingerprints. Cancels checking on shutdown without terminating installation. |
| `echo_recon/locking.py` | POSIX/Windows instance lock acquired before history recovery; shared setup lock. |
| `echo_recon/web.py` | Local/Host boundaries, session/CSRF, fixed setup routes and escaped reports. |
| `echo_recon/setup_launcher.py` | Startup-check state, fixed platform launch, setup/assessment mutual exclusion and bounded setup log/status. |
| `setup_tools_windows.py` | Normal-user x64 Windows setup; fixed verified assets, separate Python environments and explicit managed command resolution. |
| `setup_tools.py` | Kali package/Go setup plus supported portable Linux/package-manager families; fixed terminal sudo calls. |
| `setup_tools_macos.py` | Native Apple Silicon/Intel paths; fixed Homebrew Nmap/Nikto formulas, verified macOS release archives and isolated Python source environments. |
| `packaging/`, `.github/workflows/publish-apt.yml` | Build an architecture-independent Debian package and publish version-tagged releases to a signed static APT feed. |
| `echo_recon/security.py` | Domain/HTTP(S)-URL parsing, exact-host scope, public DNS preflight, returned URL filtering and best-effort redaction. |
| `echo_recon/tools.py` | Fixed argv adapters, identity/help diagnostics and scoped Nuclei JSONL parsing. |
| `echo_recon/runner.py` | No-shell processes, capped combined output, manual cancellation, POSIX process groups and suspended Windows Job Object containment. Assessment processes have no elapsed-time deadline. |
| `echo_recon/service.py` | Sequential state machine, cancellation and complete/partial classification. |
| `echo_recon/storage.py` | Short-lived SQLite connections and persistent snapshots. |
| `maintenance.py` | Stopped-server cleanup of explicitly marked legacy demo jobs. |
| `static/`, `templates/` | Shared bilingual dashboard/report DOM, setup progress, guidance and dark/light Matrix layouts. |

## Setup lifecycle

Installation scripts create the local dashboard venv and request backend setup unless dashboard-only is selected. Startup also checks tools asynchronously after the loopback socket binds. Ready backends are retained. If an owned automatic-attempt fingerprint already covers the same application/platform/Python/missing-tool set, the app explains how to retry explicitly instead of reopening the same failed desktop setup on every restart.

The optional Kali APT package places application code in `/usr/lib/echo-recon` and uses the normal user's XDG data directory for SQLite history, locks and setup state. A package upgrade replaces only application files. Scanner backends remain user-local. The signed feed updates only when a matching version tag is published; a plain Git checkout continues to use `git pull` and its own project-local `data/` folder.

Startup and manual setup share the launcher's guard; assessments cannot race into a pending tool check or running setup. The automatic record is private `data/auto-setup.json`, with a bounded strict schema and atomic writes. Unrecognized/redirected state is left untouched. A deliberate setup button/CLI retry is independent of this record.

Windows starts a fixed hidden worker and exposes its bounded log in the dashboard. Managed backends live in `~/Tools/EchoRecon/tooling`, outside AppData virtualization. Each tool has fixed metadata/source pins; metadata cannot supply arbitrary executable paths. Nmap remains the official interactive installer exception.

macOS also starts a fixed logged worker, using the existing native Homebrew installation without sudo or AppleScript. Its managed backends use `~/.local/share/echo-recon/tooling` and `~/.local/bin`. Native Homebrew prefixes are selected by architecture; Rosetta and conflicting/incomplete environments require manual attention. Install/run scripts use native Python 3.12+; source-checkout updates use Git.

Linux desktop setup opens a fixed terminal command. Headless `run.sh` runs setup directly in the existing terminal for sudo visibility and starts the app with duplicate startup setup suppressed. Supported package-manager families have fixed OS-package allowlists; incompatible distributions/architectures receive an explicit manual action. No password passes through HTTP, no arbitrary installer API exists, and setup accepts no scan target.

## API

- `GET /`: dashboard and CSRF session.
- `GET /api/tools`: cached local identity/help diagnostics; `?refresh=1` refreshes.
- `GET /api/tool-sources`: fixed official download/setup metadata.
- `POST /api/setup-tools`: empty JSON only, CSRF required; fixed installer.
- `GET /api/setup-status`: read-only startup/setup state, exit code and bounded plain-text log.
- `GET /api/jobs`: recent real saved runs; legacy demos are hidden.
- `POST /api/jobs`: explicit scoped assessment; CSRF/JSON required.
- `GET /api/jobs/<id>`: progress/evidence.
- `POST /api/jobs/<id>/cancel`: cancellation signal; CSRF required.
- `GET /reports/<id>.html` and `.json`: saved evidence exports.

These routes retain local access checks. No remote-agent interface, arbitrary flags, credential endpoint, automatic target expansion or external AI integration is provided.

## Process and state semantics

Phases are sequential. A nonzero exit is an error even with empty stdout. Output truncation and manual cancellation remain explicit; legacy reports can still show timeout. An assessment is complete only when all selected phases are done; interrupted/partial reports still expose available evidence and never imply full coverage.

Windows tools start suspended, join a kill-on-close Job Object before tool code runs, and resume only after assignment succeeds. Linux/macOS use a process group. Bounded output/pipes and cancellation apply across native adapter prefixes. If containment setup fails, the tool does not run uncontained.

HTTPX filters origins against exact scope; discovery is evidence only. Photon/Arjun require a live scoped host from the same run. Nmap uses limited top-100 TCP connect/service detection, with Windows `-Pn`. Nuclei JSONL is filtered to scope and labelled unverified. Nikto uses one in-scope web origin per explicit host and bounded tuning groups; when both Nuclei and Nikto are selected, Nikto runs only after the Nuclei phase is incomplete or fails. A stdout line count is not a vulnerability count.

Tool readiness is a local help/identity result, not an external network/API or provider compatibility certification. Other Linux installer branches use mocked package-manager/download tests; actual fresh installation on every distro is not claimed.

## Presentation, data and extension

`static/theme.js` switches the shared DOM without resetting form values/jobs; local browser storage remembers the choice. Both layouts are static and omit the Matrix canvas and motion effects to reduce browser work. The bilingual [usage guides](USAGE.md) explain field/rate/time/report semantics.

Production does not create demo jobs or preload findings. Mock fixtures stay in temporary directories. Offline legacy cleanup only removes explicitly flagged demos while the server is stopped; it cannot relaunch a manager or infer deletion from a domain/status.

To extend a tool, change a fixed adapter and identity requirements, then add controlled fixtures and suitable local process tests. Avoid arbitrary user flags, `shell=True`, unbounded output or public scans in CI. New checks must not silently become defaults. Preserve MIT/original attribution and follow [CONTRIBUTING.md](../CONTRIBUTING.md).
