# Release validation — 2026-10-24

## 6.1 Windows and contribution update

- Local Windows: 23 tests total; 22 passed and the Linux-only process test skipped. Windows child-tree cancellation and cross-process instance locking passed.
- Kali Linux: 23 tests total; 22 passed and the Windows-only process test skipped.
- Native `install.ps1` installed the hash-locked dashboard packages successfully into its own `.venv`.
- Real native Windows HTTP flow verified: startup, simulated demo, HTML/JSON exports, saved history, duplicate-instance refusal and rejection of unsupported live scans.
- All three PowerShell launchers parse. The exact fixed WSL command remains one argument under Windows PowerShell 5.1 and PowerShell 7, checked with a harmless argv fixture.
- WSL itself was not installed or provisioned as part of these checks; the full Kali WSL networking/toolchain path is documented, not represented as end-to-end validated here.
- CI now checks Ubuntu and Windows on Python 3.11 and 3.13. See the repository's Actions tab for the current commit's result.

## Original 6.0 validation

Validation was performed with controlled local fixtures and the requesting collaborator's Kali VirtualBox guest. No public target scan was initiated for release validation.

- Python unit/integration tests: **20 passed on Kali Linux** (including Linux process-group cancellation).
- Windows development run: 19 passed; the Linux-only process-group test was skipped.
- Python dashboard packages installed in a new isolated virtual environment using the pinned SHA-256 lock.
- `bash -n install.sh run.sh` passed; `node --check static/app.js` passed.
- Installed Kali executables for all eight adapters passed local help/identity checks. This is not a public-target functional assessment or a guarantee for every upstream release.
- Real localhost HTTP flow tested: session/CSRF, simulated demo, partial/timeout state, HTML and JSON exports, persistent history and cancellation.
- Demo calls neither a scanner nor DNS resolver. A simulated Nuclei timeout deliberately leaves a partial report.

Boundaries and unsupported guarantees are documented in `SECURITY.md`. UI layout is not claimed to have completed a graphical browser review: native browser opening was unavailable during release work. The local HTTP/API flow and rendered HTML were validated separately.
