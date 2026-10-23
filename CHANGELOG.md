# Changelog

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
