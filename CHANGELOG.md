# Changelog

## 6.7.2 — 2026-10-27

- Fix an intermittent native Intel macOS post-exit cleanup failure discovered in the main-branch CI after 6.7.1 publication. Darwin may return EPERM for a zombie-only process group. Verify a fixed system process snapshot before treating that condition as already stopped; live/unknown group permission errors remain errors.
- Keep the full owned-group cleanup, no scan deadline and all audit corrections from 6.7.1. Add regression cases for empty/zombie-only, live, failed and malformed process snapshots.

## 6.7.1 — 2026-10-27

- Clean up the owned POSIX process group after cancellation and normal tool exit, including descendants that ignore SIGTERM and redirect their output. Keep unrelated process groups intact and add native Linux/macOS regressions.
- Create missing parents of the configured user data directory before taking the startup lock, allowing first launch with the APT user's new data path.
- Redact full Authorization/Proxy-Authorization and Cookie/Set-Cookie header values, including folded continuations, before evidence is persisted or exported. Existing saved reports are not rewritten.
- Remove the incompatible `-duc` flag only from explicit Linux/Windows Nuclei template updates; retain disabled automatic updates during tool checks and assessments.
- Add a version guard to the current APT publisher before feed mutation, with Debian version-comparison regressions. Historical workflows lack this guard and must not be rerun to publish old releases. Correct public key verification and contribution/issue documentation.
- Publish a dated English/Bangla project audit with test evidence, dashboard dependency audit and explicit platform/coverage limits. Native macOS support from 6.7.0 remains available.

## 6.7.0 — 2026-10-25

- Add native macOS setup for Apple Silicon and Intel with an existing native Homebrew installation and Python 3.12+. Missing Nmap/Nikto use fixed Homebrew formulas; other backends use verified Darwin release archives or isolated pinned Python sources.
- Route install/startup and the dashboard's Setup all tools action to the macOS installer with visible progress logs. Recognize native Homebrew paths and open the local browser from normal macOS Terminal sessions.
- Add English/Bangla macOS install and Git update guides plus native macOS CI for both processor architectures. Intel backend availability remains subject to Homebrew's legacy support tier.

## 6.6.5 — 2026-10-24

- Correct the live-URL discovery expectation so in-scope URLs keep custom ports without allowing a different hostname into scope.
- Carry forward the 6.6.4 URL-input and no-scan-deadline fixes.

## 6.6.4 — 2026-10-24

- Make the primary URL a first-class form/API input while continuing to accept legacy domain fields. URL-aware tools retain the HTTP(S) page path and any valid port; the authorization scope remains the hostname.
- Remove the subprocess wall-clock deadline from assessment and installed-tool checks. Tools continue until they exit, reach the output cap, or the user presses Stop.
- Keep URL ports when confirming live hosts and when selecting Nikto's HTTP origin.

## 6.6.3 — 2026-10-24

- Accept public HTTP(S) URLs as well as domains; pass the primary URL path to HTTPX, Nuclei, Photon and Arjun, and omit query strings/fragments. Username targets remain unsupported.
- Removed the dashboard's per-tool process deadline and tool-level request timeout flags. Tools run until exit or manual Stop; tools may still report their own network/provider errors. Output and cancellation safeguards remain.
- Added overall and per-tool progress bars, completed/remaining percentages, elapsed time and clearly labelled rough remaining-time estimates where there is enough completed work to estimate.

## 6.6.2 — 2026-10-24

- Removed the full-screen Matrix canvas, rotating header icon, progress pulse, smooth scrolling and report-chevron transition to reduce browser rendering work. Dark/light layouts and all interface controls remain.
- Fixed signed APT publishing so each release replaces the previous feed indexes cleanly.

## 6.6.0 — 2026-10-24

- Added Nikto as the ninth selectable tool and optional standalone check / Nuclei fallback, with bounded tuning categories and per-host time/rate controls.
- Added pinned official Nikto source setup for portable Linux families and native Windows when Perl is already installed; Kali uses its distro package.
- Updated English/Bengali setup, Windows, platform and usage guides; versioned the release for future signed APT packaging.

## 6.3.0 — 2026-10-24

- Added in-app bilingual usage guidance and full English/Bengali guides for every field, rate/timeout semantics, tool behavior and evidence states.
- Added a persisted one-click switch between the original dark and first-v6-style light layouts, with Matrix animation in both and no form reset.
- Added a fixed one-click Kali terminal setup launcher and normal-user installer for missing tools, preserving verified working installations and requiring interactive terminal sudo where needed.
- Setup requests accept no command/path/options, retain CSRF protection and refuse overlapping assessment/setup launches. Native Windows and headless sessions receive Kali/WSL instructions.

## 6.2.0 — 2026-10-24

- Removed production demo generation and visible demo controls; legacy demos are excluded from history/report routes.
- Added an exclusive-lock offline cleanup command that removes only explicitly marked legacy demo jobs and preserves real history.
- Restored the original Echo dark/Matrix dashboard and dark accordion report presentation while retaining scope, cancellation and honest result states.
- Added adjacent tool-check and official download/setup actions, including per-tool setup links for missing/unverified tools.
- Tool checks can refresh after manual installation. No administrator installer is triggered from the dashboard.

## 6.1.1 — 2026-10-24

- Restored automatic browser opening on desktop startup, after binding and readiness checks.
- Added `--no-browser` / PowerShell `-NoBrowser` for headless/test use.
- Browser launch failure is nonfatal and shows the manual localhost address. Headless Linux/WSL does not start a terminal text browser.

## 6.1.0 — 2026-10-24

- Added English/Bengali contribution guides, issue forms, a PR template and a code of conduct.
- Applied the maintainer-selected MIT license while preserving Ahammed's original credit.
- Added native Windows installers/launchers for dashboard/demo/history/report development.
- Added a Windows launcher and bilingual guide for the full Kali WSL2 workflow; native unsupported live assessments are blocked.
- Added Windows single-instance locking and best-effort process-tree cancellation, with platform-specific tests.
- Expanded CI to Linux and Windows on Python 3.11/3.13.

## 6.0.0 — 2026-10-24

- Retained all eight tool adapters; active stages are explicit opt-ins.
- Added honest exit/timeout/missing/cancelled/partial states and JSONL finding parsing.
- Added exact input scope, public-DNS preflight and filtered HTTPX results without automatic target expansion.
- Added bounded subprocess output, process-group cancellation and low supported tool rates.
- Added private SQLite history, interrupted-run recovery and escaped HTML/JSON reports.
- Added loopback-only dashboard, CSRF/Host/client checks, bilingual instructions and a fully simulated demo.
- Removed web-triggered system installation and sudo credential caching from this edition.
- Added hashed Python dependency lock, deterministic local tests and CI.
- No AI provider, authentication for remote hosting, strict egress sandbox or automatic import of old reports is claimed.
