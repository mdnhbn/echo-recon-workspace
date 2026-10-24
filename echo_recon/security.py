"""Input boundaries and best-effort evidence redaction."""
import ipaddress
import re
from urllib.parse import urlsplit, urlunsplit

HOST = re.compile(r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
SECRET = re.compile(r"(?i)((?:password|passwd|api[_-]?key|access[_-]?token|secret|authorization|cookie)\s*[=:]\s*)([^\s&\"<>]+)")
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def redact(value):
    text = ANSI.sub("", str(value))
    text = re.sub(r"(https?://)[^/\s@]+@", r"\1[REDACTED]@", text)
    return SECRET.sub(r"\1[REDACTED]", text)


def _canonical_hostname(value):
    value = value.strip().lower().rstrip(".")
    if not HOST.fullmatch(value):
        raise ValueError("Enter a domain name or an http(s) URL; usernames, IPs, wildcards and commands are not accepted.")
    if value.endswith((".localhost", ".local", ".internal")):
        raise ValueError("Reserved/local hostnames are not accepted by the live scanner.")
    return value


def parse_target(value):
    """Accept a domain or public http(s) URL and return its safe host and page URL.

    Query strings and fragments are intentionally omitted so they are not saved
    or copied into third-party tool arguments. Any valid HTTP(S) port is kept
    for URL-aware adapters; the hostname remains the authorization scope.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Enter a domain name or an http(s) URL; usernames are not supported.")
    raw = value.strip()
    candidate = raw if "://" in raw or raw.startswith("//") else f"//{raw}"
    try:
        parsed = urlsplit(candidate)
        scheme = parsed.scheme.lower() if parsed.scheme else "https"
        if scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError
        if parsed.username or parsed.password:
            raise ValueError("URLs containing usernames or passwords are not accepted.")
        host = _canonical_hostname(parsed.hostname or "")
        port = parsed.port
    except ValueError as exc:
        if str(exc):
            raise
        raise ValueError("Enter a domain name or an http(s) URL with a valid hostname.") from exc
    authority = f"{host}:{port}" if port is not None else host
    page_url = urlunsplit((scheme, authority, parsed.path or "/", "", ""))
    return host, page_url


def hostname(value):
    """Normalize a hostname or URL to its host for exact scope checks."""
    return parse_target(value)[0]


def validate_scope(domain, entries):
    domain = hostname(domain)
    if not isinstance(entries, list) or len(entries) > 5:
        raise ValueError("Provide no more than five additional exact authorized hostnames.")
    scope = list(dict.fromkeys(hostname(item) for item in entries))
    if domain not in scope:
        scope.insert(0, domain)
    if len(scope) > 5:
        raise ValueError("The primary host plus additional hosts cannot exceed five total.")
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
            port = parsed.port
            if (parsed.scheme in {"http", "https"} and parsed.hostname in scope
                    and not parsed.username and not parsed.password):
                authority = f"{parsed.hostname}:{port}" if port is not None else parsed.hostname
                origin = f"{parsed.scheme}://{authority}"
                if origin not in results:
                    results.append(origin)
        except ValueError:
            continue
    return results
