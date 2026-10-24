"""Sequential assessment orchestration, persisted after every transition."""
from datetime import datetime, timezone
import json
from pathlib import Path
import socket
import threading
import time
import uuid
from urllib.parse import urlsplit
from .runner import run
from .security import parse_target, redact, resolve_public, scoped_urls, validate_scope
from .tools import TOOLS, command, diagnostics, is_windows, parse_findings
from . import __version__


def now():
    return datetime.now(timezone.utc).isoformat()


def page_url_for(job, host):
    parsed = urlsplit(host)
    hostname = parsed.hostname or host
    if hostname == job["domain"]:
        return job["target_url"]
    scheme = urlsplit(job["target_url"]).scheme
    return f"{scheme}://{hostname}/"


def clean_object(value):
    if isinstance(value, dict):
        return {key: clean_object(item) for key, item in value.items()}
    if isinstance(value, list):
        return [clean_object(item) for item in value]
    return redact(value) if isinstance(value, str) else value


def nikto_targets(scope, live, primary_url=None):
    """Keep the supplied primary origin; prefer HTTPS for other explicit hosts."""
    origins = {}
    primary_host = None
    if primary_url:
        try:
            parsed = urlsplit(primary_url)
            primary_host = parsed.hostname
            if parsed.scheme in {"http", "https"} and primary_host in scope:
                authority = f"{primary_host}:{parsed.port}" if parsed.port is not None else primary_host
                origins[primary_host] = f"{parsed.scheme}://{authority}"
        except ValueError:
            primary_host = None
    for value in live:
        try:
            parsed = urlsplit(value)
            host = parsed.hostname
            port = parsed.port
            if (parsed.scheme in {"http", "https"} and host in scope
                    and not parsed.username and not parsed.password):
                if host == primary_host:
                    continue
                previous = origins.get(host)
                if previous is None or (parsed.scheme == "https" and not previous.startswith("https://")):
                    authority = f"{host}:{port}" if port is not None else host
                    origins[host] = f"{parsed.scheme}://{authority}"
        except ValueError:
            continue
    return [origins.get(host, f"https://{host}") for host in scope]


class Manager:
    def __init__(self, store, data_dir, execute=run, resolver=socket.getaddrinfo,
                 check_tools=diagnostics, allow_live=True):
        self.store, self.data_dir = store, Path(data_dir)
        self.execute, self.resolver = execute, resolver
        self.check_tools = check_tools
        self.allow_live = allow_live
        self.lock = threading.RLock()
        self.active = {}
        self.store.interrupt_old_jobs()

    def save(self, job, message=None):
        job["updated"] = now()
        if message:
            job["log"].append(f"{job['updated']} {message}")
        snapshot = clean_object(job)
        snapshot.pop("target_url", None)
        self.store.save(snapshot)

    def start(self, payload, background=True):
        if payload.get("demo") is True:
            raise ValueError("Demo mode has been removed. Supply an explicitly authorized scope.")
        if not self.allow_live:
            raise ValueError("Assessment execution is disabled for this dashboard. Tool setup and saved reports remain available.")
        if payload.get("authorized") is not True or payload.get("understands_limits") is not True:
            raise ValueError("Confirm ownership/permission and third-party traffic limitations.")
        target_input = payload.get("target_url") or payload.get("url") or payload.get("domain")
        domain, target_url = parse_target(target_input)
        scope_input = payload.get("scope")
        if scope_input is None:
            scope_input = []
        domain, scope = validate_scope(domain, scope_input)
        selected = payload.get("tools", list(TOOLS))
        if (not isinstance(selected, list) or not selected or
                any(not isinstance(name, str) or name not in TOOLS for name in selected)):
            raise ValueError("Select supported tools only.")
        selected = [name for name in TOOLS if name in selected]
        rate = payload.get("rate", 2)
        if type(rate) is not int or not 1 <= rate <= 5:
            raise ValueError("Rate must be an integer from 1 to 5.")
        with self.lock:
            if self.active:
                raise RuntimeError("An assessment is already active. Stop it or wait.")
            job_id = uuid.uuid4().hex
            job = {"id": job_id, "version": __version__, "domain": domain, "target_url": target_url, "scope": scope,
                   "status": "running", "created": now(), "updated": now(),
                   "settings": {"rate": rate}, "log": [],
                   "phases": [{"tool": name, "label": TOOLS[name][0], "status": "pending",
                               "evidence": "", "stderr": "", "returncode": None,
                               "duration": 0, "findings": []} for name in selected],
                   "limitations": [
                       "Automated findings require manual verification. No findings is not proof of safety.",
                       "Exact input scope is enforced by the dashboard, not a network sandbox. DNS can change; crawlers/templates may follow secondary links or contact third parties.",
                       "Rate is a per-tool ceiling where supported, not a global packet/request budget. DNS/OSINT tools have separate behavior.",
                       "The supplied primary URL path and port are used by HTTPX, Nuclei, Photon and Arjun; query and fragment are omitted. Other checks use its hostname/origin. Usernames are not valid targets.",
                       "Evidence is truncated and common secrets are redacted best-effort; review reports before sharing.",
                   ]}
            if "nikto" in selected:
                job["limitations"].append(
                    "Nikto is a noticeable active web-server scanner. Echo Recon restricts its selected checks to informational, configuration/default-file and software-identification groups, but this is not a network sandbox.")
            if is_windows():
                job["limitations"].append(
                    "Windows Nmap uses TCP connect scanning without ping discovery (-sT -Pn); raw packet, UDP and operating-system detection are not enabled.")
            event = threading.Event()
            self.active[job_id] = event
            self.save(job, "Assessment queued with explicit scope.")
            if background:
                thread = threading.Thread(target=self.worker, args=(job, event), daemon=True)
                thread.start()
            else:
                self.worker(job, event)
            return job_id

    def cancel(self, job_id):
        with self.lock:
            event = self.active.get(job_id)
            if event:
                event.set()
                return True
            return False

    def close(self):
        with self.lock:
            for event in self.active.values():
                event.set()
        deadline = time.monotonic() + 5
        while self.active and time.monotonic() < deadline:
            time.sleep(0.05)

    def worker(self, job, event):
        try:
            self.pipeline(job, event)
            if event.is_set():
                job["status"] = "cancelled"
            elif all(phase["status"] == "done" or
                     (phase["status"] == "skipped" and phase.get("optional") is True)
                     for phase in job["phases"]):
                job["status"] = "complete"
            else:
                job["status"] = "partial"
        except Exception as exc:
            job["status"] = "error"
            job["finished_at"] = now()
            for phase in job["phases"]:
                if phase["status"] in {"running", "pending"}:
                    phase.update(status="error" if phase["status"] == "running" else "skipped",
                                 finished_at=now())
            self.save(job, f"Assessment stopped: {redact(exc)}")
        finally:
            for phase in job["phases"]:
                if phase["status"] == "pending":
                    phase.update(status="cancelled" if event.is_set() else "skipped",
                                 finished_at=now())
            job.setdefault("finished_at", now())
            self.save(job, f"Assessment ended: {job['status']}. Review phase evidence and limitations.")
            with self.lock:
                self.active.pop(job["id"], None)

    def pipeline(self, job, event):
        scope, rate = job["scope"], job["settings"]["rate"]
        live = []
        selected_tools = {phase["tool"] for phase in job["phases"]}
        health = self.check_tools(cancel=event)
        job["tool_health"] = health
        for phase in job["phases"]:
            if event.is_set():
                break
            name = phase["tool"]
            fallback_reason = None
            if name == "nikto" and "nuclei" in selected_tools:
                nuclei_phase = next((item for item in job["phases"] if item["tool"] == "nuclei"), None)
                if nuclei_phase and nuclei_phase["status"] == "done":
                    phase.update(status="skipped", optional=True,
                                 finished_at=now(),
                                 evidence="Nuclei completed successfully; the selected Nikto fallback was not needed.")
                    self.save(job, "Nikto fallback skipped; Nuclei completed.")
                    continue
                fallback_reason = nuclei_phase.get("status", "unavailable") if nuclei_phase else "unavailable"
                phase["fallback_reason"] = fallback_reason
            if health[name]["status"] != "ready":
                phase.update(status="missing" if health[name]["status"] == "missing" else "unverified",
                             evidence=health[name]["detail"])
                self.save(job, f"{phase['label']}: {phase['status']}")
                continue
            phase.update(status="running", started_at=now(), attempts=[], completed_hosts=0, duration=0)
            self.save(job, f"Starting {phase['label']}")
            # Revalidate each explicit hostname before each phase. This is not IP pinning.
            phase["resolved"] = {host: resolve_public(host, self.resolver) for host in scope}
            hosts = [job["domain"]] if name in {"dnsrecon", "subfinder", "theHarvester"} else scope
            if name == "nikto":
                hosts = nikto_targets(scope, live, job["target_url"])
                if fallback_reason is not None:
                    nuclei_phase = next((item for item in job["phases"] if item["tool"] == "nuclei"), None)
                    attempts = nuclei_phase.get("attempts", []) if nuclei_phase else []
                    failed_hosts = {item.get("host") for item in attempts if item.get("status") != "done"}
                    if failed_hosts:
                        hosts = [target for target in hosts if urlsplit(target).hostname in failed_hosts]
                    if not hosts:
                        hosts = nikto_targets(scope, live)
            if name in {"photon", "arjun"}:
                live_hosts = {urlsplit(url).hostname for url in live}
                hosts = [host for host in scope if host in live_hosts]
                if not hosts:
                    phase.update(status="skipped", finished_at=now(), evidence="No confirmed in-scope live host. Enable HTTPX or review probing errors.")
                    self.save(job)
                    continue
            outputs, errors, states, findings, attempts = [], [], [], [], []
            phase.update(total_hosts=len(hosts))
            self.save(job)
            duration = 0
            for host in hosts:
                if event.is_set():
                    break
                target_host = urlsplit(host).hostname if name == "nikto" else host
                scratch = self.data_dir / "scratch" / job["id"] / target_host
                scratch.mkdir(parents=True, exist_ok=True)
                target_url = page_url_for(job, host)
                phase.update(current_host=target_host, current_started_at=now())
                self.save(job)
                args = command(name, host, rate, scratch, target_url=target_url)
                # HTTP-facing checks receive explicit scoped targets, not discoveries.
                stdin = target_url + "\n" if name in {"httpx", "nuclei"} else ""
                result = self.execute(args, cancel=event, stdin=stdin, cwd=scratch)
                state = "error" if result.status == "done" and result.returncode != 0 else result.status
                states.append(state)
                duration += result.duration
                outputs.append(f"Host: {host}\n{result.stdout}")
                errors.append(result.stderr)
                phase["returncode"] = result.returncode
                attempts.append({"host": host, "status": state,
                                 "returncode": result.returncode, "duration": result.duration})
                phase.update(attempts=list(attempts), completed_hosts=len(attempts),
                             duration=round(duration, 2))
                phase.pop("current_host", None)
                phase.pop("current_started_at", None)
                self.save(job)
                if name == "httpx" and state == "done":
                    live.extend(scoped_urls(result.stdout, scope))
                if name == "nuclei":
                    parsed, invalid = parse_findings(result.stdout, scope)
                    findings.extend(parsed)
                    if invalid:
                        errors.append(f"{invalid} malformed or out-of-scope result lines excluded; review required.")
                        if states[-1] == "done":
                            states[-1] = "error"
                # Stop this phase if the executable is missing; do not repeat per host.
                if state in {"missing", "cancelled", "output_limit"}:
                    break
            status = next((state for state in states if state != "done"), "done")
            if event.is_set():
                status = "cancelled"
            evidence, stderr = redact("\n".join(outputs)), redact("\n".join(errors))
            if name == "nikto" and fallback_reason is not None:
                evidence = redact(f"Nuclei status was {fallback_reason}; running the selected Nikto fallback.\n" + evidence)
            truncated = len(evidence) > 100_000 or len(stderr) > 25_000
            if truncated and status == "done":
                status = "output_limit"
            phase.update(status=status, finished_at=now(), duration=round(duration, 2), findings=findings,
                         attempts=attempts, evidence_truncated=truncated,
                         evidence=evidence[:100_000], stderr=stderr[:25_000])
            phase.pop("current_host", None)
            phase.pop("current_started_at", None)
            if name == "nuclei" and status == "done" and not findings:
                phase["evidence"] += "\nNo automated findings reported within this run's coverage; not proof of safety."
            self.save(job, f"{phase['label']}: {status}")
