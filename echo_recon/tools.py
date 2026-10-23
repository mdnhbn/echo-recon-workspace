"""Fixed tool adapters. User input never becomes executable code or flags."""
import json
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
}


def diagnostics(cancel=None):
    result = {}
    cancel = cancel or threading.Event()
    required = {"httpx": ("-rate-limit", "-silent"),
                "arjun": ("--rate-limit", "--disable-redirects"),
                "nuclei": ("-jsonl", "-disable-redirects", "-exclude-tags")}
    for name, (label, flags, identity) in TOOLS.items():
        path = shutil.which(name)
        item = {"label": label, "path": path, "status": "missing", "detail": "Not installed"}
        if path:
            check = run([path, *flags], cancel=cancel, timeout=8, max_bytes=80_000)
            banner = (check.stdout + "\n" + check.stderr).lower()
            valid = check.returncode == 0 and identity in banner
            # ProjectDiscovery's help identifies itself; Python HTTPX has different flags.
            valid = valid and all(flag in banner for flag in required.get(name, ()))
            item.update(status="ready" if valid else "unverified",
                        detail="Identity/help check passed" if valid else "Help/identity check failed; inspect version/PATH",
                        banner=(check.stdout + check.stderr)[:350])
        result[name] = item
    return result


def command(name, host, rate, output_dir):
    url = f"https://{host}"
    return {
        "dnsrecon": ["dnsrecon", "-d", host, "-t", "std"],
        "subfinder": ["subfinder", "-d", host, "-silent"],
        "httpx": ["httpx", "-silent", "-rl", str(rate), "-threads", "1", "-timeout", "8", "-retries", "0"],
        "nmap": ["nmap", "-sT", "-sV", "--version-light", "--top-ports", "100", "--max-rate", str(rate), "--max-retries", "1", host],
        "theHarvester": ["theHarvester", "-d", host, "-b", "crtsh,otx"],
        "photon": ["photon", "-u", url, "-l", "1", "-t", "1", "-d", str(1 / rate), "--output", str(output_dir)],
        "arjun": ["arjun", "-u", url, "-t", "1", "-T", "8", "--rate-limit", str(rate), "--disable-redirects"],
        "nuclei": ["nuclei", "-silent", "-jsonl", "-duc", "-ni", "-dr", "-rl", str(rate), "-c", "1", "-bs", "1", "-timeout", "8", "-retries", "0", "-severity", "low,medium,high,critical", "-etags", "dos,fuzz,bruteforce,headless,code"],
    }[name]


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
