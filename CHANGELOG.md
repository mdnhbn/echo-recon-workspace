# Changelog

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
