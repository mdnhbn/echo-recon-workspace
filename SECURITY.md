# Security model and limits

This is a **single-user local assessment application**, not a hosted service, firewall or security certification.

- Binds only `127.0.0.1:8001`; rejects non-loopback clients and unexpected Host headers. Do not expose it through a tunnel, reverse proxy, port forward or multi-user machine without a separate reviewed authentication design.
- State-changing routes require a same-site session and CSRF token. Reports escape HTML and the application sets a restrictive content policy.
- **Setup all tools** accepts only an empty CSRF-protected request and opens the repository's fixed installer in a separate local Kali terminal. It cannot accept commands, paths, versions or sudo credentials from the browser. The installer runs as a normal user and may request sudo interactively for fixed apt packages; passwords are never cached by the application. Assessment and setup launches are gated against each other. Third-party source/dependency downloads retain upstream supply-chain risk; review the fixed plan and pins before installation. Manual official links and refreshable health checks remain available.
- Exact user scope is checked before scheduling; DNS preflight rejects non-public answers. This **does not pin DNS, sandbox a tool, prevent all redirects or enforce every downstream request**. Third-party services, crawlers and templates can have secondary traffic. Use external isolation when strict scope containment is required.
- Limits apply per tool/host; some DNS/OSINT behavior has no comparable request-rate knob. One job at a time does not equal a complete network traffic budget.
- Stop and normal Ctrl+C/SIGTERM cancel the Linux process group. Power loss, SIGKILL, detached grandchildren or a server crash can leave orphan processes; inspect the system after abnormal shutdown. History marks old jobs interrupted but does not automatically relaunch or kill arbitrary PIDs.
- Output caps bound stored evidence, not every file an external crawler may write. Review `data/scratch` disk usage after large runs. Private local evidence is not automatically deleted.
- Common credential strings are masked best-effort. Personal data, unusual secrets and Photon raw files can remain. Review/redact before export or publication. Do not commit `data`, `.env`, logs, tokens or real scan reports.
- No results are sent to an AI service. No API keys are requested in the UI.
- Native Windows supports dashboard/history/reports, not live scanner execution. Use Kali WSL2 for the Linux toolchain. Windows uses inherited NTFS permissions; Unix `chmod` calls do not establish a private Windows ACL. Keep native and WSL environments/data separate and in private user-owned locations.
- Production demo generation is removed. Test fixtures belong only in temporary directories. `maintenance.py remove-demo` is an offline operation for explicitly marked legacy demo records; stop the server first and preserve real assessment history. Do not use a blanket data-directory deletion to remove demos.
- Third-party tools/templates may be incompatible, unavailable or wrong. Human validation is necessary. A completed command or an empty finding list is not proof of security.

Report an application issue to the repository maintainer without posting credentials or target evidence publicly. For a discovered issue in someone else's system, follow that owner's reporting process rather than attaching it to this project.
