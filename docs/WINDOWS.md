# Windows setup / Windows-এ চালানোর নিয়ম

## Choose the right mode / কোন পদ্ধতি ব্যবহার করবেন

| Mode | Supported features | How to run |
|---|---|---|
| Kali Linux / Kali VirtualBox | Dashboard and all eight adapters, with separately installed tools | `bash install.sh`, `bash run.sh` |
| Windows + Kali WSL2 | The same Linux workflow, viewed from a Windows browser | Install inside Kali WSL2; start there or use `run-wsl.ps1` |
| Native Windows + Python | Dashboard, saved history, HTML/JSON reports, development tests | `install.ps1`, `run.ps1` |

**Native Windows live assessments are deliberately disabled.** Installing Python does not turn Linux scanner wrappers into Windows tools. Use Kali WSL2 for the full scanner workflow. The application explains this and rejects unsupported native live requests server-side.

সরাসরি Windows-এ dashboard, সংরক্ষিত history, report ও development করা যাবে। আটটি scanner-এর পুরো কাজের জন্য Windows-এর মধ্যে **Kali WSL2** ব্যবহার করুন। দুটি mode-এর project folder, `.venv` ও `data` আলাদা রাখুন। Demo বা বানানো scan result তৈরি হয় না।

## A. Full workflow with Kali WSL2 (recommended)

Follow [Microsoft's official WSL installation guide](https://learn.microsoft.com/windows/wsl/install). Supported commands below require a current Windows 11 or supported Windows 10 with WSL support. Enabling WSL may require administrator permission and a restart.

Open PowerShell as administrator for the **one-time WSL installation**:

```powershell
wsl --list --online
wsl --install -d kali-linux
```

Use the distribution name shown in your online list. Restart if requested, open Kali, and create your normal Linux username/password privately. Do not post the password in an issue.

Then open a normal Windows Terminal / PowerShell:

```powershell
wsl -d kali-linux
```

You are now **inside Kali Linux**. The next commands are Bash commands, not PowerShell:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv
mkdir -p ~/Tools/02-Custom
cd ~/Tools/02-Custom
git clone https://github.com/mdnhbn/echo-recon-workspace.git
cd echo-recon-workspace
bash install.sh
bash run.sh
```

Leave that terminal open. In Windows Edge/Firefox/Chrome, visit **http://127.0.0.1:8001**. Microsoft documents Windows-to-WSL localhost access in its [WSL networking guide](https://learn.microsoft.com/windows/wsl/networking). If localhost forwarding is restricted on your machine, troubleshoot WSL networking; do not change this dashboard to bind `0.0.0.0`, open a firewall port or disable its local-client checks as a shortcut.

Use **Check installed tools** and **Download / setup tools** in the dashboard, then follow [TOOLS.md](TOOLS.md) for official sources and manual setup. Install/check the eight tools **inside the same Kali WSL distribution**. Tools installed in a VirtualBox VM or native Windows are not automatically installed in WSL. After setup, recheck tools; restart the server if PATH changed. Keep the repository in Linux HOME, not `/mnt/c`, for this workflow. Do not reuse the Windows virtual environment or database.

পরেরবার Kali terminal-এ project folder থেকে `bash run.sh` দিলেই হবে। Windows-এ repo-এর আরেকটি কপি থাকলে তার PowerShell থেকে `run-wsl.ps1` দিয়েও WSL-এর নির্দিষ্ট Linux folder-এর project চালানো যায়:

```powershell
.\run-wsl.ps1
# Only if your installed distro has another name:
.\run-wsl.ps1 -Distro kali-linux
```

The launcher starts an already installed Linux copy at `~/Tools/02-Custom/echo-recon-workspace`. It does not install WSL, change a default distro, request administrator rights or copy environments between operating systems. Stop with Ctrl+C in its terminal. A WSL distro with a different name can be selected explicitly.

## B. Native Windows dashboard and development

Install a current Python **3.11+** from [python.org](https://www.python.org/downloads/windows/) and Git from [git-scm.com](https://git-scm.com/downloads/win), or download the repository ZIP and extract into a **new private user-owned folder**. Do not run as administrator. Open PowerShell in that folder.

```powershell
git clone https://github.com/mdnhbn/echo-recon-workspace.git
cd echo-recon-workspace
.\install.ps1
.\run.ps1
```

If multiple Python installations exist, choose one explicitly:

```powershell
.\install.ps1 -PythonExe 'C:\Path\To\python.exe'
```

The default browser opens **http://127.0.0.1:8001** after the local server is ready. If it does not open, enter that address yourself. You can inspect the dashboard, saved history and report exports, and test contributions. A new installation has no sample scan history. **Download / setup tools** shows official sources and a guide; it does not install scanners or enable native Windows assessments. Stop the server with Ctrl+C. The application uses a Windows file lock so another instance cannot alter recovery state for the same data directory. Use `.\run.ps1 -NoBrowser` to disable browser opening; for a WSL launch use `.\run-wsl.ps1 -NoBrowser`. Headless WSL normally needs you to open the address in Windows yourself.

### If PowerShell blocks a script

Read the script first and follow your organization's policy. You do not need to weaken the machine's execution policy: use Python directly instead:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes --only-binary=:all: -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

If `py` is unavailable, use the full path to your installed Python. Do not use `sudo`, Linux `.venv/bin/python` or Git Bash to activate a Windows environment. No activation is needed when using the full `.venv\Scripts\python.exe` path.

### Tests on Windows

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

CI checks both Linux and Windows. OS-specific process tests are skipped on the other operating system. Tests use fixtures and local child processes in temporary directories; they do not seed production history or contact public targets. Full WSL provisioning/adapter network operation is a separate integration check; Windows CI does not install Kali WSL or certify scanner behavior there.

## Storage, permissions and updates

On Linux, private directory/file modes are applied. On Windows, `chmod` does **not** create equivalent private NTFS permissions. Use your private Windows user profile, retain suitable inherited NTFS permissions, and avoid shared/synced folders for `data/`. Reports may contain sensitive evidence.

Windows-এ user-এর private folder ব্যবহার করুন। Linux-এর permission ও Windows-এর ACL এক নয়। `data/`, report, secret বা `.venv` GitHub-এ দেবেন না।

Stop before updating. In a Windows copy:

```powershell
git status
git pull --ff-only
.\install.ps1
.\run.ps1
```

Inside a WSL copy, use `bash install.sh` and `bash run.sh` instead. Both modes use port 8001, so do not run both at the same time on Windows if localhost ports conflict. Keep environments and histories separate.

### Remove legacy demo history / পুরোনো demo history সরানো

Version 6.2 no longer generates demos. To remove saved demos from an earlier native Windows installation, stop its dashboard with **Ctrl+C**, open PowerShell in that same repository and run:

```powershell
.\.venv\Scripts\python.exe maintenance.py remove-demo
```

For a Kali WSL copy, stop that copy and use its Linux environment instead:

```bash
.venv/bin/python maintenance.py remove-demo
```

The offline command removes only records explicitly marked as legacy demos; real assessment history is retained. It does not scan targets or remove scanner installations. Do not delete the whole `data/` directory, run cleanup against an active server, or copy one environment's database into another.

আগে যে mode-এর demo মুছবেন, সেই dashboard বন্ধ করুন। একই repository-র সঠিক Python environment দিয়ে command দিন। শুধু demo হিসেবে চিহ্নিত record সরবে; বাস্তব history রাখা হবে।
