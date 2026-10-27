#!/usr/bin/env python3
"""Interactive, fixed-source backend setup for a normal Linux user.

Default/--plan only reads local paths: no commands, network requests or writes.
--install executes a conditional plan, then verifies all nine tool adapters.
No scan target is accepted and no assessment is started by this program.
"""
import argparse
import importlib.util
import platform
import urllib.request
import urllib.error
import os
from pathlib import Path
import re
import shlex
import ssl
import shutil
import subprocess
import sys
import tempfile

# Keep even project-module bytecode caches out of the read-only CLI plan.
sys.dont_write_bytecode = True

from echo_recon.locking import InstanceLock
from echo_recon.tools import TOOLS, diagnostics, nuclei_templates_incomplete


ROOT = Path(__file__).resolve().parent
GO_MINIMUM = (1, 26)
GO_MODULES = {
    "subfinder": "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@v2.17.0",
    "httpx": "github.com/projectdiscovery/httpx/cmd/httpx@v1.12.0",
    "nuclei": "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@v3.11.1",
}
APT_TOOLS = {"dnsrecon": "dnsrecon", "nmap": "nmap", "theHarvester": "theharvester",
             "nikto": "nikto"}
PHOTON_URL = "https://github.com/s0md3v/Photon.git"
PHOTON_COMMIT = "c8d2566841d69a268b244609921143d84b72b0c6"
ARJUN_VERSION = "2.2.7"
PORTABLE_SOURCE_VERSIONS = {"dnsrecon": "1.6.3", "theHarvester": "4.11.1", "nikto": "2.6.1"}
PORTABLE_NIKTO_PERL_PACKAGES = {
    "apt": ("perl", "libio-socket-ssl-perl", "libnet-ssleay-perl", "libxml-writer-perl"),
    "dnf": ("perl", "perl-IO-Socket-SSL", "perl-Net-SSLeay", "perl-XML-Writer"),
    "pacman": ("perl", "perl-io-socket-ssl", "perl-net-ssleay", "perl-xml-writer"),
    "zypper": ("perl", "perl-IO-Socket-SSL", "perl-Net-SSLeay", "perl-XML-Writer"),
}
# Package names are fixed, never supplied by browser input. No third-party
# distro repository, profile edits, remote shell pipe, or whole-system upgrade.
LINUX_FAMILIES = {
    "apt": {"ids": {"debian", "ubuntu", "linuxmint", "pop", "raspbian"}, "manager": "/usr/bin/apt-get",
            "base": ("python3-venv", "ca-certificates")},
    "dnf": {"ids": {"fedora", "rhel", "centos", "rocky", "almalinux", "ol"}, "manager": "/usr/bin/dnf",
            "base": ("python3-pip", "ca-certificates")},
    "pacman": {"ids": {"arch", "manjaro", "endeavouros"}, "manager": "/usr/bin/pacman",
               "base": ("python-pip", "ca-certificates")},
    "zypper": {"ids": {"opensuse", "opensuse-leap", "opensuse-tumbleweed", "sles", "sled"}, "manager": "/usr/bin/zypper",
               "base": ("python3-pip", "ca-certificates")},
}
# Exact runtime pins from the packages' official PyPI metadata. Build helpers
# are pinned too, and source distributions build only inside the tool venv.
BUILD_PINS = ("setuptools==80.9.0", "wheel==0.45.1", "packaging==25.0")
REQUEST_PINS = ("requests==2.34.2", "charset-normalizer==3.5.2", "idna==3.20",
                "urllib3==2.8.0", "certifi==2026.10.23")
ARJUN_PINS = (f"arjun=={ARJUN_VERSION}", "dicttoxml==1.7.16", "ratelimit==2.2.1", *REQUEST_PINS)
PHOTON_PINS = ("tld==0.13.2", "PySocks==1.7.1", *REQUEST_PINS)
MARKER = "Echo Recon managed backend environments v1\n"
WRAPPER_MARKER = "# Echo Recon managed tool launcher v1"


class SetupError(RuntimeError):
    """Expected setup failure with an actionable terminal message."""


def local_path(home):
    """Use the same user-bin precedence as run.sh, without editing profiles."""
    return os.pathsep.join((str(home / ".local/bin"), str(home / "go/bin"),
                            "/usr/local/go/bin", os.environ.get("PATH", "")))


def managed_root(home):
    return home / ".local/share/echo-recon/tooling"


def go_target(home, name):
    version = GO_MODULES[name].rsplit("@", 1)[1]
    return managed_root(home) / f"{name}-{version}" / "bin" / name


def tool_target(home, name):
    if name in GO_MODULES:
        return go_target(home, name), ()
    if name in PORTABLE_SOURCE_VERSIONS:
        if name == "nikto":
            folder = managed_root(home) / f"nikto-{PORTABLE_SOURCE_VERSIONS[name]}"
            return folder / "source/program/nikto.pl", ()
        return managed_root(home) / f"{name}-{PORTABLE_SOURCE_VERSIONS[name]}" / f"venv/bin/{name}", ()
    if name == "arjun":
        return managed_root(home) / f"arjun-{ARJUN_VERSION}" / "venv/bin/arjun", ()
    if name == "photon":
        folder = managed_root(home) / f"photon-{PHOTON_COMMIT}"
        return folder / "venv/bin/python", (str(folder / "source/photon.py"),)
    raise SetupError(f"No user-local installer for {name}.")


def wrapper_text(home, name):
    target, extra = tool_target(home, name)
    if name == "nikto":
        return (f"#!/bin/sh\n{WRAPPER_MARKER}\n# tool: {name}\n"
                f"exec /usr/bin/perl {shlex.quote(str(target))} \"$@\"\n")
    return (f"#!/bin/sh\n{WRAPPER_MARKER}\n# tool: {name}\n"
            f"exec {shlex.join([str(target), *extra])} \"$@\"\n")


def check_wrapper(home, name):
    """Never replace another project's file, symlink or broken symlink."""
    path = home / ".local/bin" / name
    if os.path.lexists(path):
        if (path.is_symlink() or not path.is_file() or
                path.read_text(encoding="utf-8", errors="replace") != wrapper_text(home, name)):
            raise SetupError(
                f"Command conflict: {path} is not this installer's launcher. Nothing was overwritten. "
                "Inspect it and choose manually which command to keep; rename/move your own conflicting "
                "launcher before retrying. System executables are never moved or deleted.")


def show_plan(home=None, output=print):
    """No subprocesses, diagnostic probes, mkdir or network activity here."""
    home = Path(home or Path.home())
    output("Echo Recon backend setup — READ-ONLY PLAN (Linux native / WSL / VirtualBox)")
    output("No command, download, installation or scan is run in this mode.")
    output("With --install: check local help/version identity first; skip every ready tool.")
    output("Existing ready tools stay in place. Any sudo prompt stays in the visible terminal for fixed OS packages.")
    for name in TOOLS:
        path = shutil.which(name, path=local_path(home))
        output(f"  {name}: {path or 'not on PATH'} (not probed in plan mode)")
    output("Kali branch only — conditional apt packages: dnsrecon, nmap, theharvester, nikto; missing prerequisites:")
    output("  Kali: python3-venv, git, ca-certificates, golang-go. Go >=1.26 is required; no Go bootstrap scripts.")
    output("  sudo /usr/bin/apt-get update")
    output("  sudo /usr/bin/apt-get install --yes --no-install-recommends <needed fixed packages above>")
    output(f"User-local environments: {managed_root(home)}")
    for name, module in GO_MODULES.items():
        output(f"  {name}: go install -v {module} (isolated GOBIN, verified public Go module checksums)")
    output("  arjun: isolated venv; pinned PyPI runtime: " + ", ".join(ARJUN_PINS))
    output(f"  photon: {PHOTON_URL} at exact commit {PHOTON_COMMIT}; isolated venv")
    output("    Pinned PyPI runtime: " + ", ".join(PHOTON_PINS))
    output("  Python build helpers: " + ", ".join(BUILD_PINS))
    output("Nuclei: newly installed engines download official templates with -update-templates.")
    output("Existing ready Nuclei/templates are untouched unless --update-templates is explicitly added.")
    output("Template refresh downloads current official templates (not a pinned template snapshot); no target is scanned.")
    output("Nikto: Kali uses the official distro package. Other supported Linux families use the pinned Nikto 2.6.1 source and Perl runtime packages.")
    output("Launchers are added in ~/.local/bin only when absent or exactly managed by this installer.")
    output("Other supported distro families: Debian/Ubuntu (apt), Fedora/RHEL (dnf), Arch (pacman), openSUSE (zypper).")
    output("Portable branch: fixed distro packages for Nmap/prerequisites, pinned official Linux amd64/arm64 binaries (no Go SDK) and isolated Python >=3.12 source environments.")
    output("Alpine/musl and other architectures are not automatic-install targets; working tools are still usable manually.")
    output("Portable Python dependencies resolve from official PyPI using the pinned upstream project's requirements; no cross-platform lock is claimed.")
    output("Run: python3 setup_tools.py --install   (terminal; may take several minutes and require free disk/RAM)")


def linux_family(values=None):
    """Read only os-release. Unknown/musl distributions never get guessed commands."""
    if values is None:
        try:
            values = {}
            for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
                key, sep, value = line.partition("=")
                if sep:
                    values[key] = value.strip().strip('"')
        except OSError as exc:
            raise SetupError("Cannot identify Linux distribution. Install backends manually from their official sources.") from exc
    distro = values.get("ID", "").lower()
    if distro == "kali":
        return "kali"
    if distro == "alpine":
        raise SetupError("Alpine/musl is not an automatic-install target: upstream browser/Python wheels require glibc. Use a supported glibc distro or install compatible tools manually.")
    identities = {distro, *values.get("ID_LIKE", "").lower().split()}
    for family, settings in LINUX_FAMILIES.items():
        if identities & settings["ids"]:
            return family
    raise SetupError("Automatic Linux setup supports Kali, Debian/Ubuntu, Fedora/RHEL, Arch and openSUSE families. This distribution needs manual official tool installation.")


def validate_platform():
    if sys.platform != "linux":
        raise SetupError("Use native Windows setup_tools_windows.py on Windows, or this script inside Linux/WSL2.")
    if os.geteuid() == 0:
        raise SetupError("Run as your normal Linux user, not root or sudo python. OS packages request sudo separately.")
    return linux_family()


class Installer:
    def __init__(self, home=None, run=None, check_tools=None, output=print):
        self.home = Path(home or Path.home())
        self.base = managed_root(self.home)
        self.run = run or subprocess.run
        self.check_tools = check_tools or diagnostics
        self.output = output
        self.env = dict(os.environ, PATH=local_path(self.home))
        for key in list(self.env):
            if key.startswith("GIT_") or key in {"PYTHONPATH", "PYTHONHOME", "PYTHONUSERBASE", "PYTHONSTARTUP"}:
                self.env.pop(key, None)
        self.env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null",
                        GIT_CONFIG_COUNT="0", GIT_TERMINAL_PROMPT="0", PYTHONNOUSERSITE="1",
                        PIP_CONFIG_FILE="/dev/null")

    def safe_managed_path(self, path):
        """Never follow a redirected storage component while writing tooling."""
        path = Path(path)
        try:
            relative = path.relative_to(self.base)
        except ValueError as exc:
            raise SetupError(f"Setup path is outside managed storage: {path}") from exc
        current = self.base
        for part in (None, *relative.parts):
            if part is not None:
                current = current / part
            if current.is_symlink():
                raise SetupError(f"Managed setup path is a symlink: {current}. Kept untouched; inspect it before retrying.")
        if not path.resolve().is_relative_to(self.base.resolve()):
            raise SetupError(f"Resolved setup path escapes managed storage: {path}")
        return path

    def check_managed_tree(self, path):
        """Reject pre-existing redirected children before git/pip/go can use them.

        Python's normal venv lib64 -> lib link is the one permitted exception:
        it is not an execution target and resolves within that same venv.
        The venv interpreter is created with --copies, not external symlinks.
        """
        path = self.safe_managed_path(path)
        if path.exists():
            for entry in path.rglob("*"):
                if entry.is_symlink():
                    if (entry.name == "lib64" and entry.parent.name == "venv" and
                            entry.resolve() == (entry.parent / "lib").resolve()):
                        continue
                    raise SetupError(f"Managed storage contains a symlink: {entry}. Kept untouched; inspect it before retrying.")
        return path

    def command(self, args, *, env=None, cwd=None, capture=False):
        args = [str(arg) for arg in args]
        self.output("\n$ " + shlex.join(args))
        options = dict(check=True, shell=False, env=env or self.env, cwd=cwd)
        if capture:
            options.update(stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=20)
        try:
            result = self.run(args, **options)
        except subprocess.CalledProcessError as exc:
            if capture and exc.stdout:
                self.output(str(exc.stdout).strip())
            raise SetupError(f"Command failed (exit {exc.returncode}): {shlex.join(args)}") from exc
        except subprocess.TimeoutExpired as exc:
            raise SetupError(f"Local version/configuration check timed out: {args[0]}") from exc
        except OSError as exc:
            raise SetupError(f"Cannot run {args[0]}: {exc}") from exc
        if capture:
            text = result.stdout or ""
            self.output(text.strip())
            return text.strip()
        return result

    def health(self):
        # diagnostics uses the launcher's PATH exactly. Never modify the user's
        # shell configuration or process-wide PATH after setup has finished.
        previous = os.environ.get("PATH")
        os.environ["PATH"] = self.env["PATH"]
        try:
            return self.check_tools()
        finally:
            if previous is None:
                os.environ.pop("PATH", None)
            else:
                os.environ["PATH"] = previous

    def choose_go(self):
        candidates = [shutil.which("go", path=self.env["PATH"]), "/usr/bin/go"]
        seen = set()
        for candidate in candidates:
            if not candidate or candidate in seen or not Path(candidate).is_file():
                continue
            seen.add(candidate)
            try:
                version = self.command([candidate, "version"], capture=True)
            except SetupError:
                continue
            match = re.search(r"\bgo(\d+)\.(\d+)(?:\.\d+)?\b", version)
            if match and tuple(map(int, match.groups())) >= GO_MINIMUM:
                return candidate
        return None

    def package_present(self, name):
        try:
            return self.command(["/usr/bin/dpkg-query", "-W", "-f=${db:Status-Status}", name], capture=True) == "installed"
        except SetupError:
            return False

    def prerequisites(self, needed):
        packages = [APT_TOOLS[name] for name in needed if name in APT_TOOLS]
        if any(name in {"arjun", "photon"} for name in needed) and not self.package_present("python3-venv"):
            packages.append("python3-venv")
        if "photon" in needed and not Path("/usr/bin/git").is_file():
            packages.append("git")
        go = self.choose_go() if any(name in GO_MODULES for name in needed) else None
        if any(name in GO_MODULES for name in needed) and not go:
            packages.append("golang-go")
        if needed and not self.package_present("ca-certificates"):
            packages.append("ca-certificates")
        if packages:
            if not sys.stdin.isatty():
                raise SetupError("Apt needs an interactive terminal for sudo. Open Kali Terminal and run python3 setup_tools.py --install.")
            self.output("Only these fixed Kali apt packages are requested: " + ", ".join(packages))
            self.command(["/usr/bin/sudo", "/usr/bin/apt-get", "update"])
            self.command(["/usr/bin/sudo", "/usr/bin/apt-get", "install", "--yes", "--no-install-recommends", *packages])
        if any(name in GO_MODULES for name in needed) and not go:
            go = self.choose_go()
            if not go:
                raise SetupError("These pinned Go tools require Go >=1.26. Kali's golang-go is still too old or not on disk. Update your Kali package sources/Go manually, then retry; no bootstrap script was downloaded.")
        return go

    def check_storage(self):
        # Refuse redirected managed storage instead of modifying unknown files.
        for path in (self.home / ".local", self.home / ".local/share",
                     self.base.parent, self.base, self.home / ".local/bin"):
            if path.is_symlink():
                raise SetupError(f"Managed setup path is a symlink: {path}. Inspect it before using automatic setup.")
        marker = self.base / ".echo-recon-managed"
        if self.base.exists() and (not marker.is_file() or marker.is_symlink() or
                                   marker.read_text(encoding="utf-8") != MARKER):
            raise SetupError(f"Unrecognized existing folder: {self.base}. No files were replaced. Inspect/relocate it manually before retrying.")

    def prepare(self):
        self.check_storage()
        marker = self.base / ".echo-recon-managed"
        self.base.mkdir(parents=True, exist_ok=True, mode=0o700)
        marker.write_text(MARKER, encoding="utf-8")
        (self.home / ".local/bin").mkdir(parents=True, exist_ok=True)

    def write_wrapper(self, name):
        check_wrapper(self.home, name)
        target, _ = tool_target(self.home, name)
        self.safe_managed_path(target)
        if not target.is_file():
            raise SetupError(f"Expected installed executable is missing: {target}. Launcher was not written.")
        folder = self.home / ".local/bin"
        descriptor, temporary = tempfile.mkstemp(prefix=f".echo-{name}-", dir=folder)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(wrapper_text(self.home, name))
            os.chmod(temporary, 0o755)
            # Recheck immediately before replacing an existing managed launcher.
            check_wrapper(self.home, name)
            os.replace(temporary, folder / name)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        self.output(f"Managed launcher ready: {folder / name}")

    def install_go(self, name, go):
        target, _ = tool_target(self.home, name)
        self.check_managed_tree(target.parent.parent)
        self.safe_managed_path(target)
        self.check_managed_tree(self.base / "go-cache")
        target.parent.mkdir(parents=True, exist_ok=True)
        env = dict(self.env, GOBIN=str(target.parent), GOPATH=str(self.base / "go-cache"),
                   GOMODCACHE=str(self.base / "go-cache/pkg/mod"), GOCACHE=str(self.base / "go-cache/build"),
                   GOENV="off", GOWORK="off", GOFLAGS="-p=2", GOMAXPROCS="2", GOTOOLCHAIN="local", CGO_ENABLED="0",
                   GOPROXY="https://proxy.golang.org", GOSUMDB="sum.golang.org", GOPRIVATE="",
                   GONOPROXY="", GONOSUMDB="")
        self.command([go, "install", "-v", GO_MODULES[name]], env=env)
        self.write_wrapper(name)

    def install_python(self, folder, pins):
        self.check_managed_tree(folder)
        venv = folder / "venv"
        python = venv / "bin/python"
        self.safe_managed_path(venv / "bin")
        self.safe_managed_path(python)
        self.command(["/usr/bin/python3", "-m", "venv", "--copies", str(venv)])
        self.check_managed_tree(venv)
        pip = [str(python), "-m", "pip", "--isolated", "install", "--disable-pip-version-check",
               "--no-input", "--index-url", "https://pypi.org/simple", "--no-deps"]
        self.command([*pip, "--only-binary=:all:", *BUILD_PINS])
        self.command([*pip, "--no-build-isolation", *pins])
        self.command([str(python), "-m", "pip", "--isolated", "check"])

    def install_photon(self):
        folder = self.base / f"photon-{PHOTON_COMMIT}"
        source = folder / "source"
        self.check_managed_tree(folder)
        self.safe_managed_path(source)
        folder.mkdir(parents=True, exist_ok=True)
        git = ["/usr/bin/git", "-c", "core.hooksPath=/dev/null", "-c", "init.templateDir="]
        if not source.exists():
            self.command([*git, "init", str(source)])
            self.command([*git, "-C", str(source), "remote", "add", "origin", PHOTON_URL])
        origin = self.command([*git, "-C", str(source), "remote", "get-url", "origin"], capture=True)
        if origin != PHOTON_URL:
            raise SetupError(f"Photon source origin differs from the reviewed official URL: {source}. Kept untouched.")
        self.command([*git, "-C", str(source), "fetch", "--depth", "1", "origin", PHOTON_COMMIT])
        self.command([*git, "-C", str(source), "checkout", "--detach", PHOTON_COMMIT])
        actual = self.command([*git, "-C", str(source), "rev-parse", "HEAD"], capture=True)
        if actual != PHOTON_COMMIT:
            raise SetupError("Photon checkout does not match the pinned commit. Setup stopped.")
        self.command([*git, "-C", str(source), "diff", "--exit-code", "HEAD", "--"])
        if not (source / "photon.py").is_file():
            raise SetupError("Pinned Photon source has no photon.py entry point.")
        self.install_python(folder, PHOTON_PINS)
        self.write_wrapper("photon")

    def update_templates(self, health):
        item = health.get("nuclei", {})
        path = item.get("path") or shutil.which("nuclei", path=self.env["PATH"])
        if item.get("engine_status", item.get("status")) != "ready" or not path:
            raise SetupError("Nuclei did not pass its local identity check; templates were not updated.")
        self.output("Downloading current official Nuclei templates only; this does not scan a target.")
        # In the pinned engine, -duc also disables explicit template setup.
        # Read-only diagnostics/scans keep their separate update-disable flag.
        self.command([path, "-update-templates"])

    def install(self, update_templates=False):
        initial = self.health()
        needed = [name for name in TOOLS if initial.get(name, {}).get("status") != "ready"]
        missing_templates = nuclei_templates_incomplete(initial)
        install_needed = [name for name in needed if not (name == "nuclei" and missing_templates)]
        for name in TOOLS:
            status = ("TEMPLATE CHECK NEEDS REPAIR — refresh official templates only" if name == "nuclei" and missing_templates else
                      "SKIP — existing tool passed local checks" if name not in needed else "needs setup/repair")
            self.output(f"{name}: {status}")
        for name in install_needed:
            if name not in APT_TOOLS:
                check_wrapper(self.home, name)
            else:
                current = initial.get(name, {}).get("path")
                expected = Path("/usr/bin") / name
                if current and Path(current).resolve() != expected.resolve():
                    raise SetupError(f"Unverified command shadows Kali's {name}: {current}. It was not replaced. Inspect your PATH/launcher before retrying; the official apt command is {expected}.")
        if not install_needed and not update_templates and not missing_templates:
            self.output("All 9 tools and local Nuclei template data passed checks. No downloads or installations were needed. No scan was run.")
            return 0
        custom_needed = any(name not in APT_TOOLS for name in install_needed)
        if custom_needed:
            self.check_storage()
            if self.base.exists():
                self.check_managed_tree(self.base)
        go = self.prerequisites(install_needed)
        if custom_needed:
            self.prepare()
        failures = []
        new_nuclei = False
        for name in install_needed:
            try:
                if name in GO_MODULES:
                    self.install_go(name, go)
                    new_nuclei |= name == "nuclei"
                elif name == "arjun":
                    self.install_python(self.base / f"arjun-{ARJUN_VERSION}", ARJUN_PINS)
                    self.write_wrapper(name)
                elif name == "photon":
                    self.install_photon()
            except SetupError as exc:
                failures.append(f"{name}: {exc}")
                self.output(f"SETUP ERROR — {name}: {exc}")
        final = self.health()
        if new_nuclei or update_templates or missing_templates:
            try:
                self.update_templates(final)
                final = self.health()
            except SetupError as exc:
                failures.append(str(exc))
                self.output(f"TEMPLATE ERROR — {exc}")
        not_ready = []
        self.output("\nFinal local checks (availability/identity only, no external assessment):")
        for name in TOOLS:
            item = final.get(name, {})
            self.output(f"  {name}: {item.get('status', 'unknown')} — {item.get('detail', '')}")
            if item.get("status") != "ready":
                not_ready.append(name)
        if failures or not_ready:
            self.output("Setup is incomplete. Review errors above; existing tools were not deleted or moved.")
            self.output("Rerunning retries failed/missing tools and skips tools that now pass checks.")
            return 1
        self.output("All 9 tools passed local checks; the local Nuclei template version was also found. Restart the dashboard via bash run.sh and refresh Check installed tools.")
        self.output("These checks do not verify every template file, API credentials, upstream sources or assessment results.")
        return 0


def _portable_assets():
    # Shared immutable hashes/source snapshots, not the Windows validator or
    # Windows execution code. These helpers are platform-neutral and read-only.
    import setup_tools_windows as assets
    return assets


def portable_download(url, limit=200 * 1024 * 1024):
    assets = _portable_assets()
    allowed = {item["url"] for item in assets.SOURCE_ARCHIVES.values()}
    for name, item in assets.WINDOWS_RELEASES.items():
        allowed.add(item["checksums_url"])
        prefix = item["url"].rsplit("/", 1)[0]
        for arch in ("amd64", "arm64"):
            allowed.add(f"{prefix}/{name}_{item['version']}_linux_{arch}.zip")
    if url not in allowed:
        raise SetupError("Download URL is outside the pinned official Linux sources.")
    assets._check_https_host(url)
    opener = urllib.request.build_opener(assets.FixedSourceRedirect())
    request = urllib.request.Request(url, headers={"User-Agent": "Echo-Recon-linux-setup/1"})
    try:
        with opener.open(request, timeout=60) as response:
            assets._check_https_host(response.geturl())
            chunks, total = [], 0
            while True:
                chunk = response.read(min(1024 * 1024, limit + 1 - total))
                if not chunk:
                    return b"".join(chunks)
                total += len(chunk)
                if total > limit:
                    raise SetupError("Official Linux asset exceeds the reviewed size limit.")
                chunks.append(chunk)
    except (OSError, urllib.error.URLError) as exc:
        raise SetupError(f"Official Linux download failed: {exc}") from exc


class PortableInstaller(Installer):
    """Common glibc distro setup without adding Kali repositories or a Go SDK.

    Nmap and missing Python/CA prerequisites use the distro's own package
    manager. Other backends live in isolated, versioned normal-user folders.
    Upstream Python dependencies resolve for this interpreter/platform from
    PyPI, using the pinned project's declared requirements (not a lockfile).
    """
    def __init__(self, family, home=None, run=None, check_tools=None, output=print, fetch=None):
        if family not in LINUX_FAMILIES:
            raise SetupError("Unsupported Linux package manager family.")
        super().__init__(home=home, run=run, check_tools=check_tools, output=output)
        self.family = family
        self.fetch = fetch or portable_download

    def architecture(self):
        arch = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}.get(platform.machine().lower())
        if arch is None:
            raise SetupError("Automatic portable Linux assets support x86_64/AMD64 and aarch64/ARM64. Install other architecture backends manually.")
        return arch

    def prerequisites(self, needed):
        python_needed = any(name not in GO_MODULES and name != "nmap" for name in needed)
        if any(name in {"dnsrecon", "theHarvester"} for name in needed) and tuple(sys.version_info[:2]) < (3, 12):
            raise SetupError("Pinned DNSRecon/theHarvester require Python >=3.12. Install a supported distro Python 3.12+ and recreate the dashboard venv with it before retrying.")
        settings = LINUX_FAMILIES[self.family]
        packages = ["nmap"] if "nmap" in needed else []
        if "nikto" in needed:
            packages.extend(PORTABLE_NIKTO_PERL_PACKAGES[self.family])
            python_needed = any(name not in GO_MODULES and name not in {"nmap", "nikto"} for name in needed)
        if python_needed and any(importlib.util.find_spec(name) is None for name in ("venv", "ensurepip")):
            packages.extend(settings["base"])
        trust = ssl.get_default_verify_paths()
        if needed and not (trust.cafile or trust.capath):
            packages.append("ca-certificates")
        if not packages:
            return
        manager = settings["manager"]
        if not Path(manager).is_file():
            raise SetupError(f"Expected official package manager is missing: {manager}. Configure this distro's supported manager manually.")
        if not sys.stdin.isatty():
            raise SetupError("OS package installation needs an interactive terminal for sudo. Run python3 setup_tools.py --install in your Linux terminal.")
        if not Path("/usr/bin/sudo").is_file():
            raise SetupError("This normal-user installation needs sudo for fixed distro packages. Ask your administrator to install the displayed prerequisites; do not run the dashboard as root.")
        packages = list(dict.fromkeys(packages))
        self.output(f"Only these fixed {self.family} packages are requested: " + ", ".join(packages))
        prefix = ["/usr/bin/sudo", manager]
        if self.family == "apt":
            self.command([*prefix, "update"])
            self.command([*prefix, "install", "--yes", "--no-install-recommends", *packages])
        elif self.family == "dnf":
            self.command([*prefix, "install", "--assumeyes", *packages])
        elif self.family == "pacman":
            self.command([*prefix, "-S", "--needed", "--noconfirm", *packages])
        else:
            self.command([*prefix, "--non-interactive", "install", "--no-recommends", *packages])

    def version_folder(self, name):
        target, _ = tool_target(self.home, name)
        return target.parent.parent.parent if name not in GO_MODULES else target.parent.parent

    def preflight(self, needed, initial):
        self.architecture()
        for name in needed:
            if name != "nmap":
                check_wrapper(self.home, name)
                folder = self.version_folder(name)
                self.safe_managed_path(folder)
                if os.path.lexists(folder):
                    raise SetupError(f"Existing incomplete/unverified tool folder preserved: {folder}. Inspect/relocate it manually before retrying.")
            else:
                path = initial.get(name, {}).get("path")
                if path and Path(path).resolve() != Path("/usr/bin/nmap").resolve():
                    raise SetupError(f"Unverified nmap shadows the official distro command: {path}. Inspect PATH before retrying.")
        if any(name != "nmap" for name in needed):
            self.check_storage()

    def install_release(self, name):
        assets = _portable_assets()
        item = assets.WINDOWS_RELEASES[name]
        if GO_MODULES[name].rsplit("@v", 1)[1] != item["version"]:
            raise SetupError("Shared release metadata differs from the reviewed Linux version; update both pins before setup.")
        arch = self.architecture()
        filename = f"{name}_{item['version']}_linux_{arch}.zip"
        manifest = self.fetch(item["checksums_url"], limit=100_000)
        assets.verify_sha256(manifest, item["checksums_sha256"])
        expected = assets.checksum_for(manifest, filename)
        payload = self.fetch(item["url"].rsplit("/", 1)[0] + "/" + filename)
        assets.verify_sha256(payload, expected)
        target, _ = tool_target(self.home, name)
        self.safe_managed_path(target)
        assets.extract_zip(payload, target.parent, binary=name)
        os.chmod(target, 0o755)
        self.write_wrapper(name)

    def install_source(self, name):
        assets = _portable_assets()
        folder = self.version_folder(name)
        self.safe_managed_path(folder)
        if os.path.lexists(folder):
            raise SetupError(f"Existing environment was preserved: {folder}.")
        if name in assets.SOURCE_ARCHIVES:
            item = assets.SOURCE_ARCHIVES[name]
            payload = self.fetch(item["url"])
            assets.verify_sha256(payload, item["sha256"])
            assets.extract_zip(payload, folder / "source", prefix=item["prefix"])
        else:
            folder.mkdir(parents=True, exist_ok=False)
        if name == "nikto":
            self.write_wrapper(name)
            return
        venv = folder / "venv"
        python = venv / "bin/python"
        self.command([sys.executable, "-I", "-m", "venv", "--copies", str(venv)])
        self.check_managed_tree(venv)
        pip = [str(python), "-I", "-m", "pip", "--isolated", "install", "--disable-pip-version-check",
               "--no-input", "--index-url", "https://pypi.org/simple"]
        self.command([*pip, "--only-binary=:all:", "--no-deps", *assets.BUILD_PINS])
        if name in {"dnsrecon", "theHarvester"}:
            # Fixed source; upstream requirements include correct OS markers.
            self.command([*pip, "--no-build-isolation", str(folder / "source")])
        elif name == "arjun":
            self.command([*pip, "--no-deps", "--no-build-isolation", *ARJUN_PINS[1:]])
            self.command([*pip, "--no-deps", "--no-build-isolation", assets.ARJUN_SOURCE])
        else:
            self.command([*pip, "--no-deps", "--no-build-isolation", *PHOTON_PINS])
        self.command([str(python), "-I", "-m", "pip", "--isolated", "check"])
        self.write_wrapper(name)

    def install(self, update_templates=False):
        initial = self.health()
        needed = [name for name in TOOLS if initial.get(name, {}).get("status") != "ready"]
        missing_templates = nuclei_templates_incomplete(initial)
        install_needed = [name for name in needed if not (name == "nuclei" and missing_templates)]
        for name in TOOLS:
            status = ("TEMPLATE CHECK NEEDS REPAIR — refresh official templates only" if name == "nuclei" and missing_templates else
                      "needs setup" if name in needed else "SKIP — existing tool passed local checks")
            self.output(f"{name}: {status}")
        if not install_needed and not update_templates and not missing_templates:
            self.output("All 9 tools and local Nuclei template data passed checks. No install or scan was needed.")
            return 0
        self.preflight(install_needed, initial)
        self.prerequisites(install_needed)
        if any(name != "nmap" for name in install_needed):
            self.prepare()
        failures, new_nuclei = [], False
        assets = _portable_assets()
        for name in install_needed:
            if name == "nmap":
                continue
            try:
                if name in GO_MODULES:
                    self.install_release(name)
                    new_nuclei |= name == "nuclei"
                else:
                    self.install_source(name)
            except (SetupError, assets.SetupError, OSError) as exc:
                failures.append(name)
                self.output(f"SETUP ERROR — {name}: {exc}")
        final = self.health()
        if new_nuclei or update_templates or missing_templates:
            try:
                self.update_templates(final)
                final = self.health()
            except SetupError as exc:
                failures.append("nuclei templates")
                self.output(f"TEMPLATE ERROR — {exc}")
        self.output("\nFinal local checks (help/identity only; no target scan):")
        not_ready = []
        for name in TOOLS:
            item = final.get(name, {})
            self.output(f"  {name}: {item.get('status', 'unknown')} — {item.get('detail', '')}")
            if item.get("status") != "ready":
                not_ready.append(name)
        if failures or not_ready:
            self.output("Setup is incomplete. Existing files were preserved; inspect errors before retrying.")
            return 1
        self.output("All 9 tools passed local checks; the local Nuclei template version was also found. Refresh Check installed tools. No scan was run.")
        return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="Show read-only plan (default); no commands, network or writes")
    mode.add_argument("--install", action="store_true", help="Install missing backend tools together on supported Linux distributions")
    parser.add_argument("--update-templates", action="store_true", help="With --install, also refresh templates of an existing ready Nuclei")
    parser.add_argument("--pause", action="store_true", help="Keep the interactive terminal open until Enter")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data", help="Local dashboard data directory for the setup lock (trusted launcher configuration)")
    args = parser.parse_args(argv)
    if args.update_templates and not args.install:
        parser.error("--update-templates requires --install")
    lock = None
    try:
        if not args.install:
            show_plan()
            return 0
        family = validate_platform()
        print("Echo Recon backend setup. Only the fixed official sources below are used. No scan is run.", flush=True)
        show_plan()
        data = args.data_dir.expanduser().resolve()
        data.mkdir(parents=True, exist_ok=True, mode=0o700)
        if (data / "setup-tools.lock").is_symlink():
            raise SetupError("The setup lock is a symlink. Inspect the data directory before retrying.")
        try:
            lock = InstanceLock(data / "setup-tools.lock").acquire()
        except RuntimeError as exc:
            raise SetupError("Another backend setup is already running. Finish/close that terminal before retrying.") from exc
        installer = Installer() if family in {None, "kali"} else PortableInstaller(family)
        return installer.install(update_templates=args.update_templates)
    except (SetupError, OSError) as exc:
        print(f"\nSetup stopped: {exc}", file=sys.stderr, flush=True)
        return 1
    except KeyboardInterrupt:
        print("\nSetup interrupted. Existing tools were not removed; retry to check current state.", file=sys.stderr, flush=True)
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
