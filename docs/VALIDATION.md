# Release validation — 2026-10-24

## 6.2 demo removal and original dark presentation

- Windows suite: 30 tests total; 28 passed, with Linux process groups and privileged directory symlinks skipped. Kali suite: 30 tests total; 29 passed and the Windows process test skipped. Cleanup tests check that real records are byte-for-byte unchanged, redirected scratch roots are refused, and maintenance refuses an active server lock. A history regression keeps older real entries visible behind newer legacy demos.
- Native Windows localhost HTTP checks passed for the dark dashboard, eight official source entries, empty real history, and rejection of removed demo mode and unsupported live assessments.
- Kali Firefox graphical checks confirmed the dark dashboard, adjacent tool-check and download/setup actions, and an open setup dialog with official links. Refreshed local help/identity checks reported all eight existing tools ready; no assessment was started.
- The preserved real report opened with the dark summary cards and collapsible phase layout. Its recorded completion/timeout states remained visible.
- Removed nine explicitly marked legacy demo records from the collaborator's Kali installation and two from the local Windows development data. The existing real Kali history entry was preserved; test fixtures stay in temporary directories.
- Legacy demo job/report routes return 404. Demo generation and its dashboard control are removed. JavaScript syntax and whitespace checks passed.

Older entries below describe the behavior of those historical releases; their demo flows are no longer available in 6.2.

## 6.1.1 automatic browser startup

- Kali desktop: starting `run.sh` opened Firefox automatically at `127.0.0.1:8001`; the dashboard title and version 6.1.1 were confirmed in a VM screenshot.
- Browser opening starts only after this process binds the port and readiness succeeds. Headless/no-browser modes remain available.
- Local Linux and Windows suites: 25 tests total on each; 24 passed and the other platform's process test skipped. Readiness and stop-before-open behavior use a mocked browser, so tests do not open windows.
- Native Windows localhost HTTP startup/demo/report/history/duplicate-instance/live-block checks passed with `--no-browser`.

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
