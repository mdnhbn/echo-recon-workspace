# Using Echo Recon, step by step

**[বাংলা নির্দেশনা](USAGE.bn.md)** · [Installation](../README.md) · [Tool setup](TOOLS.md) · [Windows / WSL](WINDOWS.md)

Echo Recon is a local dashboard that runs eight separate assessment tools in a fixed order and saves their evidence. Opening the dashboard does not start a scan. This guide uses `example.com` only to explain the fields: **replace it with a domain you own or have explicit permission to assess. Do not start a run against the example addresses.**

## 1. Open the dashboard

In your Kali terminal, go to your installed project folder and run:

```bash
cd ~/Tools/02-Custom/echo-recon-workspace
bash run.sh
```

Keep that terminal open. Firefox should open **http://127.0.0.1:8001**. If it does not, enter that address manually. This is the dashboard's address on your own Kali machine; it is not the domain you put in the assessment form.

Run as your normal user. The dashboard itself does not need root. On native Windows, the dashboard, saved history and reports work; use **Kali WSL2** for the eight-tool assessment workflow. See [WINDOWS.md](WINDOWS.md).

### Switch between the two layouts

The header's **Light layout / হালকা** button switches the dashboard to the light layout. It then reads **Dark layout / ডার্ক**; click again to return to the dark layout. The button names the layout you will switch to, not the current one.

Changing the layout keeps your form values, running job and displayed results in place. The choice is remembered for this dashboard address in the same browser when local browser storage is available. A new browser/profile, cleared storage or blocked storage may start with the default dark layout. Another open tab for the same address follows the saved choice when browser storage events are available.

The background matrix animation is available in both layouts; reduced-motion preferences disable it. This switch changes dashboard presentation, not the scan settings. For the built-in instructions, click **How to use / ব্যবহারবিধি** in the header or **Full usage guide / বিস্তারিত নিয়ম** in the sidebar.

## 2. Check and set up the tools

1. Click **Check installed tools**. Wait for the identity/help checks to finish.
2. Read each tool's state:

   | State | Meaning | Next step |
   |---|---|---|
   | `ready` | A matching executable passed the local help/identity check. | It can be selected, but this is not a complete compatibility test. |
   | `missing` | The executable was not found on the server's PATH. | Set up the tool in the same Kali environment as the dashboard. |
   | `unverified` | An executable was found, but its identity or required help flags did not match. | Check the version and PATH first; reinstalling may be unnecessary. |

3. Click **Download / Setup tools** to see official sources and installation guidance for all eight tools. A missing/unverified row also has a setup shortcut.
4. On a supported Kali desktop, **Setup all tools** opens a local terminal for the project's fixed tool installer. Review what it says before continuing. If administrator permission is needed, enter your sudo password **in that terminal**, never in the dashboard or a chat. Password characters normally stay invisible while typing.
5. Keep the installer terminal open until it reports completion or an error. A started installer is not proof that all tools installed successfully. Downloading source and installing a working executable are different steps.
6. If no terminal can open, or you are using Windows/WSL without a Kali desktop, use the exact terminal commands below and [TOOLS.md](TOOLS.md) inside Kali. A native Windows tool installation does not make these Linux adapters work in Windows.
7. After setup, click **Check installed tools** again. If the shell's PATH or other environment changed, restart the dashboard and recheck. Select only checks you need; installing a tool does not require you to run it.

**HTTPX warning:** this project needs **ProjectDiscovery HTTPX**. Python HTTPX is a different program with the same executable name. Do not delete Python HTTPX or overwrite `/usr/bin/httpx` to fix the conflict; follow the tool guide.

Nuclei also needs compatible templates. External data providers may be unavailable or need separate account configuration. Tool setup does not create paid accounts or API keys.

### Headless Kali / Kali WSL terminal commands

Open your own **Kali terminal**, go to this installed repository, and preview the fixed plan first:

```bash
cd ~/Tools/02-Custom/echo-recon-workspace
.venv/bin/python setup_tools.py --plan
```

`--plan` reads local paths and prints the setup plan. It does not execute commands, probe tool help, download, install or scan. A printed path is not a passed readiness check.

When you are ready to make the changes, finish or stop any assessment, then run:

```bash
.venv/bin/python setup_tools.py --install
```

`--install` starts the fixed installation workflow; it is not another preview. It checks the tools, skips those passing local checks, and sets up those needing attention. It may request sudo in this interactive terminal for fixed Kali packages. Run the Python command as your normal user, **not** `sudo python`. Do not start several installers at once. Review any error before retrying; an unrelated existing launcher will not be overwritten automatically.

Newly installed Nuclei engines also download official templates. Existing ready Nuclei installations/templates are retained by default. After setup, close the finished installer terminal, restart the dashboard if its environment changed, and click **Check installed tools** again. These installer commands accept no scan target and do not launch an assessment. On Windows, enter Kali WSL before running them; `--install` supports Kali rather than native Windows or arbitrary Linux distributions.

## 3. Fill in the form

### Primary domain

Enter a hostname only. The primary domain is the main name for this assessment, such as `example.com` in the explanation below.

| Entry | Accepted? | Why |
|---|---|---|
| `example.com` | Yes, as a hostname format | Replace with your authorized domain. |
| `app.example.com` | Yes, as a hostname format | If it is primary, only that name and its own subdomains can be in scope. |
| `https://example.com` | No | Includes a URL scheme. |
| `example.com/login` | No | Includes a path. |
| `example.com:443` | No | Includes a port. |
| `*.example.com` | No | Wildcards are not supported. |
| `127.0.0.1`, `192.168.1.10`, `localhost` | No | IP addresses and local hosts are not accepted live targets. |

The live scanner requires hostnames that resolve only to public IP addresses. A hostname that resolves to private/reserved addresses is rejected. The local dashboard address is therefore not a target to paste into the form.

### Exact authorized hosts

This is the list of **exact hostnames you permit the active checks to receive**. Put one hostname on each line, include the primary domain, and use **no more than five entries**. Extra entries must be subdomains of that primary domain.

For example, the form structure would be:

**Primary domain:**

```text
example.com
```

**Exact authorized hosts:**

```text
example.com
app.example.com
```

Replace both lines with real names you are authorized to assess before starting. Do not add a subdomain merely because it appears in a result: check ownership/permission first. If you authorize only the primary domain, put only that one line in scope. A separately owned domain cannot be added to this run; it needs its own assessment.

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

Select **Live hosts / HTTPX** in the same run when using Photon or Arjun. Otherwise those phases have no confirmed live-host list and are skipped. The current Photon/Arjun adapters use `https://HOST` at the site root; they do not accept an arbitrary page path and do not automatically fall back to HTTP when HTTPS fails. An HTTPX response at HTTP alone does not guarantee these HTTPS checks will succeed.

## 4. Understand rate and time before starting

### Tool rate ceiling

The form offers **1, 2 or 5 per second**; the default is **2**. Choosing 1 requests a slower setting where the adapter supports it. It does **not** guarantee the whole computer, whole assessment or every secondary connection stays under one request per second.

| Adapter | How the selected rate is used |
|---|---|
| HTTPX | Passed as its request-rate setting; one worker, no retries. |
| Nuclei | Passed as its request-rate setting; concurrency and batch size are one, no retries. |
| Arjun | Passed as its rate-limit setting; one worker. |
| Photon | Converted into a delay of `1 / rate` seconds; one worker. At rate 2, that requested delay is 0.5 seconds. |
| Nmap | Passed as `--max-rate`, a scan-packet setting, not a universal web-request limit. It does not bound every service-check or OS/network operation. |
| DNSRecon, Subfinder, theHarvester | This adapter does not pass the selected rate to them. DNS and public-provider traffic follow their own behavior. |

These tools count different operations. The setting is a collection of tool-specific controls, **not a shared traffic meter or a total request budget**. Lower settings and short time limits can leave work incomplete.

### Time per tool / host

The form offers **30, 60, 120 or 180 seconds**; the default is **120 seconds**. This is the process allowance for **one tool invocation on one host**, not the deadline for the whole assessment.

For example, with a 120-second allowance, HTTPX on the first scoped host can use up to that allowance; HTTPX on the next scoped host gets its own allowance. Another selected tool then gets its own allowance. Tools also have some shorter internal connection/request timeouts, so an individual request may fail sooner.

All phases and their hosts run sequentially. They do not all share one 120-second timer.

- A simple conservative calculation is `8 tools × 5 hosts × 120 seconds = 4,800 seconds`, or **80 minutes** of process allowances. This overcounts the present pipeline because three tools use only the primary domain.
- In the current code, all eight checks with five eligible hosts mean at most `3 + (5 × 5) = 28` scanner invocations, so `28 × 120 = 3,360 seconds`, or **56 minutes** of scanner allowances. Photon/Arjun may have fewer hosts or be skipped.
- Neither calculation is a hard wall-clock limit or an estimate of what your run will take. Identity/help checks, repeated DNS preflight, process startup/cleanup, provider behavior and other overhead add time. A DNS lookup is not wrapped in the scanner's per-process timer. Many tools finish early, fail, or are missing. There is no separate whole-job deadline.

If a process exceeds its allowance, it is stopped and marked **timeout**. A timeout means **the phase is incomplete**, not “no vulnerability” or “site is safe.” Other selected phases may still continue; normally the job becomes **partial** if not every selected phase finishes successfully. A fatal pipeline error can instead end the job as **error**. Raising the timeout can let work continue longer, but it does not repair a missing tool, invalid scope or unavailable provider.

## 5. Start and stop deliberately

1. Recheck the primary domain and exact scope. Remove hosts you do not intend to assess.
2. Choose only the checks you need, then choose the rate and per-tool/host allowance.
3. Tick the ownership/permission confirmation only when true. Read and acknowledge the network limitations.
4. Click **Start assessment** once. Only one job is allowed at a time.
5. Watch **Progress & evidence** and **Live activity**. An initial delay can be the local tool checks or DNS preflight, not a frozen page.
6. To stop the assessment, click **Stop** and wait for cancellation to complete before starting another job. On Linux, the application asks the current process group to stop. Abnormal shutdown or detached child processes can require separate inspection.
7. To close the dashboard server, press **Ctrl+C in its original terminal**. Closing the browser tab alone does not stop the server or an assessment.

For a first authorized run, keep just the primary host in scope, keep the three preselected checks, and choose rate 1 and a 120-second allowance. Add additional checks only when you understand and permit their traffic. This is a form example, not a scan performed by this guide.

## 6. Read history and reports correctly

After a job ends, use **View report**, **HTML** or **JSON**. Click a phase in the HTML report to expand its evidence, diagnostics and per-host records. **Saved history** reopens saved state; it does not launch another scan. Refreshing the browser is not a fresh assessment either.

| State | Meaning |
|---|---|
| `pending` / `running` | Waiting for this phase / work is in progress. |
| `done` | The command exited successfully within the captured limits. It does not certify security. |
| `missing` | The required executable could not be found. |
| `unverified` | Identity/help checks failed; this phase was not treated as a ready tool. |
| `error` | Execution, parsing or another required operation failed. Read diagnostics. |
| `timeout` | A tool invocation exceeded its allowance; coverage is incomplete. |
| `output_limit` | An output limit was reached; the captured evidence is incomplete. |
| `skipped` | A prerequisite was missing, or an earlier problem prevented the phase. |
| `cancelled` | Stop was requested; remaining work was not completed. |
| `interrupted` | The server restarted during the job; there is no automatic resume. |
| `complete` | Every selected phase ended `done`. This is successful execution, not proof of safety. |
| `partial` | At least one selected phase is incomplete or unsuccessful. |

**Selected Tools**, **Completed Phases** and **Incomplete Phases** count recorded phases, not verified vulnerabilities. **Automated Findings** counts parsed findings, not a complete count of security problems. Nuclei matches are labelled **unverified automated finding** until a person reviews them. Zero findings can mean limited coverage, incompatible/missing templates, unavailable sources or simply no match in this run.

The report's **Tool execution time** sums recorded scanner durations; it is not the total time you waited, because diagnostics and DNS overhead are outside those values. Report timestamps are recorded in UTC; the dashboard may display dates in your browser's local time.

History and raw evidence stay under the project's private `data/` directory. They may contain sensitive information even after best-effort redaction. Review before sharing; keep real reports and secrets out of GitHub. Demo generation has been removed. For legacy demo cleanup, follow the stopped-server maintenance instructions in the [README](../README.md#remove-saved-demos-from-an-earlier-edition).

## Quick troubleshooting

| Problem | Check first |
|---|---|
| “Enter a hostname” | Remove `https://`, path, port, wildcard or IP address. |
| “Primary domain must appear” | Include exactly that primary hostname in the scope list. |
| Scope is rejected | Use at most five hosts; each must be the primary name or its exact subdomain. |
| Non-public DNS error | This live mode does not accept private/reserved target addresses. |
| Tool remains missing after setup | Verify installation in this same Kali environment and its PATH; recheck or restart after PATH changes. |
| HTTPX is unverified | Confirm ProjectDiscovery HTTPX, not the unrelated Python HTTPX. |
| Photon/Arjun are skipped | Select HTTPX in the same run and inspect its live-host results. |
| Timeout/partial | Read the failing phase and per-host diagnostics; do not interpret it as a clean result. |
| Server restarted | Reload the dashboard for a new session; interrupted work is not automatically resumed. |

