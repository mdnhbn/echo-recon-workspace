# Release validation — 2026-10-24

Validation was performed with controlled local fixtures and the requesting collaborator's Kali VirtualBox guest. No public target scan was initiated for release validation.

- Python unit/integration tests: **20 passed on Kali Linux** (including Linux process-group cancellation).
- Windows development run: 19 passed; the Linux-only process-group test was skipped.
- Python dashboard packages installed in a new isolated virtual environment using the pinned SHA-256 lock.
- `bash -n install.sh run.sh` passed; `node --check static/app.js` passed.
- Installed Kali executables for all eight adapters passed local help/identity checks. This is not a public-target functional assessment or a guarantee for every upstream release.
- Real localhost HTTP flow tested: session/CSRF, simulated demo, partial/timeout state, HTML and JSON exports, persistent history and cancellation.
- Demo calls neither a scanner nor DNS resolver. A simulated Nuclei timeout deliberately leaves a partial report.

Boundaries and unsupported guarantees are documented in `SECURITY.md`. UI layout is not claimed to have completed a graphical browser review: native browser opening was unavailable during release work. The local HTTP/API flow and rendered HTML were validated separately.
