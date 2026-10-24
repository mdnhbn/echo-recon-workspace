#!/usr/bin/env python3
"""Fixed-source, normal-user native Windows backend setup.

Default/--plan does not write, download, or execute anything. --install sets up
supported tools in separate user-local version folders. Nmap's installer and
Nikto's Perl runtime are manual prerequisites when absent.
Only local help/version checks run; no assessment target is accepted.
"""
import argparse
import ctypes
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import stat
import struct
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile

sys.dont_write_bytecode = True

from echo_recon.locking import InstanceLock

ROOT = Path(__file__).resolve().parent
TOOL_NAMES = ("dnsrecon", "subfinder", "httpx", "nmap", "theHarvester", "photon", "arjun", "nuclei", "nikto")
MARKER = "Echo Recon native Windows tooling v1\n"
TOOL_MARKER = ".echo-recon-tool.json"
SCHEMA = 1
MAX_DOWNLOAD = 200 * 1024 * 1024
MAX_UNPACKED = 600 * 1024 * 1024

# Official immutable releases and GitHub-published SHA256 digests reviewed
# 2026-10-24: github.com/projectdiscovery/{subfinder,httpx,nuclei}/releases.
# Pin both each official checksum manifest and the selected Windows ZIP.
WINDOWS_RELEASES = {
    "subfinder": {"version": "2.17.0", "repository": "projectdiscovery/subfinder",
                  "sha256": "a3fd612928d591fb31c1e59a2e06055e364421ba32251e553073f5673a2d3103",
                  "checksums_sha256": "115acad346b14570ba1fbc98adb49bce97f9ed7e451de226d4c5b0b2087e495c"},
    "httpx": {"version": "1.12.0", "repository": "projectdiscovery/httpx",
              "sha256": "14d8ccaa2d95ce9365162682f1a2ba3f14d2000bb4bfb0924af65ec5163ae021",
              "checksums_sha256": "541586a8d1bc7e30f3f31ff954baca6ac3e02cd74363378b7773375a78259c02"},
    "nuclei": {"version": "3.11.1", "repository": "projectdiscovery/nuclei",
               "sha256": "bb6cb9ff8939b753f6fcab06fd30a15f5bc61d8382a597871334c007a85ff9d2",
               "checksums_sha256": "8c55f4113c54dfa4a202e32eaaa8b78abc741a13ed7941651322748fb233a05e"},
}
for _name, _release in WINDOWS_RELEASES.items():
    _release["asset"] = f"{_name}_{_release['version']}_windows_amd64.zip"
    _release["checksums"] = f"{_name}_{_release['version']}_checksums.txt"
    _prefix = f"https://github.com/{_release['repository']}/releases/download/v{_release['version']}/"
    _release["url"] = _prefix + _release["asset"]
    _release["checksums_url"] = _prefix + _release["checksums"]

ARJUN_VERSION = "2.2.7"
ARJUN_SOURCE = ("https://files.pythonhosted.org/packages/04/22/"
                "c5b969720d2802de2248c2aac0414ee5ae234887cfe150564d591c73fb23/"
                "arjun-2.2.7.tar.gz#sha256=b193cdaf97bf7b0e8cd91a41da778639e01fd9738d5f666a8161377f475ce72e")
PHOTON_COMMIT = "c8d2566841d69a268b244609921143d84b72b0c6"
DNSRECON_COMMIT = "8ba53cec0e1d61886cd0251da753a586fafa7a28"
HARVESTER_COMMIT = "fd832dee7936458a4f6e2029bf37ba6797228676"
NIKTO_COMMIT = "d201dac320fc5187eac75e723dd07a716196ec5a"
SOURCE_ARCHIVES = {
    "photon": {"version": PHOTON_COMMIT, "repository": "s0md3v/Photon", "commit": PHOTON_COMMIT,
               "sha256": "440e730b243e43381f0972bccb7e6959bbfe5d0c713c271ed763ade9406272a8"},
    "dnsrecon": {"version": "1.6.3", "repository": "darkoperator/dnsrecon", "commit": DNSRECON_COMMIT,
                 "sha256": "4552b3221706c5f9b66187dc1836e04b6975237a3d25cc8803a5e5904bef47e6"},
    "theHarvester": {"version": "4.11.1", "repository": "laramies/theHarvester", "commit": HARVESTER_COMMIT,
                     "sha256": "c250f692b92aa21a18948c5fc2ac68b088fcc9f96e87254bd15fd237146c1ca0"},
    "nikto": {"version": "2.6.1", "repository": "sullo/nikto", "commit": NIKTO_COMMIT,
              "sha256": "80683343b725645f58f90ef51191527891557adadd2396f23cd5726d1c8a3900"},
}
for _source in SOURCE_ARCHIVES.values():
    _source["url"] = f"https://codeload.github.com/{_source['repository']}/zip/{_source['commit']}"
    _source["prefix"] = _source["repository"].split("/")[1] + "-" + _source["commit"]

# Runtime closure from each pinned official uv.lock with Windows/Python3.12
# markers and runtime extras, excluding development groups. Venvs stay separate.
BUILD_PINS = ("setuptools==82.0.1", "wheel==0.47.0", "packaging==25.0", "flit_core==3.12.0")
REQUEST_PINS = ("requests==2.34.2", "charset-normalizer==3.5.2", "idna==3.20", "urllib3==2.8.0", "certifi==2026.10.23")
ARJUN_PINS = ("dicttoxml==1.7.16", "ratelimit==2.2.1", *REQUEST_PINS)
PHOTON_PINS = ("tld==0.13.2", "PySocks==1.7.1", *REQUEST_PINS)
DNSRECON_PINS = tuple("""
annotated-doc==0.0.4 annotated-types==0.7.0 anyio==4.14.0 certifi==2026.5.20
click==8.4.1 colorama==0.4.6 deprecated==1.3.1 dnspython==2.8.0 fastapi==0.138.1
h11==0.16.0 httpcore==1.0.9 httptools==0.8.0 httpx==0.28.1 idna==3.18 limits==5.8.0
loguru==0.7.3 netaddr==1.3.0 packaging==26.2 pydantic==2.13.4 pydantic-core==2.46.4
python-dotenv==1.2.2 pyyaml==6.0.3 slowapi==0.1.10 stamina==26.1.0 starlette==1.3.1
tenacity==9.1.4 typing-extensions==4.15.0 typing-inspection==0.4.2 ujson==5.13.0
uvicorn==0.49.0 watchfiles==1.2.0 websockets==16.0 win32-setctime==1.2.0 wrapt==2.2.1
""".split())
HARVESTER_PINS = tuple("""
aiodns==4.0.4 aiofiles==25.1.0 aiohappyeyeballs==2.6.1 aiohttp==3.14.0
aiohttp-socks==0.11.0 aiomultiprocess==0.9.1 aiosignal==1.4.0 aiosqlite==0.22.1
annotated-doc==0.0.4 annotated-types==0.7.0 anyio==4.12.1 argcomplete==3.6.3
attrs==25.4.0 backoff==2.2.1 beautifulsoup4==4.14.3 censys==2.2.19 certifi==2026.5.20
cffi==2.0.0 charset-normalizer==3.4.4 click==8.3.1 click-plugins==1.1.1.2
colorama==0.4.6 deprecated==1.3.1 dnspython==2.8.0 fastapi==0.136.3 filelock==3.20.3
frozenlist==1.8.0 greenlet==3.3.0 h11==0.16.0 httpcore==1.0.9 httpx==0.28.1 idna==3.15
limits==5.6.0 lxml==6.1.1 markdown-it-py==4.0.0 mdurl==0.1.2 multidict==6.7.0
netaddr==1.3.0 packaging==25.0 playwright==1.60.0 propcache==0.4.1 pycares==5.0.1
pycparser==2.23 pydantic==2.12.5 pydantic-core==2.41.5 pyee==13.0.0 pygments==2.20.0
python-dateutil==2.9.0.post0 python-socks==2.8.0 pyyaml==6.0.3 requests==2.33.0
requests-file==3.0.1 retrying==1.4.2 rich==14.2.0 shodan==1.31.0 six==1.17.0
slowapi==0.1.9 soupsieve==2.8.1 starlette==0.50.0 tldextract==5.3.1
typing-extensions==4.15.0 typing-inspection==0.4.2 ujson==5.12.1 urllib3==2.7.0
uvicorn==0.48.0 winloop==0.6.3 wrapt==2.0.1 xlsxwriter==3.2.9 yarl==1.22.0
""".split())
PYTHON_PINS = {"arjun": ARJUN_PINS, "photon": PHOTON_PINS,
               "dnsrecon": DNSRECON_PINS, "theHarvester": HARVESTER_PINS}
TOOL_VERSIONS = {name: item["version"] for name, item in {**WINDOWS_RELEASES, **SOURCE_ARCHIVES}.items()}
TOOL_VERSIONS["arjun"] = ARJUN_VERSION
MANUAL_TOOLS = {"nmap": ("Install official Windows Nmap from https://nmap.org/download.html and rerun setup. "
                         "Its interactive installer may request administrator permission. "
                         "Setup never opens installers, installs drivers, or changes security settings."),
                "nikto": ("Install Strawberry Perl from https://strawberryperl.com/ and make sure perl.exe is on PATH, "
                          "then rerun Setup all tools. Echo Recon downloads the pinned official Nikto source but does not "
                          "install a separate Windows Perl runtime.")}
ALLOWED_URLS = frozenset([item[key] for item in WINDOWS_RELEASES.values() for key in ("url", "checksums_url")]
                        + [item["url"] for item in SOURCE_ARCHIVES.values()])
ALLOWED_HOSTS = frozenset({"github.com", "codeload.github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"})


class SetupError(RuntimeError):
    """Expected setup failure with an actionable terminal message."""


def managed_root(local_app_data=None):
    """Shared user storage outside virtualized AppData; never creates anything.

    An explicit local_app_data keeps the original caller-supplied override.
    The default must be the same for desktop and packaged-app processes.
    """
    local = Path(local_app_data) if local_app_data is not None else Path.home() / "Tools"
    if not local.is_absolute():
        raise SetupError("Tool storage must name an absolute local folder.")
    return local / "EchoRecon/tooling"


def tool_folder(name, local_app_data=None):
    if name not in TOOL_VERSIONS:
        raise SetupError(f"No automatic native Windows installer for {name}.")
    return managed_root(local_app_data) / f"{name}-{TOOL_VERSIONS[name]}"


def _redirected(path):
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        return True
    try:
        return bool(getattr(path.lstat(), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024))
    except FileNotFoundError:
        return False


def plain_path(path):
    """Reject symlinks, junctions and other reparse points in every component."""
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise SetupError(f"Setup requires an absolute path without parent traversal: {path}")
    for part in (*reversed(path.parents), path):
        if _redirected(part):
            raise SetupError(f"Setup path is a symlink/junction/reparse point: {part}. Kept untouched; inspect it manually.")
    return path


def marker_data(name):
    source = {**WINDOWS_RELEASES, **SOURCE_ARCHIVES}.get(name)
    digest = source["sha256"] if source else ARJUN_SOURCE.rsplit("=", 1)[1]
    return {"schema": SCHEMA, "name": name, "version": TOOL_VERSIONS[name],
            "source_sha256": digest, "complete": True}


def _command_in(name, folder):
    if name in WINDOWS_RELEASES:
        return (str(folder / "bin" / f"{name}.exe"),)
    if name == "nikto":
        perl = shutil.which("perl.exe") or shutil.which("perl")
        if not perl or Path(perl).suffix.lower() != ".exe":
            return None
        return (perl, str(folder / "source/program/nikto.pl"))
    python = str(folder / "venv/Scripts/python.exe")
    if name == "photon":
        return (python, str(folder / "source/photon.py"))
    if name in {"dnsrecon", "theHarvester"}:
        return (str(folder / "venv/Scripts" / f"{name}.exe"),)
    return (python, "-m", "arjun")


def tool_command(name, local_app_data=None):
    """Read-only resolver: explicit argv with complete strict metadata only.

    Diagnostics must still verify help/identity before advertising readiness.
    """
    if name not in TOOL_VERSIONS:
        return None
    try:
        folder = plain_path(tool_folder(name, local_app_data))
        owner = plain_path(folder.parent / ".echo-recon-managed")
        if not owner.is_file() or owner.stat().st_size > 4096 or owner.read_text(encoding="utf-8") != MARKER:
            return None
        metadata = plain_path(folder / TOOL_MARKER)
        if not metadata.is_file() or metadata.stat().st_size > 4096:
            return None
        if json.loads(metadata.read_text(encoding="utf-8")) != marker_data(name):
            return None
        command = _command_in(name, folder)
        if not command:
            return None
        targets = [Path(command[0])]
        if name in {"photon", "nikto"}:
            targets.append(Path(command[1]))
        if not all(plain_path(path).is_file() for path in targets):
            return None
        return command
    except (SetupError, OSError, ValueError, TypeError):
        return None


def validate_platform():
    if sys.platform != "win32":
        raise SetupError("This installer requires native Windows. On Kali use setup_tools.py.")
    if struct.calcsize("P") != 8 or platform.machine().lower() not in {"amd64", "x86_64"}:
        raise SetupError("Automatic native setup supports Windows x64 (AMD64) only.")
    if tuple(sys.version_info[:2]) != (3, 12):
        raise SetupError("Run this installer with normal Windows Python 3.12, using the dashboard launcher.")
    if ctypes.windll.shell32.IsUserAnAdmin():
        raise SetupError("Run setup as your normal Windows user; an administrator terminal is unnecessary.")


def show_plan(local_app_data=None, output=print):
    output("Echo Recon native Windows backend setup — READ-ONLY PLAN")
    output("No command, local probe, download, write, or scan is run in this mode.")
    output("With --install: existing tools that pass help/identity checks are skipped.")
    output(f"User-local immutable version folders: {managed_root(local_app_data)}")
    for name, item in WINDOWS_RELEASES.items():
        output(f"  {name} {item['version']}: {item['url']}")
        output(f"    SHA256 {item['sha256']}; official checksum manifest: {item['checksums_url']}")
    for name, item in SOURCE_ARCHIVES.items():
        output(f"  {name} {item['version']}: {item['url']} (pinned SHA256 {item['sha256']})")
    output(f"  arjun {ARJUN_VERSION}: official PyPI source with pinned SHA256; isolated Python 3.12 venv")
    output("Python tools each receive their own venv and exact runtime pins from official PyPI.")
    output("Nmap: " + MANUAL_TOOLS["nmap"])
    output("Nikto: " + MANUAL_TOOLS["nikto"])
    output("No PATH/profile/Registry changes, driver installation, elevation, WSL, or remote installer pipes.")
    output("Existing version folders are never replaced; unrecognized or partial collisions stop that tool.")
    output("New Nuclei engines fetch official templates; --update-templates also refreshes an existing ready engine.")
    output("Templates are current official content, not a pinned snapshot. No target is scanned.")
    output("Run: python setup_tools_windows.py --install")


def _check_https_host(url):
    parsed = urllib.parse.urlsplit(url)
    try:
        valid = parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS and parsed.port in {None, 443}
    except ValueError:
        valid = False
    if not valid or parsed.username or parsed.password:
        raise SetupError("Download redirect left the fixed HTTPS source allowlist.")


class FixedSourceRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _check_https_host(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(url, limit=MAX_DOWNLOAD):
    if url not in ALLOWED_URLS:
        raise SetupError("Download URL is not one of the fixed official sources.")
    _check_https_host(url)
    opener = urllib.request.build_opener(FixedSourceRedirect())
    request = urllib.request.Request(url, headers={"User-Agent": "Echo-Recon-native-setup/1"})
    try:
        with opener.open(request, timeout=60) as response:
            _check_https_host(response.geturl())
            blocks, size = [], 0
            while True:
                block = response.read(min(1024 * 1024, limit + 1 - size))
                if not block:
                    return b"".join(blocks)
                size += len(block)
                if size > limit:
                    raise SetupError("Official download exceeds the reviewed size limit.")
                blocks.append(block)
    except (OSError, urllib.error.URLError) as exc:
        raise SetupError(f"Official download failed: {exc}") from exc


def verify_sha256(data, expected):
    if not re.fullmatch(r"[0-9a-f]{64}", expected) or hashlib.sha256(data).hexdigest() != expected:
        raise SetupError("SHA256 verification failed. Download was not extracted or executed.")


def checksum_for(manifest, filename):
    try:
        rows = manifest.decode("utf-8").splitlines()
    except UnicodeError as exc:
        raise SetupError("Official checksum manifest is not valid UTF-8.") from exc
    matches = []
    for row in rows:
        match = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?([^\s]+)", row.strip())
        if match and match[2] == filename:
            matches.append(match[1].lower())
    if len(matches) != 1:
        raise SetupError("Official checksum manifest must contain exactly one selected Windows asset.")
    return matches[0]


def _zip_parts(info):
    name = info.orig_filename
    parts = PurePosixPath(name).parts
    devices = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
    mode = info.external_attr >> 16
    if (not name or "\\" in name or "\x00" in name or name.startswith("/") or
            any(part in {".", ".."} or ":" in part or part.endswith((".", " ")) or
                part.split(".")[0].lower() in devices for part in parts) or
            stat.S_IFMT(mode) not in {0, stat.S_IFREG, stat.S_IFDIR}):
        raise SetupError(f"Unsafe ZIP member refused: {name!r}")
    return parts


def extract_zip(data, destination, *, prefix=None, binary=None):
    """Validate every ZIP member before writing selected regular files."""
    destination = plain_path(destination)
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries, seen, total = [], set(), 0
            if len(archive.infolist()) > 5000:
                raise SetupError("ZIP has too many members.")
            for info in archive.infolist():
                parts = _zip_parts(info)
                if prefix:
                    if not parts or parts[0] != prefix:
                        raise SetupError("Source ZIP root does not match the pinned commit.")
                    parts = parts[1:]
                if not parts:
                    continue
                key = "/".join(parts).casefold()
                if key in seen:
                    raise SetupError("ZIP has duplicate or case-colliding paths.")
                seen.add(key)
                total += info.file_size
                if info.flag_bits & 1 or total > MAX_UNPACKED:
                    raise SetupError("Encrypted or oversized ZIP refused.")
                if info.is_dir():
                    continue
                if binary and not (len(parts) == 1 and (parts[0] == binary or parts[0].upper().startswith(("LICENSE", "COPYING", "NOTICE")))):
                    continue
                entries.append((info, parts))
            if binary and not any(parts == (binary,) for _, parts in entries):
                raise SetupError("Official Windows ZIP has no expected executable.")
            for info, parts in entries:
                target = plain_path(destination.joinpath(*parts))
                if os.path.lexists(target):
                    raise SetupError(f"ZIP extraction refuses an existing file: {target}")
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open("xb") as output:
                    written = 0
                    while block := source.read(1024 * 1024):
                        written += len(block)
                        if written > info.file_size or written > MAX_UNPACKED:
                            raise SetupError("ZIP expanded beyond its declared limit.")
                        output.write(block)
    except (zipfile.BadZipFile, RuntimeError) as exc:
        if isinstance(exc, SetupError):
            raise
        raise SetupError(f"Official ZIP could not be read safely: {exc}") from exc


class Installer:
    def __init__(self, local_app_data=None, run=None, fetch=None, check_tools=None, output=None, python=None):
        self.local_app_data = local_app_data
        self.base = managed_root(local_app_data)
        self.run = run or subprocess.run
        self.fetch = fetch or download
        self.check_tools = check_tools
        self.output = output or (lambda text: print(text, flush=True))
        self.python = str(python or sys.executable)
        self.env = dict(os.environ)
        for key in list(self.env):
            if key.upper().startswith(("PIP_", "PYTHON", "GIT_")):
                self.env.pop(key, None)
        self.env.update(PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", PIP_CONFIG_FILE=os.devnull,
                        PIP_NO_INPUT="1", PIP_DISABLE_PIP_VERSION_CHECK="1")

    def command(self, args, *, capture=False):
        args = [str(arg) for arg in args]
        self.output("\n> " + subprocess.list2cmdline(args))
        options = dict(check=True, shell=False, env=self.env)
        if capture:
            options.update(stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=20)
        try:
            return self.run(args, **options)
        except subprocess.CalledProcessError as exc:
            raise SetupError(f"Command failed (exit {exc.returncode}): {Path(args[0]).name}") from exc
        except subprocess.TimeoutExpired as exc:
            raise SetupError(f"Local check timed out: {Path(args[0]).name}") from exc
        except OSError as exc:
            raise SetupError(f"Cannot run {args[0]}: {exc}") from exc

    def health(self):
        if self.check_tools:
            return self.check_tools()
        from echo_recon.tools import diagnostics
        return diagnostics()

    def check_storage(self):
        plain_path(self.base)
        marker = plain_path(self.base / ".echo-recon-managed")
        if self.base.exists() and (not self.base.is_dir() or not marker.is_file() or
                                   marker.read_text(encoding="utf-8") != MARKER):
            raise SetupError(f"Unrecognized existing tooling folder: {self.base}. No files were replaced; inspect it manually.")

    def check_collision(self, name):
        folder = plain_path(tool_folder(name, self.local_app_data))
        if os.path.lexists(folder):
            raise SetupError(f"Existing version folder was preserved: {folder}. It did not pass checks; inspect/relocate it manually before retrying.")
        return folder

    def prepare(self):
        self.check_storage()
        if not self.base.exists():
            self.base.mkdir(parents=True, exist_ok=False)
            (self.base / ".echo-recon-managed").write_text(MARKER, encoding="utf-8")

    def new_folder(self, name):
        folder = self.check_collision(name)
        folder.mkdir(exist_ok=False)
        # Failed partial environments stay visible for manual inspection.
        # No user files or older versions are deleted automatically.
        (folder / ".echo-recon-pending").write_text(f"{name} {TOOL_VERSIONS[name]}\n", encoding="utf-8")
        return folder

    def complete(self, name, folder):
        command = _command_in(name, folder)
        if (not command or not plain_path(Path(command[0])).is_file() or
                (name in {"photon", "nikto"} and not plain_path(Path(command[1])).is_file())):
            raise SetupError("Expected installed entry point is missing; incomplete environment was preserved.")
        with (folder / TOOL_MARKER).open("x", encoding="utf-8") as metadata:
            metadata.write(json.dumps(marker_data(name), sort_keys=True) + "\n")

    def install_release(self, name):
        self.check_collision(name)
        item = WINDOWS_RELEASES[name]
        manifest = self.fetch(item["checksums_url"], limit=100_000)
        verify_sha256(manifest, item["checksums_sha256"])
        expected = checksum_for(manifest, item["asset"])
        if expected != item["sha256"]:
            raise SetupError("Official manifest differs from the reviewed Windows asset digest.")
        payload = self.fetch(item["url"])
        verify_sha256(payload, expected)
        folder = self.new_folder(name)
        extract_zip(payload, folder / "bin", binary=name + ".exe")
        self.complete(name, folder)

    def install_python(self, name):
        self.check_collision(name)
        payload = None
        if name in SOURCE_ARCHIVES:
            item = SOURCE_ARCHIVES[name]
            payload = self.fetch(item["url"])
            verify_sha256(payload, item["sha256"])
        folder = self.new_folder(name)
        if payload is not None:
            extract_zip(payload, folder / "source", prefix=item["prefix"])
        venv = folder / "venv"
        # Windows console entry EXEs embed the interpreter location, so create
        # the venv directly at its final path and never relocate it later.
        self.command([self.python, "-I", "-m", "venv", "--copies", str(venv)])
        python = plain_path(venv / "Scripts/python.exe")
        if not python.is_file():
            raise SetupError("Python did not create the expected isolated Windows interpreter.")
        pip = [str(python), "-I", "-m", "pip", "--isolated", "install", "--disable-pip-version-check",
               "--no-input", "--index-url", "https://pypi.org/simple", "--no-deps"]
        self.command([*pip, "--only-binary=:all:", *BUILD_PINS])
        self.command([*pip, "--no-build-isolation", *PYTHON_PINS[name]])
        if name == "arjun":
            self.command([*pip, "--no-build-isolation", ARJUN_SOURCE])
        elif name != "photon":
            self.command([*pip, "--no-build-isolation", str(folder / "source")])
        self.command([str(python), "-I", "-m", "pip", "--isolated", "check"])
        self.complete(name, folder)

    def install_nikto(self):
        self.check_collision("nikto")
        item = SOURCE_ARCHIVES["nikto"]
        payload = self.fetch(item["url"])
        verify_sha256(payload, item["sha256"])
        folder = self.new_folder("nikto")
        extract_zip(payload, folder / "source", prefix=item["prefix"])
        self.complete("nikto", folder)

    def update_templates(self, health):
        item = health.get("nuclei", {})
        command = item.get("command") or ([item["path"]] if item.get("path") else None)
        if item.get("engine_status", item.get("status")) != "ready" or not command:
            raise SetupError("Nuclei did not pass its local identity check; templates were not updated.")
        if isinstance(command, str) or any(not isinstance(arg, str) for arg in command):
            raise SetupError("Nuclei diagnostic command is invalid; templates were not updated.")
        self.output("Downloading current official Nuclei templates; no target is scanned.")
        self.command([*command, "-update-templates", "-duc"])

    def install(self, update_templates=False):
        from echo_recon.tools import nuclei_templates_incomplete

        initial = self.health()
        needed = [name for name in TOOL_NAMES if initial.get(name, {}).get("status") != "ready"]
        missing_templates = nuclei_templates_incomplete(initial)
        install_needed = [name for name in needed if not (name == "nuclei" and missing_templates)]
        perl_available = bool(shutil.which("perl.exe") or
                              (shutil.which("perl") and Path(shutil.which("perl")).suffix.lower() == ".exe"))
        automatic = [name for name in install_needed if name in TOOL_VERSIONS and
                     not (name == "nikto" and not perl_available)]
        for name in TOOL_NAMES:
            if name == "nuclei" and missing_templates:
                status = "TEMPLATE CHECK NEEDS REPAIR — refresh official templates only"
            else:
                status = ("SKIP — existing tool passed local checks" if name not in needed else
                          ("MANUAL — " + MANUAL_TOOLS[name] if name in MANUAL_TOOLS else "needs setup"))
            self.output(f"{name}: {status}")
        if automatic:
            self.check_storage()
            # Check every collision before the first download or command.
            for name in automatic:
                self.check_collision(name)
            self.prepare()
        failures, new_nuclei = [], False
        for name in automatic:
            try:
                if name in WINDOWS_RELEASES:
                    self.install_release(name)
                elif name == "nikto":
                    self.install_nikto()
                else:
                    self.install_python(name)
                new_nuclei |= name == "nuclei"
            except (SetupError, OSError) as exc:
                failures.append(name)
                self.output(f"SETUP ERROR — {name}: {exc}")
        final = self.health() if automatic or update_templates or missing_templates else initial
        if new_nuclei or update_templates or missing_templates:
            try:
                self.update_templates(final)
                final = self.health()
            except SetupError as exc:
                failures.append("nuclei templates")
                self.output(f"TEMPLATE ERROR — {exc}")
        not_ready = []
        self.output("\nFinal local checks (help/identity only):")
        for name in TOOL_NAMES:
            item = final.get(name, {})
            status, detail = item.get("status", "unknown"), item.get("detail", "No check result")
            if name in MANUAL_TOOLS and status != "ready":
                status, detail = "manual", MANUAL_TOOLS[name]
            self.output(f"  {name}: {status} — {detail}")
            if status != "ready":
                not_ready.append(name)
        if failures or not_ready:
            self.output("Setup is incomplete. Review the listed tools; existing files and tools were preserved.")
            return 2 if not failures and set(not_ready).issubset(MANUAL_TOOLS) else 1
        self.output("All 9 tools passed local checks; the local Nuclei template version was also found. Refresh Check installed tools in the dashboard.")
        self.output("These checks do not verify every template file, API credentials, upstream sources, or assessment results.")
        return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="Read-only plan (default)")
    mode.add_argument("--install", action="store_true", help="Install supported missing tools for the current Windows user")
    parser.add_argument("--update-templates", action="store_true", help="With --install, refresh an existing ready Nuclei's templates")
    parser.add_argument("--pause", action="store_true", help="Keep this interactive terminal open until Enter")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data", help="Trusted dashboard data directory for the shared setup lock")
    args = parser.parse_args(argv)
    if args.update_templates and not args.install:
        parser.error("--update-templates requires --install")
    lock = None
    try:
        if not args.install:
            show_plan()
            return 0
        validate_platform()
        print("Echo Recon native Windows setup. No scan is run.", flush=True)
        show_plan(output=lambda text: print(text, flush=True))
        data = plain_path(args.data_dir.expanduser())
        data.mkdir(parents=True, exist_ok=True)
        plain_path(data / "setup-tools.lock")
        try:
            lock = InstanceLock(data / "setup-tools.lock").acquire()
        except RuntimeError as exc:
            raise SetupError("Another backend setup is already running. Finish/close that terminal before retrying.") from exc
        return Installer().install(update_templates=args.update_templates)
    except (SetupError, OSError) as exc:
        print(f"\nSetup stopped: {exc}", file=sys.stderr, flush=True)
        return 1
    except KeyboardInterrupt:
        print("\nSetup interrupted. Existing tools and partial environments were preserved for inspection.", file=sys.stderr, flush=True)
        return 130
    finally:
        if lock:
            lock.release()
        if args.pause and sys.stdin.isatty():
            try:
                input("\nPress Enter to close this setup terminal...")
            except (EOFError, KeyboardInterrupt):
                pass


if __name__ == "__main__":
    raise SystemExit(main())
