# Echo Recon 6.7.1 — বাংলা নির্দেশনা

এটি নিজের কম্পিউটারে চালানোর dashboard। নয়টি আলাদা tool-এর কাজ নির্দিষ্ট ক্রমে চালায়, প্রমাণ রাখে এবং HTML/JSON report তৈরি করে। মূল project [Ahammed-এর Echo Recon / Auto-Recon](https://github.com/ahammed18122002-art/auto-rec); mdnhbn সহযোগিতায় এই সংস্করণ উন্নত হয়েছে।

## 6.7.1-এ যা বদলেছে

- Stop দেওয়ার পরে child process থেকে যাওয়া, নতুন user data folder-এ প্রথমবার চালু হওয়া ও Linux/Windows-এ Nuclei templates আপডেটের সমস্যা সংশোধন করা হয়েছে। বর্তমান APT publisher-এ পুরোনো version আটকে দেওয়ার পরীক্ষা যোগ হয়েছে; আগের version-এর পুরোনো workflow আবার প্রকাশের জন্য চালাবেন না।
- কী পরীক্ষা হয়েছে ও কোন সীমাবদ্ধতা আছে, দেখুন [পুরো প্রজেক্টের audit report](docs/AUDIT-2026-10-27.bn.md) অথবা [English report](docs/AUDIT-2026-10-27.md)।

- Native Homebrew ও Python 3.12+ থাকলে macOS-এ setup করা যাবে; Apple Silicon/Intel path ও dashboard-এ installation progress যোগ হয়েছে। [macOS নির্দেশনা](docs/MACOS.bn.md) দেখুন।

- Domain অথবা page path/port-সহ public HTTP(S) URL দিন; hostname scope নির্ধারণ করে এবং URL-aware tool path/port পায়।
- Scan ও tool check-এর process time limit সরানো হয়েছে; tool নিজে শেষ হয়, output cap-এ থামে, অথবা **Stop** চাপলে বন্ধ হয়।
- Progress bar, elapsed time ও আনুমানিক বাকি সময় আগের মতো আছে।

[English README](README.md) · [Kali APT update](docs/APT.md) · [Windows / WSL](docs/WINDOWS.md) · [macOS](docs/MACOS.bn.md) · [টুল সেটআপ](docs/TOOLS.md) · [পূর্ণ ব্যবহারবিধি](docs/USAGE.bn.md) · [অবদান রাখুন](CONTRIBUTING.bn.md) · [সীমাবদ্ধতা](SECURITY.md)

## কী উন্নতি হয়েছে

- Dashboard ও প্রয়োজনীয় backend tool একসঙ্গে সেটআপ হয়। আগে থেকে ঠিক থাকা tool আবার নামায় না।
- স্বাভাবিকভাবে চালু করলে missing tool আছে কি না দেখে প্রয়োজন হলে installer শুরু করে।
- Windows-এর tool এখন `C:\Users\আপনার-নাম\Tools\EchoRecon\tooling`-এ থাকে। ফলে desktop shortcut দিয়ে চালালেও একই tool পাওয়া যায়।
- সরাসরি Windows, Kali VirtualBox, WSL এবং সমর্থিত Linux family-এর আলাদা সেটআপ আছে। Windows-এর native adapter চালাতে WSL বাধ্যতামূলক নয়।
- Dark/Light layout এক ক্লিকে বদলায়; form-এর লেখা থাকে। Browser-এর resource কমাতে Matrix background ও অন্য animation সরানো হয়েছে।
- আগে থেকে বানানো scan result বা demo data নেই। ব্যর্থতা, সময় শেষ হওয়া ও অসম্পূর্ণ ফল report-এ দেখা যায়।
- Nikto-কে নবম tool হিসেবে যোগ করা হয়েছে। Nuclei ও Nikto দুটো বাছলে Nuclei পাওয়া না গেলে বা ব্যর্থ হলে Nikto চেষ্টা করে; শুধু Nikto বাছলেও চলে। এর check সীমিত রাখা হয়েছে।

আগের আটটি tool হলো **DNSRecon, Subfinder, ProjectDiscovery HTTPX, Nmap, theHarvester, Photon, Arjun ও Nuclei**; **Nikto** এখন নবম। Nuclei ও Nikto দুটো বাছলে Nuclei অনুপস্থিত বা ব্যর্থ হলেই Nikto fallback হিসেবে চলে। শুধু Nikto বাছলেও standalone check চলে। এগুলো install হলেই scan শুরু হয় না, কোনো API account/key তৈরি হয় না।

## ১. আগে যা লাগবে

| কোথায় চালাবেন | প্রয়োজন ও সীমা |
|---|---|
| সরাসরি Windows x64 | Backend setup-এর জন্য **Python 3.12 x64**, Git, সাধারণ user। আগের সাতটি tool স্বয়ংক্রিয়; Nikto-র জন্য আগে Strawberry Perl install করে PATH-এ রাখতে হবে। Nmap-এর official installer-এ নিজে confirmation দিতে হবে। |
| Native macOS, Apple Silicon / Intel | পুরো backend setup-এর জন্য native Homebrew ও **Python 3.12+**। একই `install.sh` / `run.sh` macOS installer বেছে নেয়। Nmap/Nikto Homebrew দিয়ে, অন্য tool verified Darwin release বা আলাদা Python environment-এ বসে। Homebrew-এর OS/architecture support ও package availability প্রযোজ্য; [macOS guide](docs/MACOS.bn.md) দেখুন। |
| Kali Linux / VirtualBox / Kali WSL | Signed APT package বসাতে feed ও package-এর জন্য একবার sudo লাগবে; Git clone পদ্ধতিতে Git, Python ও venv লাগবে। Missing Go tool build করতে Go 1.26+ লাগতে পারে। |
| অন্যান্য সমর্থিত glibc Linux | Debian/Ubuntu, Fedora/RHEL, Arch, openSUSE family; x86_64/aarch64 portable asset। DNSRecon/theHarvester source ইনস্টল করতে Python 3.12+ লাগে। |
| অন্য distro/architecture | Dashboard Python 3.11+; compatible backend নিজে official source থেকে সেটআপ করতে হতে পারে। Alpine/musl automatic target নয়। |

বর্তমান CI Windows/Linux এবং native macOS 15 Apple Silicon/Intel-এ চলে। Mac পরীক্ষায় local HTTP startup, process বন্ধ করা, আলাদা Python environment এবং Bash install/run script আছে; PR-এ Apple Silicon-এর পুরো backend installation-ও target scan ছাড়া যাচাই হয়। Intel backend পাওয়া Homebrew-এর support tier-এর ওপর নির্ভর করে। প্রতিটি OS version বা বাইরের provider-এর কাজ নিশ্চিত হয়েছে—এমন দাবি করা হচ্ছে না। আগের desktop পরীক্ষাগুলোর version [Validation নোটে](docs/VALIDATION.md) আছে।

Linux/macOS-এ **root দিয়ে app চালাবেন না**। Windows-এ administrator terminal লাগে না; Nmap installer দরকার হলে নিজে admin confirmation চাইবে। Password chat/dashboard-এ লিখবেন না।

## ২. Kali-তে APT দিয়ে install ও update

Signed Kali/Debian APT feed-ই স্বয়ংক্রিয় update পদ্ধতি; feed এখন প্রকাশিত আছে। [Kali APT নির্দেশনা](docs/APT.md) মেনে source ও `echo-recon` package একবার বসানোর পর `sudo apt update && sudo apt upgrade` চালালে সর্বশেষ **প্রকাশিত release** আসবে। `main`-এ সাধারণ commit করলেই APT package বদলায় না—নতুন version-এর সঙ্গে মেলা `vX.Y.Z` tag maintainer publish করলে signed package workflow feed update করে। বর্তমান feed [`apt-repo` branch](https://github.com/mdnhbn/echo-recon-workspace/tree/apt-repo)-এ আছে।

আগে Git clone ব্যবহার করলে migrate করার আগে app বন্ধ করুন। Package-এর report/history থাকবে `~/.local/share/echo-recon`-এ; পুরোনো report copy এবং `/usr/bin/echo-recon` ব্যবহার করার নিয়ম APT guide-এ আছে। নতুন version-এ report দেখা না পর্যন্ত পুরোনো clone মুছবেন না।

### Kali/Linux-এ Git clone করে install

Kali-তে প্রথমে প্রয়োজন হলে:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv
```

এরপর সাধারণ user-এর Terminal-এ:

```bash
mkdir -p ~/Tools/02-Custom
cd ~/Tools/02-Custom
git clone https://github.com/mdnhbn/echo-recon-workspace.git
cd echo-recon-workspace
bash install.sh
bash run.sh
```

- `mkdir` folder বানায়।
- `cd` folder-এ ঢোকে।
- `git clone` GitHub-এর project নামায়।
- `install.sh` dashboard-এর আলাদা `.venv` বানায়, package-এর hash যাচাই করে এবং missing backend একসঙ্গে ইনস্টল করে।
- `run.sh` dashboard চালায়।

অন্য Linux family-তে আগে তার package manager দিয়ে Git, উপযুক্ত Python ও venv support ইনস্টল করে একই clone/install/run command দিন। নির্দিষ্ট OS package-এর জন্য Terminal-এ sudo চাইতে পারে। পুরো installer/app `sudo` দিয়ে চালাবেন না।

### Native macOS-এ install

[Homebrew-এর official নির্দেশনা](https://docs.brew.sh/Installation) মেনে Homebrew এবং তার **Next steps** শেষ করুন। Apple Silicon হলে Rosetta ছাড়া native Terminal খুলুন। তারপর:

```bash
brew install python@3.12 git
mkdir -p ~/Tools
cd ~/Tools
git clone https://github.com/mdnhbn/echo-recon-workspace.git
cd echo-recon-workspace
bash install.sh
bash run.sh
```

Script Apple Silicon-এর `/opt/homebrew` বা Intel-এর `/usr/local` prefix এবং উপযুক্ত Python খুঁজে নেয়। Missing backend একসঙ্গে বসে; Go SDK লাগে না। Local browser interface ব্যবহার করার সময় Terminal খোলা রাখুন। Dashboard-এর **Setup all tools** চাপলে macOS setup-এর progress dashboard-এ দেখা যাবে। পুরোনো macOS/Intel Mac-এ Homebrew package পাওয়া নির্ভর করে তার বর্তমান support tier-এর ওপর। [বিস্তারিত বাংলা macOS guide](docs/MACOS.bn.md) বা [English guide](docs/MACOS.md) দেখুন। Native Mac-এ Kali APT update command প্রযোজ্য নয়।

## ৩. সরাসরি Windows-এ install

Windows 10 (version 1809 বা নতুন) অথবা Windows 11-এ Windows Terminal/PowerShell খুলে আগে দেখুন WinGet আছে কি না:

```powershell
winget --version
```

version দেখালে সাধারণ user হিসেবেই নিচের দুটি command দিন। Installer কোনো prompt দেখালে পড়ে নিজে সম্মতি দিন:

```powershell
winget install --id Python.Python.3.12 --exact --source winget
winget install --id Git.Git --exact --source winget
```

Terminal বন্ধ করে আবার খুলুন, তারপর যাচাই করুন:

```powershell
py -3.12 --version
git --version
```

এই project-এর Windows backend-এর জন্য **Python 3.12 x64** দরকার। Git শুধু GitHub থেকে repo clone/update করতে লাগে; আলাদা compiler বা Linux system দরকার হয় না। `winget` না থাকলে Microsoft Store থেকে Microsoft-এর **App Installer** install/update করে Terminal আবার খুলুন। App Installer আগে থেকেই থাকলেও WinGet register না হলে PowerShell-এ এই command দিন; তারপর Terminal বন্ধ করে আবার খুলুন:

```powershell
Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe
```

বিকল্পভাবে [Python.org](https://www.python.org/downloads/windows/) থেকে Python এবং [Git for Windows](https://git-scm.com/downloads/win) থেকে Git install করা যায়। দুটো install হলে সাধারণ PowerShell-এ নিচের command দিন:

```powershell
git clone https://github.com/mdnhbn/echo-recon-workspace.git
cd echo-recon-workspace
.\install.ps1
.\run.ps1
```

একাধিক Python থাকলে নিজের Python-এর সঠিক path বেছে নিতে পারবেন:

```powershell
.\install.ps1 -PythonExe 'C:\Path\To\Python312\python.exe'
```

**Nmap আলাদা ধাপ:** [official Windows installer](https://nmap.org/download.html) খুলে license/administrator confirmation নিজে শেষ করুন। তারপর **Check installed tools** বা **Setup all tools** আবার চাপুন। App নিজে থেকে license মেনে নেয় না বা driver ইনস্টল করে না।

PowerShell script বন্ধ করলে policy কমাবেন না; [Windows guide-এর সরাসরি Python পদ্ধতি](docs/WINDOWS.md) ব্যবহার করুন। Git না চাইলে GitHub-এর **Code → Download ZIP**, নতুন folder-এ Extract করে সেই folder-এ installer চালাতে পারেন। পুরোনো copy-এর ওপর Extract করবেন না।

## ৪. চালু হয়েছে কি না দেখুন

Desktop-এ browser নিজে থেকে **http://127.0.0.1:8001** খোলে। না খুললে নিজে লিখুন। Terminal খোলা রাখুন; app বন্ধ করতে ওই Terminal-এ Ctrl+C দিন। Browser tab বন্ধ করলেই server বন্ধ হয় না।

`127.0.0.1` মানে যে environment-এ server চলছে সেটি। VirtualBox-এর Kali ও Windows host-এর loopback আলাদা। WSL-এর project Linux HOME-এ রাখুন; Windows/Kali/WSL-এর `.venv` ও `data` মেশাবেন না।

### Automatic setup ও retry

1. চালুর সময় স্থানীয় help/পরিচয় দেখে tool প্রস্তুত কি না যাচাই হয়।
2. Missing থাকলে একসঙ্গে সেটআপ হয়। Windows-এর progress dashboard-এ; Linux desktop-এ আলাদা Terminal-এ দেখা যায়।
3. Headless Linux/WSL-এ `run.sh` একই Terminal-এ setup চালায়, যাতে sudo prompt দেখা যায়।
4. একই ব্যর্থ desktop automatic চেষ্টা `data/auto-setup.json`-এ মনে রাখে। শুধু restart দিলে বারবার একই download চালায় না। Error পড়ে **Setup all tools** দিয়ে retry করুন।
5. **Check installed tools** আবার চাপুন। `ready` হলে local help/পরিচয় পাস; Nuclei-র ক্ষেত্রে local official template version-ও পাওয়া গেছে। তবে প্রতিটি template file, API, provider বা scan result যাচাই হয় না। Nuclei template version না পাওয়া গেলে **Setup all tools** engine reinstall না করে official template refresh করার চেষ্টা করে। `unverified` হলে version/path ও দেখানো error দেখুন।
6. অন্য project-এর wrapper, অচেনা folder বা অসম্পূর্ণ environment নিজে থেকে overwrite করে না।

শুধু dashboard ইনস্টল করতে `bash install.sh --dashboard-only` বা `.\install.ps1 -DashboardOnly` দিন। পরে automatic backend setup-ও বন্ধ রাখতে চালান:

```bash
bash run.sh --no-tool-setup
```

Windows-এ:

```powershell
.\run.ps1 -NoToolSetup
```

Browser নিজে থেকে খুলতে না চাইলে সঙ্গে `--no-browser` / `-NoBrowser` দিন। Direct entry point-এ `python app.py --no-tool-setup`-ও আছে।

## ৫. Form পূরণ করার সহজ নিয়ম

বিস্তারিত [বাংলা ব্যবহারবিধি](docs/USAGE.bn.md)-তে আছে। সংক্ষেপে:

1. নিজের বা স্পষ্ট অনুমতি থাকা domain অথবা public HTTP(S) URL **Primary domain**-এ দিন। URL-এর path ও port HTTPX, Nuclei, Photon ও Arjun-এ যায়; query ও fragment বাদ থাকে। Username, IP বা wildcard গ্রহণ করা হয় না।
2. URL/domain থেকে পাওয়া primary host নিজে থেকে যুক্ত হয়। চাইলে **Additional authorized hosts**-এ আরও সর্বোচ্চ চারটি অনুমোদিত subdomain দিন (সব মিলিয়ে পাঁচটি)। URL দিলে scope check-এ শুধু hostname নেওয়া হয়।
3. প্রয়োজনীয় check বাছুন। Photon/Arjun-এর জন্য একই run-এ HTTPX দিয়ে live scoped host পাওয়া লাগবে।
4. **গতিসীমা** tool যেটুকু সমর্থন করে ততটুকু নিয়ন্ত্রণ করে; সব tool মিলিয়ে একটি মোট request meter নয়।
5. Dashboard tool-কে নির্দিষ্ট সময় পরে বন্ধ করে না। Tool শেষ হওয়া পর্যন্ত চলে, অথবা **Stop** চাপলে থামে। Tool নিজে network/provider error দিতে পারে; output-এর সীমা থাকে।
6. অনুমতি ও network সীমা পড়ে সত্য হলে confirmation দিয়ে Start চাপুন। ইনস্টল চললে assessment শুরু হয় না।
7. Overall progress শেষ হওয়া tool phase গোনে; tool-এর bar শেষ হওয়া host attempt গোনে। Elapsed time দেখা যায়, আর যথেষ্ট কাজ শেষ হলে rough ETA আসে। Tool host-এর ভেতরের শতাংশ না জানালে তা বানিয়ে দেখানো হয় না। **Stop** দিলে Linux process group বা Windows-এর contained process tree বন্ধ হয়। শেষে evidence ও report পড়ুন।

Nmap top-100 port-এ TCP connect/service check করে। Windows-এ `-Pn` ব্যবহার করে raw-packet discovery এড়ায়। Nuclei finding হাতে যাচাই না করা পর্যন্ত **unverified**। Tool সফল বা finding শূন্য মানেই website নিরাপদ নয়।

এটি network sandbox নয়। Third-party tool আবার DNS resolve করতে পারে, অন্য data service বা secondary destination-এ request পাঠাতে পারে। [Security সীমাবদ্ধতা](SECURITY.md) পড়ুন।

## ৬. Update, backup এবং uninstall

Server বন্ধ করে `data/`-এর private backup রাখুন। Kali/Linux বা macOS-এ Git clone দিয়ে ইনস্টল করলে repo folder-এর terminal-এ:

```bash
git status
git pull --ff-only
bash install.sh
bash run.sh
```

Native Windows-এর Git clone update করতে PowerShell-এ repo folder খুলুন, চলমান app বন্ধ করুন, তারপর:

```powershell
git status --short
git pull --ff-only
.\install.ps1
.\run.ps1
```

`git pull` GitHub-এর নতুন code আনে; installer Windows-এর dependency ও missing backend মিলিয়ে নেয়। `sudo apt upgrade` Kali/Linux APT install-এর জন্য, native Windows-এর জন্য নয়। ZIP দিয়ে install করলে নতুন ZIP নতুন folder-এ extract করুন; পুরোনো folder-এর ওপর extract করবেন না। Force reset দেবেন না। পুরোনো venv অচেনা/নষ্ট বা অন্য Python major/minor দিয়ে তৈরি হলে installer সেটি রেখে থামে। Private data backup রেখে নতুন project folder ব্যবহার করুন, অথবা নিজের venv পরীক্ষা করে সচেতনভাবে rebuild করুন। Report/history/setup log/raw evidence-এ sensitive তথ্য থাকতে পারে; এগুলো GitHub-এ দেবেন না। কিছু secret ঢাকলেও সব চেনা সম্ভব নয়; report AI service-এ পাঠানো হয় না।

### আগের সংস্করণের saved demo মুছতে

Production demo তৈরি হয় না। পুরোনো demo সরাতে server বন্ধ করে Linux-এ `.venv/bin/python maintenance.py remove-demo`, Windows-এ `.\.venv\Scripts\python.exe maintenance.py remove-demo` দিন। শুধু demo হিসেবে চিহ্নিত পুরোনো record সরবে; বাস্তব history থাকবে। পুরো `data/` মুছবেন না।

Repo folder Trash-এ নিলে বাইরে ইনস্টল করা tool নিজে থেকে uninstall হয় না। নিজের দরকারি history backup রেখে এবং installer-owned tool folder দেখে তারপর removal করুন।

## ৭. শিক্ষার্থী ও সহপাঠীদের অবদান

যে কেউ **Fork → branch → code/test/doc পরিবর্তন → Pull Request** দিতে পারেন। Maintainer review করে merge করবেন। [বাংলা contribution guide](CONTRIBUTING.bn.md), [English guide](CONTRIBUTING.md), [Code of Conduct](CODE_OF_CONDUCT.md) দেখুন।

Developer test:

```bash
.venv/bin/python -m unittest discover -s tests -v
bash -n install.sh run.sh
```

Windows-এ `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`। Test mock/স্থানীয় child process ব্যবহার করে; public target scan বা production history-তে fake result তৈরি করে না।

মূল লেখক **Ahammed**; মূল source snapshot `f3fbf45`। mdnhbn জানিয়েছেন তিনি সহযোগী সহপাঠী এবং project সরবরাহ করেছেন। Credit রাখা হয়েছে। Project-এর **[MIT license](LICENSE)** ও [NOTICE.md](NOTICE.md) দেখুন; third-party tool-এর নিজের license বহাল থাকে।
