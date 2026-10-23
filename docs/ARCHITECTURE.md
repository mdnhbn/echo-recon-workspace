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
| `echo_recon/web.py` | API, session/CSRF, request boundaries, escaped reports. |
| `echo_recon/security.py` | Exact-host scope, DNS preflight, output URL filtering, best-effort secret masking. |
| `echo_recon/storage.py` | Short-lived SQLite connections and persistent job snapshots. |
| `echo_recon/service.py` | Sequential state machine, cancellation, partial vs complete classification. |
| `echo_recon/tools.py` | Fixed adapters, local executable diagnostics, Nuclei JSONL parsing. |
| `echo_recon/runner.py` | No-shell subprocesses, bounded output, timeout and Linux group termination. |
| `static/`, `templates/` | Bilingual dashboard and report presentation. |

## API

- `GET /`: dashboard and a CSRF session.
- `GET /api/tools`: cached local tool identity/help diagnostics.
- `GET /api/jobs`: latest 50 persisted runs.
- `POST /api/jobs`: local demo or an explicitly scoped assessment. JSON only, CSRF required.
- `GET /api/jobs/<id>`: state, evidence and progress.
- `POST /api/jobs/<id>/cancel`: set cancellation signal; CSRF required.
- `GET /reports/<id>.html` and `.json`: evidence exports. HTML is self-contained.

There is no arbitrary command API, web installer, root/sudo request, remote-agent interface, automatic target expansion or AI integration.

## State semantics

Every phase starts pending, becomes running and finishes with an explicit result. A nonzero tool exit is `error`, even if stdout is empty. Truncated output is not treated as a complete result. The whole assessment is `complete` only when every selected phase is `done`; otherwise it is `partial`, `cancelled`, `error` or `interrupted`. Reports exist for unfinished/partial work too, but never imply complete coverage.

Phases remain sequential. HTTPX filters returned origins against exact scope. Newly discovered subdomains are evidence only. Photon and Arjun require a confirmed live result. Nuclei returns JSONL which is checked against scope and labelled unverified. No stdout line-count guess is used as a vulnerability count.

## Extending an adapter

Change only a fixed adapter, add identity/help requirements, and add tests using controlled `Result` fixtures. Avoid `shell=True`, arbitrary user flags, unbounded output or an external scan in CI. New tools should not silently become default checks. An optional future AI explanation layer must use reviewed/redacted evidence, preserve evidence references and clearly label uncertainty; this version deliberately makes no external AI call.
