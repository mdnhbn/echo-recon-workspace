# macOS-এ install ও update করার নিয়ম

[বাংলা README](../README.bn.md) · [English macOS guide](MACOS.md) · [Tool setup](TOOLS.md) · [ব্যবহারবিধি](USAGE.bn.md)

Echo Recon আপনার Mac-এ একটি local Python server চালায়। Interface খুলবে Mac-এর browser-এ: **http://127.0.0.1:8001**। ব্যবহার করার সময় Terminal খোলা রাখতে হবে। এই পদ্ধতিতে source code থেকে চালানো হয়; signed `.app` bundle তৈরি হয় না।

## ১. আগে যা লাগবে

নিজের সাধারণ macOS user account, internet এবং পুরো backend setup-এর জন্য **Python 3.12 বা নতুন** লাগবে। Terminal, Python ও Homebrew একই native architecture-এর রাখুন:

| Mac | Architecture | Homebrew-এর স্থান |
|---|---|---|
| Apple Silicon | `arm64` | `/opt/homebrew` |
| Intel | `x86_64` | `/usr/local` |

দুই architecture-এর setup path আছে। তবে সব পুরোনো macOS-এ সব Homebrew package পাওয়া যাবে—এমন নিশ্চয়তা নেই। [Homebrew-এর বর্তমান requirements](https://docs.brew.sh/Installation) ও [support tiers](https://docs.brew.sh/Support-Tiers) দেখুন। Intel macOS এখন legacy Tier 3। Apple Silicon Mac-এ Rosetta mode-এর বদলে native Terminal ব্যবহার করুন।

Homebrew না থাকলে [brew.sh-এর official নির্দেশনা](https://brew.sh/) মেনে নিজে install করুন। সেখানে **Next steps** এবং প্রয়োজন হলে Command Line Tools-এর ধাপ শেষ করুন। Echo Recon নিজে Homebrew-এর remote shell installer চালায় না বা system security settings বদলায় না।

Terminal-এ `brew --version` কাজ করলে প্রথমে দিন:

```bash
brew install python@3.12 git
git --version
```

Setup script উপযুক্ত native Homebrew Python এবং PATH-এ থাকা উপযুক্ত Python খুঁজবে। অন্য Python distribution ব্যবহার করলে সেটিতে `venv` এবং সঠিক native architecture থাকতে হবে।

## ২. Project নামিয়ে install করুন

Terminal খুলে নিচের প্রতিটি line একটির পর একটি দিন:

```bash
mkdir -p ~/Tools
cd ~/Tools
git clone https://github.com/mdnhbn/echo-recon-workspace.git
cd echo-recon-workspace
bash install.sh
bash run.sh
```

- `mkdir` folder বানায়, `cd` সেই folder-এ ঢোকে।
- `git clone` GitHub থেকে project নামায়।
- `install.sh` dashboard-এর আলাদা `.venv` বানায়, dependency-এর hash যাচাই করে এবং macOS backend installer চালায়।
- `run.sh` dashboard চালায়। এই command-গুলোর আগে `sudo` দেবেন না।

Installer নয়টি tool দেখে; আগে থেকে local identity check পাস করা tool আবার install করে না। Missing Nmap ও Nikto official [Homebrew Nmap](https://formulae.brew.sh/formula/nmap) ও [Nikto](https://formulae.brew.sh/formula/nikto) formula দিয়ে বসে। Subfinder, ProjectDiscovery HTTPX ও Nuclei-র নির্দিষ্ট official Darwin release checksum যাচাই করে নামায়। DNSRecon, theHarvester, Photon ও Arjun-কে নির্দিষ্ট upstream version/snapshot থেকে আলাদা user-owned Python environment-এ রাখে। এই macOS পদ্ধতিতে Go SDK লাগে না।

Managed tool-এর folder হলো `~/.local/share/echo-recon/tooling`; launcher থাকে `~/.local/bin`-এ। আগে থেকে কাজ করা system tool নিজের জায়গায় থাকে। Git clone দিয়ে চালালে report/history project-এর private `data/` folder-এ থাকে, যদি আলাদা data directory নিজে না বাছেন।

Browser খুললে **Check installed tools** দিয়ে readiness দেখুন। **Setup all tools** একই macOS installer আবার চালায় এবং worker log dashboard-এ দেখায়। Install করলেই scan শুরু হয় না, API account/key-ও তৈরি হয় না। Terminal খোলা রাখুন; app বন্ধ করতে সেই Terminal-এ **Ctrl+C** চাপুন।

## ৩. Setup plan দেখা বা আবার চেষ্টা করা

Project folder-এর Terminal-এ:

```bash
.venv/bin/python setup_tools_macos.py --plan
.venv/bin/python setup_tools_macos.py --install
.venv/bin/python doctor.py
```

Default/`--plan` শুধু source ও path দেখায়; tool চালায় না, download বা file লেখা করে না। `--install` আসল setup করে। অচেনা folder, conflicting launcher বা অসম্পূর্ণ environment পেলে সেটি রেখে error দেখায়। Error পড়ে নিজের পুরোনো file দেখুন; Python venv অন্য folder বা machine-এ সরাবেন না।

ইচ্ছা করে Nuclei-র official templates refresh করতে:

```bash
.venv/bin/python setup_tools_macos.py --install --update-templates
```

Templates upstream-এ বদলায়। Local version check পাস মানে প্রতিটি template, provider বা scan পুরোপুরি যাচাই হয়েছে—এমন নয়।

শুধু dashboard লাগলে:

```bash
bash install.sh --dashboard-only
bash run.sh --no-tool-setup
```

Browser নিজে খুলতে না চাইলে `run.sh`-এর শেষে `--no-browser` যোগ করুন, তারপর দেখানো local ঠিকানা নিজে খুলুন। এই macOS setup script-গুলো dashboard-only mode-এও native Python 3.12+ ব্যবহার করে।

## ৪. পরে নতুন version আনা

আগে চলমান server-এর Terminal-এ Ctrl+C দিন। Private `data/` backup রাখুন। এরপর project folder-এর Terminal-এ:

```bash
git status --short
git pull --ff-only
bash install.sh
bash run.sh
```

`git pull` Echo Recon-এর নতুন code আনে। `install.sh` dashboard dependency ও missing backend মিলিয়ে নেয়; check পাস করা পুরোনো tool রেখে দেয়। নিজের code পরিবর্তন থাকলে Git update থামাতে পারে—সেই পরিবর্তন দেখুন, force reset দেবেন না।

Native macOS install এই project-এর Kali APT feed ব্যবহার করে না। Mac-এ `sudo apt upgrade` দিয়ে Echo Recon update হবে না। `brew upgrade` Homebrew software update করে; cloned Echo Recon-এর code আনে না। ZIP ব্যবহার করলে নতুন ZIP নতুন folder-এ extract করুন; পুরোনো server বন্ধ করে নিজের report/history পরে সচেতনভাবে copy করুন।

## ৫. সমস্যা হলে

| কী দেখাচ্ছে | কী করবেন |
|---|---|
| Homebrew বা Command Line Tools নেই | Official prerequisite setup শেষ করে Terminal আবার খুলুন, তারপর retry করুন। |
| Architecture/Homebrew prefix মিলছে না | Apple Silicon বা Intel-এর native Terminal, Python ও Homebrew একসঙ্গে ব্যবহার করুন; Rosetta আর native environment মেশাবেন না। |
| Python পুরোনো | উপযুক্ত Python বসান। আগের `.venv` অন্য Python version-এর হলে fresh project folder ব্যবহার করুন। |
| Tool `unverified` বা launcher conflict | Tool health/`doctor.py`-তে path পড়ুন; পুরোনো install দেখে তারপর নিজে সিদ্ধান্ত নিন। |
| Browser খুলছে না | Server চলতে দিন; একই Mac-এ `http://127.0.0.1:8001` খুলুন। |
| Port 8001 ব্যস্ত | আগের Echo Recon process বন্ধ করে তারপর নতুন copy চালান। |

Local help/identity check বা automated fixture দিয়ে প্রতিটি macOS version-এ fresh install ও live provider-এর কাজ নিশ্চিত করা হয় না। শুধু নিজের বা স্পষ্ট অনুমতি থাকা host পরীক্ষা করুন; [SECURITY.md](../SECURITY.md) দেখুন।
