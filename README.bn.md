# Echo Recon 6.1 — বাংলা নির্দেশনা

এটি Kali Linux-এ নিজের কম্পিউটারে চালানোর একটি dashboard। আগের আটটি টুল—**DNSRecon, Subfinder, ProjectDiscovery HTTPX, Nmap, theHarvester, Photon, Arjun ও Nuclei**—রয়েছে। নতুন সংস্করণে ভুল ফল শনাক্ত করা, পরীক্ষা বন্ধ করা, ইতিহাস রাখা ও প্রমাণসহ রিপোর্ট দেখানো উন্নত হয়েছে।

[English README](README.md) · [Windows/WSL নির্দেশনা](docs/WINDOWS.md) · [অবদান রাখুন](CONTRIBUTING.bn.md) · [আটটি টুলের সেটআপ](docs/TOOLS.md) · [সীমাবদ্ধতা](SECURITY.md)

## শিক্ষার্থী ও সহপাঠীদের অবদান

যে কেউ এই public repository **Fork → নতুন branch → পরিবর্তন → Pull Request** পদ্ধতিতে অবদান রাখতে পারবেন। Maintainer review করে মূল project-এ যোগ করবেন। সরাসরি মূল repo-তে সবার write access লাগবে না। Bug/feature form ও PR template দেওয়া আছে। [বাংলা contributor guide](CONTRIBUTING.bn.md) এবং [আচরণবিধি](CODE_OF_CONDUCT.md) দেখুন। Project-এ মূল লেখকের credit-সহ **[MIT license](LICENSE)** আছে।

## Windows-এ ব্যবহার

- **Windows + Kali WSL2:** আটটি টুলসহ Linux workflow; Windows browser-এ dashboard খুলবেন।
- **সরাসরি Windows + Python:** dashboard, demo, history, report ও development test। Live assessment-এর জন্য Kali WSL2 লাগবে।
- `install.ps1`, `run.ps1` এবং আগে ইনস্টল করা WSL copy চালানোর `run-wsl.ps1` আছে। বিস্তারিত [Windows নির্দেশনা](docs/WINDOWS.md)। Windows ও Linux-এর `.venv`/`data` আলাদা রাখবেন।

## ১. আগে যা লাগবে

- Kali Linux এবং Python 3.11 বা নতুন সংস্করণ।
- সাধারণ user account। **Root হিসেবে চালাবেন না।**
- ইনস্টলের সময় ইন্টারনেট। Demo চালাতে বাইরের scanner বা কোনো সাইটে পরীক্ষা দরকার নেই।

VirtualBox-এর ভেতরে Kali-র Terminal খুলুন। প্রতিটি block আলাদা করে লিখে Enter চাপুন। `sudo` পাসওয়ার্ড লেখার সময় অক্ষর দেখা যায় না—এটি স্বাভাবিক।

## ২. ডাউনলোড এবং ইনস্টল

প্রথমে প্রয়োজনীয় সাধারণ সফটওয়্যার:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv
```

এরপর project রাখার ফোল্ডার তৈরি করে ডাউনলোড করুন:

```bash
mkdir -p ~/Tools/02-Custom
cd ~/Tools/02-Custom
git clone https://github.com/mdnhbn/echo-recon-workspace.git
cd echo-recon-workspace
```

`mkdir` ফোল্ডার বানায়, `cd` ফোল্ডারে ঢোকে, `git clone` GitHub থেকে project-এর কপি নামায়। ডাউনলোড করলেই ইনস্টল হয় না। এখন চালান:

```bash
bash install.sh
```

এটি project-এর ভেতর `.venv` নামে আলাদা Python পরিবেশ তৈরি করে। নির্দিষ্ট version ও SHA-256 hash মিলিয়ে dashboard-এর প্রয়োজনীয় package ইনস্টল করে। বাইরের আটটি scanner ইনস্টল করে না। আগের টুলের ফোল্ডার বা Java/Go বদলায় না।

Git ব্যবহার করতে না চাইলে GitHub-এ **Code → Download ZIP**, তারপর নতুন ফোল্ডারে Extract করে সেই ফোল্ডারে Terminal খুলে `bash install.sh` দিন। পুরোনো ইনস্টলেশনের ওপর Extract করবেন না।

## ৩. চালাবেন যেভাবে

```bash
cd ~/Tools/02-Custom/echo-recon-workspace
bash run.sh
```

Terminal খোলা রাখুন। Desktop session-এ server প্রস্তুত হলে default browser নিজে থেকে dashboard খুলবে। না খুললে Kali-র Firefox-এ লিখুন:

**http://127.0.0.1:8001**

`127.0.0.1` মানে আপনার নিজের Kali। পুরোনো Echo-এর 8000 port-এর সঙ্গে মিশে না যাওয়ার জন্য নতুন সংস্করণ 8001 ব্যবহার করে।

Browser নিজে থেকে খুলতে না চাইলে `bash run.sh --no-browser` দিন। সরাসরি Windows-এ একই option: `.\run.ps1 -NoBrowser`। Desktop ছাড়া WSL session-এ Windows browser-এ ঠিকানাটি নিজে খুলুন।

## ৪. প্রথমে Demo দেখুন

1. **Open demo / ডেমো দেখুন** চাপুন।
2. ধাপগুলোর অগ্রগতি দেখুন। এখানে ফলগুলো বানানো উদাহরণ—বাস্তবে কোনো scanner বা DNS lookup চলে না।
3. শেষ ধাপে ইচ্ছা করে একটি **timeout** দেখানো হয়।
4. পুরো কাজ **partial** দেখাবে। এটি ত্রুটি নয়: অসম্পূর্ণ পরীক্ষাকে নিরাপদ বলা ঠিক নয়।
5. **View report** চাপুন। চাইলে **HTML** বা **JSON** ডাউনলোড করুন।
6. **Saved history** থেকে আগের রিপোর্ট আবার খুলুন।

পরীক্ষা চলাকালে **Stop / বন্ধ করুন** দিলে বর্তমান process ও Linux-এর তার process group বন্ধের অনুরোধ যায়। Dashboard বন্ধ করতে Terminal-এ **Ctrl+C** দিন। বিদ্যুৎ চলে যাওয়া বা process জোর করে kill করা graceful shutdown নয়; orphan process রয়ে গেছে কি না প্রয়োজনে পরীক্ষা করতে হবে।

## ৫. বাস্তব পরীক্ষা করার আগে

শুধু নিজের বা স্পষ্ট অনুমতি থাকা host ব্যবহার করুন। [টুল সেটআপ গাইড](docs/TOOLS.md) দেখুন। টুল আছে কি না জানতে dashboard-এর **Check installed tools** অথবা:

```bash
.venv/bin/python doctor.py
```

এটি টুলের local help/পরিচয় দেখে; কোনো target scan করে না। পুরো version compatibility-এর নিশ্চয়তা নয়। নতুন tool ইনস্টল বা PATH বদলানোর পর dashboard বন্ধ করে আবার চালান।

## ৬. Form পূরণ করার নিয়ম

1. **Primary domain**: মূল hostname লিখুন; `https://`, path, port বা `*` দেবেন না।
2. **Exact authorized hosts**: অনুমোদিত hostname প্রতি লাইনে একটি লিখুন। মূল hostname-টিও রাখুন। সর্বোচ্চ পাঁচটি। অতিরিক্তগুলো মূল domain-এর subdomain হতে হবে।
3. প্রয়োজনীয় check বেছে নিন। DNS, subdomain ও HTTPX আগে থেকে selected থাকে। বাকিগুলো আলাদা করে বেছে নিতে হয়।
4. Photon বা Arjun চাইলে একই run-এ HTTPX-ও বেছে নিন। সচল in-scope host না পাওয়া গেলে এই দুটি ধাপ **skipped** হবে। আন্দাজ করে target বেছে নেয় না।
5. Rate ও প্রতি tool/host-এর সময়সীমা ঠিক করুন। Rate সব টুল মিলিয়ে মোট request budget নয়।
6. মালিকানা/অনুমতি ও network সীমাবদ্ধতা বোঝার checkbox দিন। তারপর **Start assessment**।
7. ফলের প্রতিটি ধাপ, প্রমাণ ও diagnostic পড়ুন। শুধু সবুজ রং দেখে সিদ্ধান্ত নেবেন না।

Subfinder কোনো নতুন subdomain পেলেই সেটিতে active scan হয় না। শুধু আপনার explicit scope তালিকার host-গুলো active ধাপে দেওয়া হয়। তবে এটি network firewall নয়: DNS বদলাতে পারে এবং বাইরের crawler/template অন্য destination-এ অনুরোধ পাঠাতে পারে। কঠোর isolation লাগলে আলাদা lab ও firewall দরকার।

## ৭. ফলের শব্দগুলোর অর্থ

| অবস্থা | অর্থ |
|---|---|
| `done` | Command সফল exit করেছে; সাইট নিরাপদ হওয়ার সনদ নয়। |
| `missing` | প্রয়োজনীয় tool পাওয়া যায়নি। |
| `unverified` | Executable পাওয়া গেছে, কিন্তু পরিচয়/help যাচাই পাস করেনি। |
| `error` | Tool বা result parsing ব্যর্থ হয়েছে। |
| `timeout` | নির্ধারিত সময়ে শেষ হয়নি। |
| `output_limit` | অতিরিক্ত output হওয়ায় বন্ধ হয়েছে। |
| `skipped` | পূর্বশর্ত পূরণ না হওয়ায় ধাপ চালানো হয়নি। |
| `cancelled` | আপনি কাজ থামিয়েছেন। |
| `interrupted` | চলার সময় server restart হয়েছে; পরীক্ষা অসম্পূর্ণ। |
| `partial` | কিছু ধাপ অসম্পূর্ণ; পরিষ্কার নিরাপত্তা সিদ্ধান্ত দেওয়া যাবে না। |

Nuclei finding মানে যাচাই করার মতো সম্ভাব্য বিষয়। রিপোর্টে **unverified automated finding** বলা থাকে। হাতে যাচাই ছাড়া নিশ্চিত দুর্বলতা বলবেন না। কোনো finding না পাওয়া মানেও সাইট নিরাপদ নয়।

## ৮. তথ্য কোথায় থাকে

এই repository-র `data/` ফোল্ডারে SQLite history ও Photon-এর raw crawl file থাকতে পারে। এগুলোতে সংবেদনশীল তথ্য থাকতে পারে। Git-এ `data/` বাদ দেওয়া আছে। সাধারণ secret pattern আড়াল করা হয়, তবে সব secret ধরা সম্ভব নয়—রিপোর্ট শেয়ার করার আগে নিজে দেখুন। কোনো AI provider-এ রিপোর্ট পাঠানো হয় না; এই সংস্করণে AI integration নেই।

## ৯. Update, backup এবং uninstall

আগে Ctrl+C দিয়ে dashboard বন্ধ করুন। প্রয়োজন হলে `data/`-এর private backup রাখুন। তারপর:

```bash
git status
git pull --ff-only
bash install.sh
bash run.sh
```

নিজে কোড বদলালে আগে সেটি সংরক্ষণ করুন। পুরোনো Echo-এর report স্বয়ংক্রিয়ভাবে import করা হয় না। একসঙ্গে একই data directory দিয়ে একাধিক server চালাবেন না।

Uninstall করতে dashboard বন্ধ করে file manager দিয়ে শুধু **এই project folder** Trash-এ সরান। দরকার হলে আগে `data/` backup নিন। বাইরের scanner-গুলো মুছে যাবে না।

## ১০. সাধারণ সমস্যার সমাধান

- **Root হিসেবে চলছে না:** সাধারণ Kali user-এর Terminal ব্যবহার করুন।
- **venv error:** `python3-venv` ইনস্টল আছে কি না দেখুন।
- **HTTPX unverified:** Python HTTPX ও ProjectDiscovery HTTPX আলাদা। `command -v httpx` এবং টুল গাইড দেখুন।
- **Reload/CSRF error:** server restart-এর পরে browser page reload করুন।
- **8001 port ব্যস্ত:** আগে চালানো এই dashboard বন্ধ করুন।
- **Timeout/partial:** রিপোর্টের diagnostics পড়ুন; এটি অসম্পূর্ণ পরীক্ষা।
- **Tool install করার পরেও পুরোনো health:** dashboard restart করুন।

## ১১. Developer পরীক্ষা

```bash
.venv/bin/python -m unittest discover -s tests -v
bash -n install.sh run.sh
```

এগুলো mock ফল ও local process দিয়ে চলে; কোনো public target scan করে না।

মূল project: **Ahammed**, [auto-rec](https://github.com/ahammed18122002-art/auto-rec)। Upgrade collaboration: **mdnhbn**। Maintainer-এর নির্দেশনায় **[MIT license](LICENSE)** যোগ করা হয়েছে। বাইরের tool-গুলোর নিজস্ব license বহাল। বিস্তারিত [NOTICE.md](NOTICE.md)।
