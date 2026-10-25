# Security model and limits

This is a single-user local assessment application, not a hosted service, network sandbox or security certification.

## Local access and data

- The listener binds only `127.0.0.1:8001`; non-loopback clients and unexpected Host headers are rejected. Do not expose it through a tunnel, reverse proxy, port forward or multi-user host without a separate reviewed authentication design.
- State-changing HTTP requests require the same-site session and CSRF token. Reports escape HTML and use a restrictive content policy.
- Common credential strings are masked best effort. Personal data, unusual secrets and raw Photon crawl files can remain in `data/`. Review/redact exports before sharing; never commit history, logs, reports, `.env`, tokens or venvs.
- Linux private modes do not create equivalent Windows NTFS ACLs. Use a private user-owned location with suitable inherited permissions; keep Windows, WSL and VirtualBox environments/history separate.
- No report is sent to an AI provider. The UI does not request API keys.

## Installation boundary

Default installation/startup can install missing backend tools, but does not start an assessment. Use `--dashboard-only` / `-DashboardOnly` for dashboard-only installation and `--no-tool-setup` / `-NoToolSetup` to skip automatic startup setup.

The setup route accepts only empty CSRF-protected JSON. It launches fixed repository code and arguments; it accepts no target, arbitrary command, path, version or password. Setup checking/installation and assessments are gated against each other. Normal startup uses that same fixed launcher after local help checks. A private, owned `data/auto-setup.json` records identical desktop automatic attempts to avoid failure loops; explicit retries remain available.

Windows uses normal-user, separate versioned environments in `~/Tools/EchoRecon/tooling`. Official release/archive and checksum-manifest hashes are checked where specified; pinned Python sources/dependencies are separate from the dashboard's lockfile. Nmap requires its official installer and the user's legal/admin confirmations; no unattended driver install, privilege elevation or global security/PATH/registry change is performed.

Linux uses the supported distribution's fixed package manager for necessary system packages. Sudo is entered only in the local terminal, never over HTTP. Kali's Go builds use exact module versions; portable Linux assets and source projects have reviewed pins, while some upstream Python dependencies resolve by platform rather than a complete transitive hash lock. OS packages/templates change upstream. No `curl | shell` installer pipe is used.

macOS setup requires an existing native Homebrew installation and Python 3.12+. It runs as the normal user, uses fixed Homebrew formulas for missing Nmap/Nikto, verifies pinned upstream Darwin release archives and keeps Python tools in separate user environments. The dashboard shows the installer's log; it never accepts passwords, shell commands or arbitrary package names. Homebrew packages and Nuclei templates can change upstream; Intel availability follows Homebrew's legacy support tier.

Unknown/incomplete folders, conflicting wrappers and redirected managed paths are preserved. Downloads/pins reduce accidental drift but do not eliminate third-party supply-chain risk. Review installer plans and upstream licenses; tool authors retain control of their programs' behavior.

## Assessment boundary

Only an explicit user action starts an assessment. Exact host scope is validated before scheduling, discovered names do not enlarge active scope, and DNS preflight rejects non-public answers. This does not pin DNS, sandbox tools, prevent every redirect or enforce every downstream request. Third-party services, crawlers and templates may contact secondary destinations or resolve DNS again. Use independently configured egress isolation when strict containment is required.

Rate/output bounds are per adapter or tool/host attempt, not one guaranteed global request budget. There is no wall-clock deadline; use **Stop** to cancel a tool that does not finish. Some DNS/OSINT behavior lacks an equivalent rate knob. Missing/error/timeout/output-limited work cannot become a clean complete assessment.

On Linux and macOS, cancellation terminates the active process group. On native Windows, each tool is created suspended, assigned to a kill-on-close Job Object, then resumed; assignment failure prevents uncontained execution. The job closes on normal completion, cancellation or output limits, including descendants holding pipes after a parent exits. Local process fixtures test this behavior. Abnormal OS shutdown, power loss or tool/OS defects can still require system inspection; history marks interrupted jobs without relaunching arbitrary PIDs.

Native Windows adapters use verified managed command prefixes. Nmap is limited TCP connect/service detection with `-Pn`; UDP, OS/raw-packet modes are not exposed. Local help checks and mocked adapter tests do not certify external provider/API behavior, every operating-system release or the absence of vulnerabilities.

Output caps bound stored evidence, not every file a crawler may write. Review `data/scratch` disk usage after runs. Findings remain unverified until reviewed; a successful process or empty finding list is not proof of security.

## Legacy cleanup and reporting

Production demo generation is removed. Mock data stays in temporary tests. `maintenance.py remove-demo` is an offline command for records explicitly marked as legacy demos: stop the server first, preserve real history and private backups, and never delete the whole data folder merely to clear demos.

Report application problems privately to the repository maintainer without posting credentials or target evidence. For an issue in someone else's system, use that owner's reporting process rather than attaching sensitive evidence to this project.
