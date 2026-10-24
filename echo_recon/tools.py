"""Fixed tool adapters. User input never becomes executable code or flags."""
import json
import os
from pathlib import Path
import re
import shutil
import threading
from urllib.parse import urlsplit
from .runner import run

TOOLS = {
    "dnsrecon": ("DNS records", ["-h"], "dnsrecon"),
    "subfinder": ("Subdomain discovery", ["-h"], "subfinder"),
    "httpx": ("Live HTTP hosts", ["-h"], "projectdiscovery"),
    "nmap": ("Ports and services", ["--version"], "nmap version"),
    "theHarvester": ("Public-source research", ["-h"], "theharvester"),
    "photon": ("Shallow web crawl", ["-h"], "photon"),
    "arjun": ("HTTP parameters", ["-h"], "arjun"),
    "nuclei": ("Template checks", ["-h"], "nuclei"),
    "nikto": ("Nikto web-server checks", ["-Help"], "nikto"),
}

SOURCES = {
    "dnsrecon": "https://github.com/darkoperator/dnsrecon",
    "subfinder": "https://github.com/projectdiscovery/subfinder/releases",
    "httpx": "https://github.com/projectdiscovery/httpx/releases",
    "nmap": "https://nmap.org/download.html",
    "theHarvester": "https://github.com/laramies/theHarvester",
    "photon": "https://github.com/s0md3v/Photon",
    "arjun": "https://github.com/s0md3v/Arjun",
    "nuclei": "https://github.com/projectdiscovery/nuclei/releases",
    "nikto": "https://github.com/sullo/nikto",
}


def is_windows():
    return os.name == "nt"


def managed_windows_command(name):
    """Read only complete installer-owned environments; never change PATH."""
    try:
        from setup_tools_windows import tool_command
        return tool_command(name)
    except (ImportError, OSError, ValueError, TypeError, KeyError):
        return None


def native_tool_command(name):
    if not is_windows():
        return None
    managed = managed_windows_command(name)
    if managed:
        return tuple(managed)
    if name == "nmap":
        for variable in ("ProgramFiles", "ProgramFiles(x86)"):
            folder = os.environ.get(variable)
            if folder:
                candidate = Path(folder) / "Nmap" / "nmap.exe"
                if candidate.is_file():
                    return (str(candidate),)
    return None


def resolve_tool(name):
    prefix = native_tool_command(name)
    if prefix:
        return prefix
    path = shutil.which(name)
    return (path,) if path else None


def nuclei_templates_incomplete(health):
    """True when the Nuclei engine is healthy but its local template metadata is not."""
    item = health.get("nuclei", {}) if isinstance(health, dict) else {}
    return item.get("engine_status") == "ready" and item.get("template_status") != "ready"


def nuclei_template_health(prefix, cancel=None):
    """Read Nuclei's local template version without auto-updating or scanning."""
    result = run([*prefix, "-tv", "-duc"], cancel=cancel or threading.Event(), max_bytes=80_000)
    output = result.stdout + "\n" + result.stderr
    match = re.search(r"public nuclei-templates version:\s*([^\s(]+)", output, flags=re.IGNORECASE)
    if result.status == "done" and result.returncode == 0 and match:
        return {"template_status": "ready", "template_version": match.group(1),
                "template_detail": f"Official Nuclei templates {match.group(1)} found locally"}
    if result.status == "done" and result.returncode == 0:
        return {"template_status": "missing", "template_version": None,
                "template_detail": "Nuclei engine is present, but its local template version was not found; Setup all tools will retry the official template download"}
    return {"template_status": "unverified", "template_version": None,
            "template_detail": f"Local Nuclei template check did not finish ({result.status}); Setup all tools can retry the official template download"}


def tool_sources():
    guide = "https://github.com/mdnhbn/echo-recon-workspace/blob/main/docs/TOOLS.md"
    return {name: {"label": TOOLS[name][0], "url": url, "setup_url": guide,
                   "note": (("Nikto requires Strawberry Perl on PATH; Nmap uses its official installer. Windows setup does not install runtimes or drivers unattended."
                             if name == "nikto" else
                             "Native Windows setup uses isolated compatible tools; Nmap uses its official installer and TCP connect scans without raw packet privileges.")
                            if is_windows() else "Use the official source and follow the Kali setup guide.")}
            for name, url in SOURCES.items()}


def diagnostics(cancel=None):
    result = {}
    cancel = cancel or threading.Event()
    required = {"httpx": ("-rate-limit", "-silent"),
                "arjun": ("--rate-limit", "--disable-redirects"),
                "nuclei": ("-jsonl", "-disable-redirects", "-exclude-tags"),
                "nikto": ("-host", "-tuning", "-maxtime", "-pause")}
    for name, (label, flags, identity) in TOOLS.items():
        prefix = resolve_tool(name)
        item = {"label": label, "path": prefix[0] if prefix else None,
                "command": list(prefix) if prefix else [], "status": "missing", "detail": "Not installed"}
        if prefix:
            check = run([*prefix, *flags], cancel=cancel, max_bytes=80_000)
            banner = (check.stdout + "\n" + check.stderr).lower()
            valid = check.returncode == 0 and identity in banner
            # ProjectDiscovery's help identifies itself; Python HTTPX has different flags.
            valid = valid and all(flag in banner for flag in required.get(name, ()))
            if name == "nuclei":
                item["engine_status"] = "ready" if valid else "unverified"
                if valid:
                    item.update(nuclei_template_health(prefix, cancel=cancel))
                else:
                    item.update(template_status="unknown", template_version=None,
                                template_detail="Engine check failed; template data was not checked")
                ready = valid and item.get("template_status") == "ready"
                detail = (item["template_detail"] if valid else
                          "Help/identity check failed; inspect version/PATH")
                item.update(status="ready" if ready else "unverified", detail=detail,
                            banner=(check.stdout + check.stderr)[:350])
            else:
                item.update(status="ready" if valid else "unverified",
                            detail="Identity/help check passed" if valid else "Help/identity check failed; inspect version/PATH",
                            banner=(check.stdout + check.stderr)[:350])
        result[name] = item
    return result


def command(name, host, rate, output_dir, target_url=None):
    url = target_url or f"https://{host}/"
    args = {
        "dnsrecon": ["dnsrecon", "-d", host, "-t", "std"],
        "subfinder": ["subfinder", "-d", host, "-silent"],
        "httpx": ["httpx", "-silent", "-rl", str(rate), "-threads", "1", "-retries", "0"],
        "nmap": ["nmap", "-sT", "-sV", "--version-light", "--top-ports", "100", "--max-rate", str(rate), "--max-retries", "1", host],
        "theHarvester": ["theHarvester", "-d", host, "-b", "crtsh,otx"],
        "photon": ["photon", "-u", url, "-l", "1", "-t", "1", "-d", str(1 / rate), "--output", str(output_dir)],
        "arjun": ["arjun", "-u", url, "-t", "1", "--rate-limit", str(rate), "--disable-redirects"],
        "nuclei": ["nuclei", "-silent", "-jsonl", "-duc", "-ni", "-dr", "-rl", str(rate), "-c", "1", "-bs", "1", "-retries", "0", "-severity", "low,medium,high,critical", "-etags", "dos,fuzz,bruteforce,headless,code"],
        # Nikto's default scan is wider. Keep this adapter to informational,
        # configuration/default-file and software-identification categories.
        # These exclude its DoS, command-execution, SQLi and other exploit-style
        # tuning groups. The user-supplied rate maps to a delay between tests.
        "nikto": ["nikto", "-nointeractive", "-nocheck", "-ask", "no",
                  "-Tuning", "123b", "-Pause", f"{1 / rate:.3f}",
                  "-host", urlsplit(host).hostname or host],
    }[name]
    if name == "nikto":
        parsed_host = urlsplit(host)
        port = parsed_host.port or (443 if parsed_host.scheme == "https" else None)
        if port is not None:
            args.extend(["-port", str(port)])
        if parsed_host.scheme == "https":
            args.append("-ssl")
    if name == "nmap" and is_windows():
        # Official Nmap guidance for Windows without Npcap: use sockets only.
        args.insert(2, "-Pn")
    prefix = native_tool_command(name)
    return [*prefix, *args[1:]] if prefix else args


def parse_findings(text, scope):
    findings, invalid = [], 0
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            info = entry.get("info", {})
            matched = entry.get("matched-at", entry.get("host", ""))
            if urlsplit(matched).hostname not in scope:
                invalid += 1
                continue
            findings.append({"template": str(entry.get("template-id", "unknown")),
                             "name": str(info.get("name", "Unnamed finding")),
                             "severity": str(info.get("severity", "unknown")),
                             "matched": str(matched), "verification": "unverified automated finding",
                             "remediation": str(info.get("remediation", "Review the evidence and vendor guidance; verify before changing systems."))})
        except (ValueError, TypeError, AttributeError):
            invalid += 1
    return findings, invalid
