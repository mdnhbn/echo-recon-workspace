#!/usr/bin/env python3
"""Fixed-source, normal-user macOS backend setup.

Default/--plan is read-only. --install uses the native Homebrew installation
for Nmap/Nikto and verified official Darwin releases or isolated Python
environments for the other seven tools. No scan target is accepted.
"""
import argparse
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

sys.dont_write_bytecode = True

from echo_recon.locking import InstanceLock
from echo_recon.tools import TOOLS, nuclei_templates_incomplete
from setup_tools import (GO_MODULES, Installer, PortableInstaller, ROOT, SetupError,
                         _portable_assets, check_wrapper, managed_root, tool_target)

BREW_TOOLS = ("nmap", "nikto")


def architecture():
    value = {"x86_64": "amd64", "arm64": "arm64"}.get(platform.machine().lower())
    if value is None:
        raise SetupError("macOS setup supports native Intel x86_64 and Apple Silicon arm64 only.")
    return value


def homebrew_prefix():
    return Path("/opt/homebrew" if architecture() == "arm64" else "/usr/local")


def local_path(home):
    prefix = homebrew_prefix()
    return os.pathsep.join((str(Path(home) / ".local/bin"), str(Path(home) / "go/bin"),
                            str(prefix / "bin"), str(prefix / "sbin"),
                            os.environ.get("PATH", "")))


def validate_platform():
    if sys.platform != "darwin":
        raise SetupError("Use this installer only in native macOS; Windows/Linux have separate installers.")
    if os.geteuid() == 0:
        raise SetupError("Run as your normal macOS user, without sudo.")
    if tuple(sys.version_info[:2]) < (3, 12):
        raise SetupError("macOS backend setup requires Python >=3.12. Install Homebrew python@3.12 and recreate the dashboard venv.")
    arch = architecture()
    if arch == "amd64":
        # Apple documents this read-only kernel flag for detecting Rosetta.
        # An absent flag on an Intel Mac exits nonzero with no value.
        try:
            result = subprocess.run(["/usr/sbin/sysctl", "-in", "sysctl.proc_translated"],
                                    check=False, shell=False, stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL, text=True, timeout=10)
        except OSError as exc:
            raise SetupError("Cannot verify the native Mac architecture. Use native Terminal and Python, then retry.") from exc
        except subprocess.TimeoutExpired as exc:
            raise SetupError("The local architecture check did not finish. Retry from native macOS Terminal.") from exc
        if result.stdout.strip() == "1":
            raise SetupError("Rosetta/x86_64 Python on Apple Silicon is not an automatic setup target. Use native arm64 Terminal, /opt/homebrew and a new native Python venv.")
        if result.stdout.strip() not in {"", "0"}:
            raise SetupError("Unrecognized Mac architecture result; no tools were installed.")
    return arch


def show_plan(home=None, output=print):
    """Read local paths only: never probe, download, execute or write."""
    home = Path(home or Path.home())
    output("Echo Recon backend setup — READ-ONLY PLAN (native macOS)")
    output("No command, download, installation or scan is run in this mode.")
    output("Requires Python >=3.12 and a working native Homebrew installation for missing Nmap/Nikto.")
    output("Homebrew is installed manually from https://brew.sh; no remote shell installer is run here.")
    output("Apple Silicon uses /opt/homebrew; native Intel uses /usr/local. Rosetta setup is rejected.")
    output("Homebrew currently gives Intel legacy/Tier 3 support; older macOS/formula builds may need manual repair.")
    try:
        path = local_path(home)
    except SetupError:
        path = os.environ.get("PATH", "")
    for name in TOOLS:
        output(f"  {name}: {shutil.which(name, path=path) or 'not on PATH'} (not probed in plan mode)")
    output("Missing formula tools: brew install --formula homebrew/core/nmap homebrew/core/nikto (only needed names).")
    output("Existing tools that pass identity checks are skipped; no brew update/upgrade or sudo is run.")
    output(f"User-local version folders: {managed_root(home)}; launchers: {home / '.local/bin'}")
    output("subfinder/httpx/nuclei: pinned official Darwin amd64/arm64 ZIPs; pinned checksum manifests and selected asset SHA256 are verified before extraction.")
    output("DNSRecon/theHarvester/Photon/Arjun: pinned official source/version, separate Python venvs, upstream requirements from official PyPI.")
    output("New Nuclei engines fetch official templates; --update-templates also refreshes a ready engine.")
    output("Current official templates and resolved Python dependencies are not one frozen cross-platform snapshot.")
    output("Run: python3 setup_tools_macos.py --install")


def download(url, limit=200 * 1024 * 1024):
    assets = _portable_assets()
    allowed = {item["url"] for name, item in assets.SOURCE_ARCHIVES.items() if name != "nikto"}
    for name, item in assets.WINDOWS_RELEASES.items():
        allowed.add(item["checksums_url"])
        prefix = item["url"].rsplit("/", 1)[0]
        for arch in ("amd64", "arm64"):
            allowed.add(f"{prefix}/{name}_{item['version']}_macOS_{arch}.zip")
    if url not in allowed:
        raise SetupError("Download URL is outside the pinned official macOS sources.")
    assets._check_https_host(url)
    opener = urllib.request.build_opener(assets.FixedSourceRedirect())
    request = urllib.request.Request(url, headers={"User-Agent": "Echo-Recon-macOS-setup/1"})
    try:
        with opener.open(request, timeout=60) as response:
            assets._check_https_host(response.geturl())
            blocks, total = [], 0
            while True:
                block = response.read(min(1024 * 1024, limit + 1 - total))
                if not block:
                    return b"".join(blocks)
                total += len(block)
                if total > limit:
                    raise SetupError("Official macOS download exceeds the reviewed size limit.")
                blocks.append(block)
    except (OSError, urllib.error.URLError) as exc:
        raise SetupError(f"Official macOS download failed: {exc}") from exc


class MacInstaller(PortableInstaller):
    """Share POSIX managed-storage and source installers without Linux commands."""

    def __init__(self, home=None, run=None, check_tools=None, output=print, fetch=None):
        Installer.__init__(self, home=Path(home or Path.home()).expanduser().resolve(),
                           run=run, check_tools=check_tools, output=output)
        self.fetch = fetch or download
        self.env["PATH"] = local_path(self.home)
        # Keep browser/inherited environment from redirecting formula sources,
        # build flags or package-manager wrappers. Brew verifies its own bottles.
        for key in list(self.env):
            if key.startswith("HOMEBREW_"):
                self.env.pop(key, None)
        self.env.update(HOMEBREW_NO_AUTO_UPDATE="1", HOMEBREW_NO_ANALYTICS="1",
                        HOMEBREW_NO_ENV_HINTS="1")

    def architecture(self):
        return architecture()

    def prerequisites(self, needed):
        if any(name not in GO_MODULES and name not in BREW_TOOLS for name in needed):
            if tuple(sys.version_info[:2]) < (3, 12):
                raise SetupError("Pinned macOS Python tools require Python >=3.12; recreate the dashboard venv with Homebrew python@3.12.")
        packages = [f"homebrew/core/{name}" for name in BREW_TOOLS if name in needed]
        if not packages:
            return
        brew = homebrew_prefix() / "bin/brew"
        if not brew.is_file():
            raise SetupError(f"Native Homebrew is missing at {brew}. Install Homebrew from https://brew.sh, then rerun setup; no bootstrap script was downloaded.")
        self.output("Only these missing Homebrew formulae are requested: " + ", ".join(packages))
        self.command([str(brew), "install", "--formula", *packages])

    def preflight(self, needed, initial):
        self.architecture()
        prefix = homebrew_prefix()
        for name in needed:
            if name in BREW_TOOLS:
                current = initial.get(name, {}).get("path")
                expected = prefix / "bin" / name
                if current and Path(current).resolve() != expected.resolve():
                    raise SetupError(f"Unverified {name} command shadows the native Homebrew command: {current}. Inspect PATH; no files were replaced.")
            else:
                check_wrapper(self.home, name)
                folder = self.version_folder(name)
                self.safe_managed_path(folder)
                if os.path.lexists(folder):
                    raise SetupError(f"Existing incomplete/unverified tool folder preserved: {folder}. Inspect/relocate it before retrying.")
        if any(name not in BREW_TOOLS for name in needed):
            self.check_storage()

    def install_release(self, name):
        assets = _portable_assets()
        item = assets.WINDOWS_RELEASES[name]
        if GO_MODULES[name].rsplit("@v", 1)[1] != item["version"]:
            raise SetupError("Shared release pins differ; update both reviewed versions before setup.")
        filename = f"{name}_{item['version']}_macOS_{self.architecture()}.zip"
        manifest = self.fetch(item["checksums_url"], limit=100_000)
        assets.verify_sha256(manifest, item["checksums_sha256"])
        digest = assets.checksum_for(manifest, filename)
        payload = self.fetch(item["url"].rsplit("/", 1)[0] + "/" + filename)
        assets.verify_sha256(payload, digest)
        target, _ = tool_target(self.home, name)
        self.safe_managed_path(target)
        assets.extract_zip(payload, target.parent, binary=name)
        os.chmod(target, 0o755)
        self.write_wrapper(name)

    def update_templates(self, health):
        item = health.get("nuclei", {})
        path = item.get("path") or shutil.which("nuclei", path=self.env["PATH"])
        if item.get("engine_status", item.get("status")) != "ready" or not path:
            raise SetupError("Nuclei did not pass its local identity check; templates were not updated.")
        self.output("Downloading current official Nuclei templates only; this does not scan a target or update the engine.")
        # In upstream v3.11.1, -duc calls Config.DisableUpdateCheck(), which
        # gates the template installer too. Combining it with the explicit
        # -update-templates request exits successfully without installing any
        # missing template data. Keep -duc in read-only health/scan commands,
        # but omit it from this explicit, target-free template setup action.
        self.command([path, "-update-templates"])

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
            self.output("All 9 tools and local Nuclei templates passed checks. No installation or scan was needed.")
            return 0
        self.preflight(install_needed, initial)
        self.prerequisites(install_needed)
        if any(name not in BREW_TOOLS for name in install_needed):
            self.prepare()
        failures, new_nuclei = [], False
        assets = _portable_assets()
        for name in install_needed:
            if name in BREW_TOOLS:
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
            self.output("Setup is incomplete. Review the errors; existing tools and partial environments were preserved.")
            return 1
        self.output("All 9 tools and the local Nuclei template version passed checks. Refresh Check installed tools. No scan was run.")
        return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="Show read-only plan (default)")
    mode.add_argument("--install", action="store_true", help="Set up missing native macOS backends")
    parser.add_argument("--update-templates", action="store_true", help="With --install, refresh existing Nuclei templates too")
    parser.add_argument("--pause", action="store_true", help="Wait for Enter before the setup terminal closes")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data", help="Trusted dashboard data directory for the setup lock")
    args = parser.parse_args(argv)
    if args.update_templates and not args.install:
        parser.error("--update-templates requires --install")
    lock = None
    try:
        if not args.install:
            show_plan()
            return 0
        validate_platform()
        show_plan()
        data = args.data_dir.expanduser().resolve()
        data.mkdir(parents=True, exist_ok=True, mode=0o700)
        if (data / "setup-tools.lock").is_symlink():
            raise SetupError("The setup lock is redirected. Inspect the data directory before retrying.")
        try:
            lock = InstanceLock(data / "setup-tools.lock").acquire()
        except RuntimeError as exc:
            raise SetupError("Another backend setup is already running. Finish it before retrying.") from exc
        return MacInstaller(output=lambda line: print(line, flush=True)).install(update_templates=args.update_templates)
    except (SetupError, _portable_assets().SetupError, OSError) as exc:
        print(f"\nSetup stopped: {exc}", file=sys.stderr, flush=True)
        return 1
    except KeyboardInterrupt:
        print("\nSetup interrupted. Existing tools were preserved; retry after reviewing partial environments.", file=sys.stderr, flush=True)
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
