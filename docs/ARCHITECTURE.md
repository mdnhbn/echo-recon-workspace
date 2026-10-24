# Architecture

```text
Browser (127.0.0.1:8001)
  │ same-origin session + CSRF
  ▼
Flask API ── input/scope validation ── one assessment manager
                                      │
                                      ├─ fixed tool adapters (no shell)
                                      ├─ bounded process runner + cancel event
                                      └─ SQLite state + redacted evidence
                                               │
                                               └─ HTML / JSON report
```

| File | Responsibility |
|---|---|
| `app.py` | Normal-user entry point; loopback listener; graceful signal handling. |
| `echo_recon/locking.py` | Cross-process Linux/Windows instance lock, acquired before history recovery. |
| `echo_recon/web.py` | API, session/CSRF, request boundaries, escaped reports. |
| `echo_recon/security.py` | Exact-host scope, DNS preflight, output URL filtering, best-effort secret masking. |
| `echo_recon/storage.py` | Short-lived SQLite connections and persistent job snapshots. |
| `echo_recon/service.py` | Sequential state machine, cancellation, partial vs complete classification. |
| `echo_recon/tools.py` | Fixed adapters, local executable diagnostics, Nuclei JSONL parsing. |
| `echo_recon/runner.py` | No-shell subprocesses, bounded output, timeout and Linux group termination. |
| `maintenance.py` | Offline cleanup of explicitly marked legacy demo jobs while the server is stopped. |
| `setup_tools.py` | Fixed normal-user Kali installer; isolated third-party tools; interactive terminal sudo. |
| `echo_recon/setup_launcher.py` | No-argument local terminal launcher and setup/assessment scheduling guard. |
| `static/`, `templates/` | Original-style dark bilingual dashboard, tool-setup guidance and evidence report presentation. |

## API

- `GET /`: dashboard and a CSRF session.
- `GET /api/tools`: cached local tool identity/help diagnostics. `?refresh=1` reruns the local checks after manual tool setup.
- `GET /api/tool-sources`: fixed official download/setup metadata.
- `POST /api/setup-tools`: empty JSON only, CSRF required; opens the fixed installer in a local Kali desktop terminal. Passwords are entered there, never sent to HTTP.
- `GET /api/jobs`: latest 50 persisted runs.
- `POST /api/jobs`: an explicitly scoped assessment. JSON only, CSRF required. Demo-generation requests are not supported.
- `GET /api/jobs/<id>`: state, evidence and progress.
- `POST /api/jobs/<id>/cancel`: set cancellation signal; CSRF required.
- `GET /reports/<id>.html` and `.json`: evidence exports. HTML is self-contained.

The **Download / setup tools** control exposes official sources and guidance. **Setup all tools** opens only the bundled installer with fixed arguments in a local Kali terminal. The installer skips ready tools, uses isolated user environments for custom tools, and can request sudo interactively for apt packages. There is no arbitrary command API, browser password prompt, stored sudo session, remote-agent interface, automatic target expansion or AI integration. A desktop terminal, Kali Linux and the same normal-user session are required; headless users run the fixed CLI themselves.

`static/theme.js` switches the shared dashboard DOM between dark and first-v6-style light layouts; browser-local storage remembers the choice without creating jobs or resetting the form. Both use the same reduced-motion-aware Matrix canvas. `templates/usage.html` and the bilingual usage documents explain form and result semantics.

Native Windows mode supports dashboard/history/report development and rejects live assessments server-side. Full Linux tool execution on Windows uses Kali WSL2 and a separate Linux environment. See `docs/WINDOWS.md`.

## Production data and legacy cleanup

The application does not generate demo jobs or preload sample history. Mock scanner and report fixtures are confined to temporary test directories. Existing real jobs remain in SQLite and keep their evidence exports.

With the server stopped, `.venv/bin/python maintenance.py remove-demo` removes only legacy records whose saved demo flag is explicitly true. A domain name, incomplete status or simulated-looking evidence is not a deletion criterion. Never delete the whole database or run a second manager to clean an active server: an active worker may save its snapshot again. Keep private backups out of Git.

## State semantics

Every phase starts pending, becomes running and finishes with an explicit result. A nonzero tool exit is `error`, even if stdout is empty. Truncated output is not treated as a complete result. The whole assessment is `complete` only when every selected phase is `done`; otherwise it is `partial`, `cancelled`, `error` or `interrupted`. Reports exist for unfinished/partial work too, but never imply complete coverage.

Phases remain sequential. HTTPX filters returned origins against exact scope. Newly discovered subdomains are evidence only. Photon and Arjun require a confirmed live result. Nuclei returns JSONL which is checked against scope and labelled unverified. No stdout line-count guess is used as a vulnerability count.

## Extending an adapter

Change only a fixed adapter, add identity/help requirements, and add tests using controlled `Result` fixtures. Avoid `shell=True`, arbitrary user flags, unbounded output or an external scan in CI. New tools should not silently become default checks. An optional future AI explanation layer must use reviewed/redacted evidence, preserve evidence references and clearly label uncertainty; this version deliberately makes no external AI call.
