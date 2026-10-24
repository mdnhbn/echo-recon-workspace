# Using Echo Recon, step by step

**[বাংলা নির্দেশনা](USAGE.bn.md)** · [Installation](../README.md) · [Tool setup](TOOLS.md) · [Windows / WSL](WINDOWS.md)

Echo Recon is a local dashboard that runs nine separate assessment tools in a fixed order and saves their evidence. Opening the dashboard does not start a scan. This guide uses `example.com` only to explain the fields: **replace it with a domain you own or have explicit permission to assess. Do not start a run against the example addresses.**

## 1. Open the dashboard

In your Kali terminal, go to your installed project folder and run:

```bash
cd ~/Tools/02-Custom/echo-recon-workspace
bash run.sh
```

Keep that terminal open. Firefox should open **http://127.0.0.1:8001**. If it does not, enter that address manually. This is the dashboard's address on your own Kali machine; it is not the domain you put in the assessment form.

Run as your normal user. The dashboard refuses root on Linux. Native Windows has its own verified managed tool prefixes and adapters; WSL remains a separate optional Linux environment. Windows uses `install.ps1` / `run.ps1`; other supported Linux families use the Linux scripts with their own prerequisites. See [WINDOWS.md](WINDOWS.md) and [TOOLS.md](TOOLS.md).

### Switch between the two layouts

The header's **Light layout / হালকা** button switches the dashboard to the light layout. It then reads **Dark layout / ডার্ক**; click again to return to the dark layout. The button names the layout you will switch to, not the current one.

Changing the layout keeps your form values, running job and displayed results in place. The choice is remembered for this dashboard address in the same browser when local browser storage is available. A new browser/profile, cleared storage or blocked storage may start with the default dark layout. Another open tab for the same address follows the saved choice when browser storage events are available.

Both layouts use a static background; the Matrix canvas, rotating icon, progress pulse and smooth scrolling are removed to reduce browser resource use. The Light/Dark switch changes dashboard presentation, not scan settings. For the built-in instructions, click **How to use / ব্যবহারবিধি** in the header or **Full usage guide / বিস্তারিত নিয়ম** in the sidebar.

## 2. Automatic setup and checking the tools

The default installer sets up the dashboard and missing backends together. Normal desktop startup also checks local tools asynchronously and starts the fixed setup when needed. Headless Linux/WSL uses the launcher's existing terminal so sudo prompts stay visible. Installing tools does not start an assessment.

1. Read **Tool health** / **Download / Setup** progress. Windows installs the seven original compatible backends and installs Nikto source when Strawberry Perl is on PATH; Nmap uses its official Windows installer and your license/admin confirmations. Linux desktop setup opens a supported visible terminal.
2. Enter sudo only in the Linux terminal when the fixed package manager requests it. Never send a password to the dashboard or a chat. Close the finished setup terminal before starting an assessment.
3. Wait for completion or a clear error. An opened terminal/downloaded source is not proof of installation. Existing unrelated/incomplete folders are preserved for inspection rather than overwritten.
4. Click **Check installed tools**. The main cards and open setup popup refresh their states together.
5. If desktop automatic setup previously failed for the same missing-tool set, the private attempt record prevents an identical restart loop. Read/fix the error and use **Setup all tools** for a deliberate retry. Headless CLI startup rechecks tools; use the opt-out below if you need to skip it.

| State | Meaning | Next step |
|---|---|---|
| `ready` | Matching identity/help and required adapter flags passed locally; Nuclei also reports its local official template version. | This does not validate every template file or provider. Select only needed checks and review results. |
| `missing` | No suitable command was found in managed paths/PATH. | Set up the tool in the same environment as this server, then recheck. |
| `unverified` | A command exists but identity/help requirements failed. | Inspect its resolved path/version before reinstalling. |

**HTTPX:** the adapter needs ProjectDiscovery HTTPX, not the Python HTTPX client. Do not delete another program or overwrite a system executable to fix a naming conflict.

### Preview or retry from a terminal

Finish/stop any assessment first. From the repository, as your normal user:

**Linux / WSL:**

```bash
.venv/bin/python setup_tools.py --plan
.venv/bin/python setup_tools.py --install
.venv/bin/python doctor.py
```

**Native Windows, Python 3.12 x64:**

```powershell
.\.venv\Scripts\python.exe setup_tools_windows.py --plan
.\.venv\Scripts\python.exe setup_tools_windows.py --install
.\.venv\Scripts\python.exe doctor.py
```

Default/`--plan` prints the fixed plan without running commands/help checks, downloading or writing. `--install` performs setup and accepts no target. Never run the full installer with sudo; only fixed OS package operations request elevation in their terminal. See [TOOLS.md](TOOLS.md) for supported package managers, architectures and Python requirements.

New Nuclei engines download official templates; existing ready engines/templates are kept unless an explicit template update is requested. **Check installed tools** confirms Nuclei's local engine identity and reports an official template version when present. If the version is missing or cannot be checked, **Setup all tools** refreshes templates without reinstalling the engine. This local check does not validate every template file, provider access or assessment results. Setup does not create paid accounts or API keys.

For dashboard-only installation use `bash install.sh --dashboard-only` or `.\install.ps1 -DashboardOnly`. To skip automatic setup on launch use `bash run.sh --no-tool-setup`, `.\run.ps1 -NoToolSetup` or `python app.py --no-tool-setup`. Browser suppression is separate: `--no-browser` / `-NoBrowser`.

## 3. Fill in the form

### Primary domain

Enter a permitted domain or public HTTP(S) page URL. If you enter `https://example.com:8443/help`, URL-aware tools receive the page path and port; domain-level checks use `example.com`. Query strings and fragments are dropped. Usernames, IPs and wildcards are rejected. A username is not a supported target.

| Entry | Accepted? | Why |
|---|---|---|
| `example.com` | Yes, as a hostname format | Replace with your authorized domain. |
| `app.example.com` | Yes, as a hostname format | If it is primary, only that name and its own subdomains can be in scope. |
| `https://example.com/help` | Yes | HTTPX, Nuclei, Photon and Arjun use its path; domain-level checks use the hostname. |
| `http://example.com` | Yes | Standard HTTP is accepted too. |
| `https://example.com:443/help` | Yes | The default HTTPS port is kept. |
| `https://example.com:8443/help` | Yes | URL-aware tools keep the explicitly supplied port. |
| `https://name:secret@example.com` | No | URLs with credentials are rejected. |
| `*.example.com` | No | Wildcards are not supported. |
| `127.0.0.1`, `192.168.1.10`, `localhost` | No | IP addresses and local hosts are not accepted live targets. |

The live scanner requires hostnames that resolve only to public IP addresses. A hostname that resolves to private/reserved addresses is rejected. The local dashboard address is therefore not a target to paste into the form.

### Additional authorized hosts

The primary hostname is extracted from the target and included automatically. Leave this list blank to assess only that host. Or list up to **four additional exact subdomains** you are authorized to assess, one hostname or public HTTP(S) URL per line; the application uses only each hostname for authorization. Five hosts total is the maximum.

For example, the form structure would be:

**Primary domain:**

```text
example.com
```

**Additional authorized hosts (optional):**

```text
app.example.com
```

Replace the example with a subdomain you are authorized to assess before starting. Do not add a subdomain merely because it appears in a result: check ownership/permission first. If you authorize only the primary domain, leave this field blank. A separately owned domain cannot be added to this run; it needs its own assessment.

Discovery does not automatically enlarge scope. This input control is also **not a network firewall**: third-party tools may resolve DNS again or contact secondary services and destinations. Use a separately isolated environment if you require strict network containment.

### Select checks

The first three checks are preselected. The others are optional. The selected checks run in the order below, even if you click their boxes in a different order.

| Order | Form label / tool | What this adapter does | Which names it receives |
|---|---|---|---|
| 1 | DNS records — DNSRecon | Reads standard DNS records. | Primary domain. |
| 2 | Subdomains — Subfinder | Collects subdomain names through discovery sources. Newly found names are evidence, not automatic active targets. | Primary domain. |
| 3 | Live hosts — ProjectDiscovery HTTPX | Checks for responding web origins. A response does not prove an application is safe or fully working. | Each exact scoped host. |
| 4 | Ports & services — Nmap | TCP connect and limited service checks on the top 100 ports, not all 65,535 ports. | Each exact scoped host. |
| 5 | Public-source research — theHarvester | Queries the configured `crtsh` and `otx` public-information sources. Their availability affects results. | Primary domain. |
| 6 | Shallow web crawl — Photon | Crawls one level using a single worker and a configured delay. | Scoped hosts confirmed live by HTTPX in this same run. |
| 7 | HTTP parameters — Arjun | Looks for HTTP input parameters using one worker and the adapter's bounded settings. | Scoped hosts confirmed live by HTTPX in this same run. |
| 8 | Template checks — Nuclei | Runs available low/medium/high/critical templates with selected high-impact categories excluded and out-of-band interaction disabled. Matches require verification. | Each exact scoped host. |
| 9 | Web-server checks — Nikto | Checks tuning groups 1, 2, 3 and b: interesting files, misconfiguration/default files, information disclosure and software identification. These are active requests; results need review. | At most one HTTP origin per exact scoped host. |

Choose both Nuclei and Nikto to enable fallback. Nikto runs only if Nuclei is missing, unverified, errors or otherwise does not complete. A Nuclei run that completes successfully but reports no matches does **not** invoke Nikto. Choose Nikto alone to run it as a standalone phase. The fallback is recorded as a separate report phase and does not expand the explicit scope.

Select **Live hosts / HTTPX** in the same run when using Photon or Arjun. Otherwise those phases have no confirmed live-host list and are skipped. For the primary host, Photon/Arjun receive the supplied page path if you entered a URL; additional scope hosts use their site root. They use the submitted URL scheme and do not automatically retry using the other scheme if it fails.

## 4. Understand rate, timing and progress

### Tool rate ceiling

Enter any whole number from **1 to 5 per second**; the default is **2**. Choosing 1 requests a slower setting where the adapter supports it. It does **not** guarantee the whole computer, whole assessment or every secondary connection stays under one request per second.

| Adapter | How the selected rate is used |
|---|---|
| HTTPX | Passed as its request-rate setting; one worker, no retries. |
| Nuclei | Passed as its request-rate setting; concurrency and batch size are one, no retries. |
| Arjun | Passed as its rate-limit setting; one worker. |
| Photon | Converted into a delay of `1 / rate` seconds; one worker. At rate 2, that requested delay is 0.5 seconds. |
| Nikto | Converted into a delay between tests of `1 / rate` seconds. At rate 2, that requested delay is 0.5 seconds. |
| Nmap | Passed as `--max-rate`, a scan-packet setting, not a universal web-request limit. It does not bound every service-check or OS/network operation. |
| DNSRecon, Subfinder, theHarvester | This adapter does not pass the selected rate to them. DNS and public-provider traffic follow their own behavior. |

These tools count different operations. Nikto's pause is between tests, not a strict network request meter. The setting is a collection of tool-specific controls, **not a shared traffic meter or a total request budget**. Lower rates reduce request bursts but can make a run take longer.

### Timing and progress

Echo Recon applies **no per-tool or whole-assessment time limit**, including to local tool identity checks. A tool runs until it exits, reaches the output cap, or you press **Stop**. A tool can still exit with its own error. Only one assessment can run at once, and the Stop button terminates its process tree.

The overall progress bar shows the completed and remaining percentages based on resolved phases. Each tool row shows completed/remaining host-attempt percentages and elapsed time for its current attempt. Where a tool has completed hosts, its row estimates remaining time from its average completed-host duration. The overall estimate uses this run's completed phases. Both estimates are rough; tool and network speeds differ. Many command-line tools do not report their own percent within one host, so the UI labels that within-host progress unavailable instead of inventing a percentage.

Older saved reports may contain a `timeout` state. This version does not stop tools because an elapsed-time deadline was reached. Review error evidence and retry only when you have permission and understand the expected traffic.

## 5. Start and stop deliberately

1. Recheck the primary domain and exact scope. Remove hosts you do not intend to assess.
2. Choose only the checks you need and set the rate ceiling.
3. Tick the ownership/permission confirmation only when true. Read and acknowledge the network limitations.
4. Click **Start assessment** once. Only one job is allowed at a time.
5. Watch **Progress & evidence** and **Live activity**. An initial delay can be the local tool checks or DNS preflight, not a frozen page.
6. To stop the assessment, click **Stop** and wait for cancellation to complete before starting another job. On Linux, the application stops the current process group. Native Windows tools run in a kill-on-close Job Object so the contained process tree is terminated on cancellation/time/output limits, including descendants after their parent exits. If containment setup fails, the tool is not run uncontained. Abnormal OS shutdown or tool defects can still require inspection.
7. To close the dashboard server, press **Ctrl+C in its original terminal**. Closing the browser tab alone does not stop the server or an assessment.

For a first authorized run, keep just the primary host in scope, keep the three preselected checks and choose rate 1. Add additional checks only when you understand and permit their traffic. This is a form example, not a scan performed by this guide.

## 6. Read history and reports correctly

After a job ends, use **View report**, **HTML** or **JSON**. Click a phase in the HTML report to expand its evidence, diagnostics and per-host records. **Saved history** reopens saved state; it does not launch another scan. Refreshing the browser is not a fresh assessment either.

| State | Meaning |
|---|---|
| `pending` / `running` | Waiting for this phase / work is in progress. |
| `done` | The command exited successfully within the captured limits. It does not certify security. |
| `missing` | The required executable could not be found. |
| `unverified` | Identity/help checks failed; this phase was not treated as a ready tool. |
| `error` | Execution, parsing or another required operation failed. Read diagnostics. |
| `timeout` | A legacy saved report or external adapter status; this version does not stop scan processes on a timer. Coverage is incomplete. |
| `output_limit` | An output limit was reached; the captured evidence is incomplete. |
| `skipped` | A prerequisite was missing, or an earlier problem prevented the phase. |
| `cancelled` | Stop was requested; remaining work was not completed. |
| `interrupted` | The server restarted during the job; there is no automatic resume. |
| `complete` | Every selected phase ended `done`. This is successful execution, not proof of safety. |
| `partial` | At least one selected phase is incomplete or unsuccessful. |

**Selected Tools**, **Completed Phases** and **Incomplete Phases** count recorded phases, not verified vulnerabilities. **Automated Findings** counts parsed findings, not a complete count of security problems. Nuclei matches are labelled **unverified automated finding** until a person reviews them. Nikto output is evidence text rather than parsed vulnerability findings. Zero findings can mean limited coverage, incompatible/missing templates, unavailable sources or simply no match in this run.

The report's **Tool execution time** sums recorded scanner durations; it is not the total time you waited, because diagnostics and DNS overhead are outside those values. Report timestamps are recorded in UTC; the dashboard may display dates in your browser's local time.

History and raw evidence stay under the project's private `data/` directory. They may contain sensitive information even after best-effort redaction. Review before sharing; keep real reports and secrets out of GitHub. Demo generation has been removed. For legacy demo cleanup, follow the stopped-server maintenance instructions in the [README](../README.md#remove-saved-demos-from-an-earlier-edition).

## Quick troubleshooting

| Problem | Check first |
|---|---|
| Target URL rejected | Use a domain or public `http://` / `https://` URL with a valid domain. Credentials, IPs, wildcards and non-standard ports are not accepted. |
| Scope is rejected | Use at most four additional hosts; each must be an exact subdomain of the primary host. The primary is added automatically. |
| Non-public DNS error | This live mode does not accept private/reserved target addresses. |
| Tool remains missing after setup | Verify installation in this same Kali environment and its PATH; recheck or restart after PATH changes. |
| HTTPX is unverified | Confirm ProjectDiscovery HTTPX, not the unrelated Python HTTPX. |
| Photon/Arjun are skipped | Select HTTPX in the same run and inspect its live-host results. |
| Timeout/partial | Read the failing phase and per-host diagnostics; do not interpret it as a clean result. |
| Server restarted | Reload the dashboard for a new session; interrupted work is not automatically resumed. |

