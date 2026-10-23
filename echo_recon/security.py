"""Input boundaries and best-effort evidence redaction."""
import ipaddress
import re
from urllib.parse import urlsplit

HOST = re.compile(r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
SECRET = re.compile(r"(?i)((?:password|passwd|api[_-]?key|access[_-]?token|secret|authorization|cookie)\s*[=:]\s*)([^\s&\"<>]+)")
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def redact(value):
    text = ANSI.sub("", str(value))
    text = re.sub(r"(https?://)[^/\s@]+@", r"\1[REDACTED]@", text)
    return SECRET.sub(r"\1[REDACTED]", text)


def hostname(value):
    if not isinstance(value, str):
        raise ValueError("Enter a hostname, not a URL, wildcard, IP or command.")
    value = value.strip().lower().rstrip(".")
    if not HOST.fullmatch(value):
        raise ValueError("Enter a hostname, not a URL, wildcard, IP or command.")
    if value.endswith((".localhost", ".local", ".internal")):
        raise ValueError("Reserved/local hostnames are not accepted by the live scanner.")
    return value


def validate_scope(domain, entries):
    domain = hostname(domain)
    if not isinstance(entries, list) or not 1 <= len(entries) <= 5:
        raise ValueError("Provide 1–5 exact authorized hostnames.")
    scope = list(dict.fromkeys(hostname(item) for item in entries))
    if domain not in scope:
        raise ValueError("The primary domain must appear in the explicit scope.")
    if any(item != domain and not item.endswith("." + domain) for item in scope):
        raise ValueError("Scope entries must be the primary domain or its exact subdomains.")
    return domain, scope


def resolve_public(host, resolver):
    """Preflight only: third-party tools resolve again; not an egress firewall."""
    addresses = {row[4][0] for row in resolver(host, 443, type=1)}
    if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
        raise ValueError("Hostname must resolve only to public IP addresses.")
    return sorted(addresses)


def scoped_urls(text, scope):
    results = []
    for line in text.splitlines():
        try:
            parsed = urlsplit(line.strip())
            if (parsed.scheme in {"http", "https"} and parsed.hostname in scope
                    and not parsed.username and not parsed.password
                    and parsed.port in {None, 80, 443}):
                origin = f"{parsed.scheme}://{parsed.hostname}"
                if origin not in results:
                    results.append(origin)
        except ValueError:
            continue
    return results
