#!/usr/bin/env python3
"""Interactive, fixed-source backend setup for a normal Kali user.

Default/--plan only reads local paths: no commands, network requests or writes.
--install executes a conditional plan, then verifies all eight tool adapters.
No scan target is accepted and no assessment is started by this program.
"""
import argparse
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

# Keep even project-module bytecode caches out of the read-only CLI plan.
sys.dont_write_bytecode = True

from echo_recon.locking import InstanceLock
from echo_recon.tools import TOOLS, diagnostics


ROOT = Path(__file__).resolve().parent
GO_MINIMUM = (1, 26)
GO_MODULES = {
    "subfinder": "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@v2.17.0",
    "httpx": "github.com/projectdiscovery/httpx/cmd/httpx@v1.12.0",
    "nuclei": "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@v3.11.1",
}
APT_TOOLS = {"dnsrecon": "dnsrecon", "nmap": "nmap", "theHarvester": "theharvester"}
PHOTON_URL = "https://github.com/s0md3v/Photon.git"
PHOTON_COMMIT = "c8d2566841d69a268b244609921143d84b72b0c6"
ARJUN_VERSION = "2.2.7"
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
    if name == "arjun":
        return managed_root(home) / f"arjun-{ARJUN_VERSION}" / "venv/bin/arjun", ()
    if name == "photon":
        folder = managed_root(home) / f"photon-{PHOTON_COMMIT}"
        return folder / "venv/bin/python", (str(folder / "source/photon.py"),)
    raise SetupError(f"No user-local installer for {name}.")


def wrapper_text(home, name):
    target, extra = tool_target(home, name)
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
    output("Echo Recon backend setup — READ-ONLY PLAN (Kali Linux / Kali WSL2)")
    output("No command, download, installation or scan is run in this mode.")
    output("With --install: check local help/version identity first; skip every ready tool.")
    output("Existing system tools stay in place. Sudo is requested only in the interactive terminal for apt.")
    for name in TOOLS:
        path = shutil.which(name, path=local_path(home))
        output(f"  {name}: {path or 'not on PATH'} (not probed in plan mode)")
    output("Conditional official apt packages: dnsrecon, nmap, theharvester; missing prerequisites only:")
    output("  python3-venv, git, ca-certificates, golang-go. Go >=1.26 is required; no Go bootstrap scripts.")
    output("  sudo /usr/bin/apt-get update")
    output("  sudo /usr/bin/apt-get install --yes --no-install-recommends <needed fixed packages above>")
    output(f"User-local environments: {managed_root(home)}")
    for name, module in GO_MODULES.items():
        output(f"  {name}: go install -v {module} (isolated GOBIN, verified public Go module checksums)")
    output("  arjun: isolated venv; pinned PyPI runtime: " + ", ".join(ARJUN_PINS))
    output(f"  photon: {PHOTON_URL} at exact commit {PHOTON_COMMIT}; isolated venv")
    output("    Pinned PyPI runtime: " + ", ".join(PHOTON_PINS))
    output("  Python build helpers: " + ", ".join(BUILD_PINS))
    output("Nuclei: newly installed engines download official templates with -update-templates -duc.")
    output("Existing ready Nuclei/templates are untouched unless --update-templates is explicitly added.")
    output("Template refresh downloads current official templates (not a pinned template snapshot); no target is scanned.")
    output("Launchers are added in ~/.local/bin only when absent or exactly managed by this installer.")
    output("Run: python3 setup_tools.py --install   (terminal; may take several minutes and require free disk/RAM)")


def validate_platform():
    if sys.platform != "linux":
        raise SetupError("Backend installation requires Kali Linux. On Windows, open Kali WSL2; see docs/WINDOWS.md.")
    if os.geteuid() == 0:
        raise SetupError("Run as your normal Kali user, not root or sudo python. Apt will ask for sudo separately.")
    try:
        values = {}
        for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep:
                values[key] = value.strip().strip('"')
    except OSError as exc:
        raise SetupError("Cannot identify this Linux distribution; automatic setup supports Kali only.") from exc
    if values.get("ID") != "kali":
        raise SetupError("Automatic backend setup supports Kali only. See docs/TOOLS.md for official manual sources.")


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
        if item.get("status") != "ready" or not path:
            raise SetupError("Nuclei did not pass its local identity check; templates were not updated.")
        self.output("Downloading current official Nuclei templates only; this does not scan a target.")
        self.command([path, "-update-templates", "-duc"])

    def install(self, update_templates=False):
        initial = self.health()
        needed = [name for name in TOOLS if initial.get(name, {}).get("status") != "ready"]
        for name in TOOLS:
            self.output(f"{name}: " + ("SKIP — existing tool passed local checks" if name not in needed else "needs setup/repair"))
        for name in needed:
            if name not in APT_TOOLS:
                check_wrapper(self.home, name)
            else:
                current = initial.get(name, {}).get("path")
                expected = Path("/usr/bin") / name
                if current and Path(current).resolve() != expected.resolve():
                    raise SetupError(f"Unverified command shadows Kali's {name}: {current}. It was not replaced. Inspect your PATH/launcher before retrying; the official apt command is {expected}.")
        if not needed and not update_templates:
            self.output("All 8 tools passed local identity/help checks. No downloads or installations were needed. No scan was run.")
            return 0
        custom_needed = any(name not in APT_TOOLS for name in needed)
        if custom_needed:
            self.check_storage()
            if self.base.exists():
                self.check_managed_tree(self.base)
        go = self.prerequisites(needed)
        if custom_needed:
            self.prepare()
        failures = []
        new_nuclei = False
        for name in needed:
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
        if new_nuclei or update_templates:
            try:
                self.update_templates(final)
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
        self.output("All 8 tools passed local checks. Restart the dashboard via bash run.sh and refresh Check installed tools.")
        self.output("Tool readiness does not guarantee API credentials, upstream sources, templates or every assessment will succeed.")
        return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="Show read-only plan (default); no commands, network or writes")
    mode.add_argument("--install", action="store_true", help="Install missing backend tools interactively on Kali")
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
        validate_platform()
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
        return Installer().install(update_templates=args.update_templates)
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
