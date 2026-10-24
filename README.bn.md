# Echo Recon 6.5.0 — বাংলা নির্দেশনা

এটি নিজের কম্পিউটারে চালানোর dashboard। আটটি আলাদা tool-এর কাজ নির্দিষ্ট ক্রমে চালায়, প্রমাণ রাখে এবং HTML/JSON report তৈরি করে। মূল project [Ahammed-এর Echo Recon / Auto-Recon](https://github.com/ahammed18122002-art/auto-rec); mdnhbn সহযোগিতায় এই সংস্করণ উন্নত হয়েছে।

[English README](README.md) · [Windows / WSL](docs/WINDOWS.md) · [টুল সেটআপ](docs/TOOLS.md) · [পূর্ণ ব্যবহারবিধি](docs/USAGE.bn.md) · [অবদান রাখুন](CONTRIBUTING.bn.md) · [সীমাবদ্ধতা](SECURITY.md)

## কী উন্নতি হয়েছে

- Dashboard ও প্রয়োজনীয় backend tool একসঙ্গে সেটআপ হয়। আগে থেকে ঠিক থাকা tool আবার নামায় না।
- স্বাভাবিকভাবে চালু করলে missing tool আছে কি না দেখে প্রয়োজন হলে installer শুরু করে।
- Windows-এর tool এখন `C:\Users\আপনার-নাম\Tools\EchoRecon\tooling`-এ থাকে। ফলে desktop shortcut দিয়ে চালালেও একই tool পাওয়া যায়।
- সরাসরি Windows, Kali VirtualBox, WSL এবং সমর্থিত Linux family-এর আলাদা সেটআপ আছে। Windows-এর native adapter চালাতে WSL বাধ্যতামূলক নয়।
- Dark/Light layout এক ক্লিকে বদলায়; form-এর লেখা থাকে। দুই layout-এই Matrix animation আছে; reduced-motion পছন্দ মেনে চলে।
- আগে থেকে বানানো scan result বা demo data নেই। ব্যর্থতা, সময় শেষ হওয়া ও অসম্পূর্ণ ফল report-এ দেখা যায়।

আটটি tool হলো **DNSRecon, Subfinder, ProjectDiscovery HTTPX, Nmap, theHarvester, Photon, Arjun ও Nuclei**। এগুলো ইনস্টল হলেই scan শুরু হয় না, কোনো API account/key তৈরি হয় না।

## ১. আগে যা লাগবে

| কোথায় চালাবেন | প্রয়োজন ও সীমা |
|---|---|
| সরাসরি Windows x64 | Backend setup-এর জন্য **Python 3.12 x64**, Git, সাধারণ user। সাতটি tool স্বয়ংক্রিয়; Nmap-এর official installer-এ নিজে confirmation দিতে হবে। |
| Kali Linux / VirtualBox / Kali WSL | Distro Python, venv, দরকারি OS package-এর জন্য terminal-এ sudo। Missing Go tool build করতে Go 1.26+ লাগতে পারে। |
| অন্যান্য সমর্থিত glibc Linux | Debian/Ubuntu, Fedora/RHEL, Arch, openSUSE family; x86_64/aarch64 portable asset। DNSRecon/theHarvester source ইনস্টল করতে Python 3.12+ লাগে। |
| অন্য distro/architecture | Dashboard Python 3.11+; compatible backend নিজে official source থেকে সেটআপ করতে হতে পারে। Alpine/musl automatic target নয়। |

Windows ও Kali-তে স্থানীয় tool/help এবং regression পরীক্ষা করা হয়েছে। অন্য distro-গুলোর installer logic mock দিয়ে পরীক্ষা করা হয়েছে; প্রতিটি distro-তে fresh install বা বাইরের website-এ পূর্ণ scan হয়েছে—এমন দাবি করা হচ্ছে না।

Linux-এ **root দিয়ে app চালাবেন না**। Windows-এ administrator terminal লাগে না; Nmap installer দরকার হলে নিজে admin confirmation চাইবে। Password chat/dashboard-এ লিখবেন না।

## ২. Kali/Linux-এ download ও install

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

## ৩. সরাসরি Windows-এ install

[Python 3.12 x64](https://www.python.org/downloads/windows/) ও [Git](https://git-scm.com/downloads/win) ইনস্টল করে সাধারণ PowerShell-এ দিন:

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
5. **Check installed tools** আবার চাপুন। `ready` শুধু help/পরিচয় যাচাই পাস; API, template, provider বা scan-এর ফলের নিশ্চয়তা নয়। `unverified` হলে আগে version/path দেখুন।
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

1. নিজের বা স্পষ্ট অনুমতি থাকা hostname **Primary domain**-এ দিন। `https://`, path, port বা wildcard নয়।
2. **Exact authorized hosts**-এ primary-সহ সর্বোচ্চ পাঁচটি নাম এক লাইনে একটি দিন। অন্য নামগুলো primary-এর subdomain হতে হবে।
3. প্রয়োজনীয় check বাছুন। Photon/Arjun-এর জন্য একই run-এ HTTPX দিয়ে live scoped host পাওয়া লাগবে।
4. **গতিসীমা** tool যেটুকু সমর্থন করে ততটুকু নিয়ন্ত্রণ করে; সব tool মিলিয়ে একটি মোট request meter নয়।
5. **১২০ সেকেন্ড** প্রতিটি tool/host চেষ্টার সময়; পুরো run-এর সময় নয়।
6. অনুমতি ও network সীমা পড়ে সত্য হলে confirmation দিয়ে Start চাপুন। ইনস্টল চললে assessment শুরু হয় না।
7. **Stop** দিলে Linux process group বা Windows-এর contained process tree বন্ধ হয়। শেষে evidence ও report পড়ুন।

Nmap top-100 port-এ TCP connect/service check করে। Windows-এ `-Pn` ব্যবহার করে raw-packet discovery এড়ায়। Nuclei finding হাতে যাচাই না করা পর্যন্ত **unverified**। Tool সফল বা finding শূন্য মানেই website নিরাপদ নয়।

এটি network sandbox নয়। Third-party tool আবার DNS resolve করতে পারে, অন্য data service বা secondary destination-এ request পাঠাতে পারে। [Security সীমাবদ্ধতা](SECURITY.md) পড়ুন।

## ৬. Update, backup এবং uninstall

Server বন্ধ করে `data/`-এর private backup রাখুন। নিজের source edit থাকলে আগে `git status` দেখুন:

```bash
git status
git pull --ff-only
bash install.sh
bash run.sh
```

Windows-এ pull-এর পরে `.\install.ps1`, `.\run.ps1` ব্যবহার করুন। Force reset দেবেন না। পুরোনো venv অচেনা/নষ্ট বা অন্য Python major/minor দিয়ে তৈরি হলে installer সেটি রেখে থামে। Private data backup রেখে নতুন project folder ব্যবহার করুন, অথবা নিজের venv পরীক্ষা করে সচেতনভাবে rebuild করুন। Report/history/setup log/raw evidence-এ sensitive তথ্য থাকতে পারে; এগুলো GitHub-এ দেবেন না। কিছু secret ঢাকলেও সব চেনা সম্ভব নয়; report AI service-এ পাঠানো হয় না।

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
