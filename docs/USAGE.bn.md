# Echo Recon ব্যবহার করবেন যেভাবে

**[English guide](USAGE.md)** · [ইনস্টল](../README.bn.md) · [টুল সেটআপ](TOOLS.md) · [Windows / WSL](WINDOWS.md)

Echo Recon একটি স্থানীয় dashboard। এটি নির্দিষ্ট ক্রমে নয়টি আলাদা টুল চালায় এবং তাদের প্রমাণ রিপোর্টে রাখে। Dashboard খুললেই scan শুরু হয় না। এই গাইডে `example.com` শুধু form বোঝানোর নমুনা: **নিজের বা স্পষ্ট অনুমতি থাকা domain দিয়ে এটি বদলাবেন। নমুনা ঠিকানাগুলোতে Start চাপবেন না।**

## ১. Dashboard খুলুন

Kali-র Terminal থেকে নিজের ইনস্টল করা project folder-এ গিয়ে চালান:

```bash
cd ~/Tools/02-Custom/echo-recon-workspace
bash run.sh
```

Terminal খোলা রাখুন। Firefox-এ **http://127.0.0.1:8001** খোলার কথা। না খুললে নিজে ঠিকানাটি লিখুন। এটি আপনার নিজের Kali-র dashboard-এর ঠিকানা; assessment form-এ যে domain লিখবেন, এটি সেই domain নয়।

সাধারণ user দিয়ে চালান; Linux-এ root দিয়ে app চলে না। সরাসরি Windows-এর নিজস্ব managed tool ও adapter আছে; WSL আলাদা ঐচ্ছিক Linux environment। Windows-এ `install.ps1` / `run.ps1` ব্যবহার করুন। অন্য সমর্থিত Linux family-তে সঠিক Python/package-manager নিয়ে Linux script চালান। বিস্তারিত [WINDOWS.md](WINDOWS.md), [TOOLS.md](TOOLS.md)।

### দুই ধরনের layout বদলাবেন যেভাবে

Header-এর **Light layout / হালকা** চাপলে dashboard-এর হালকা layout খুলবে। এরপর বোতামে **Dark layout / ডার্ক** লেখা থাকবে; আবার চাপলে dark layout ফিরবে। বোতামে পরের যে layout খুলবে তার নাম লেখা থাকে, বর্তমান layout-এর নাম নয়।

Layout বদলালে form-এ লেখা নাম, চলমান job ও দেখানো ফল একই জায়গায় থাকে। Browser-এর local storage চালু থাকলে এই dashboard address-এর জন্য পছন্দটি একই browser-এ মনে রাখে। নতুন browser/profile, storage পরিষ্কার করা বা storage বন্ধ থাকলে default dark layout আসতে পারে। একই address-এর আরেকটি tab খোলা থাকলে browser storage event সমর্থিত অবস্থায় সেটিও সংরক্ষিত পছন্দ অনুসরণ করে।

দুই layout-এই স্থির background থাকে। Browser-এর কাজ কমাতে Matrix canvas, ঘূর্ণায়মান icon, progress pulse ও smooth scrolling সরানো হয়েছে। Light/Dark বোতাম dashboard-এর চেহারা বদলায়, scan setting নয়। App-এর ভেতরে নির্দেশনা দেখতে header-এর **How to use / ব্যবহারবিধি** অথবা sidebar-এর **Full usage guide / বিস্তারিত নিয়ম** চাপুন।

## ২. Automatic setup ও টুল যাচাই

Default installer dashboard ও missing backend একসঙ্গে সেটআপ করে। স্বাভাবিক desktop startup-এও আগে স্থানীয় tool দেখে প্রয়োজন হলে fixed installer শুরু হয়। Headless Linux/WSL-এ একই Terminal ব্যবহার হয়, যাতে sudo prompt দেখা যায়। Tool ইনস্টল হলেই scan শুরু হয় না।

1. **Tool health** / **Download / Setup**-এর progress পড়ুন। Windows-এ আগের সাতটি compatible backend আলাদা user folder-এ ইনস্টল হয়; Strawberry Perl PATH-এ থাকলে Nikto source-ও ইনস্টল হয়। Nmap-এর official Windows installer-এ license/admin confirmation নিজে দিতে হবে।
2. Linux desktop-এ আলাদা visible Terminal খুলবে। Fixed OS package manager চাইলে password **শুধু ওই Terminal-এ** দিন; dashboard বা chat-এ নয়। কাজ শেষ হলে setup Terminal বন্ধ করুন।
3. সফল/ব্যর্থ হওয়ার বার্তা না আসা পর্যন্ত অপেক্ষা করুন। Download বা Terminal খোলাই সফল ইনস্টল নয়। অন্যের wrapper, অচেনা folder বা অসম্পূর্ণ environment নিজে থেকে overwrite করে না।
4. **Check installed tools** চাপুন। Main card ও খোলা setup popup-এর ফল একসঙ্গে নতুন হবে।
5. Desktop automatic setup একই missing-tool set নিয়ে আগে ব্যর্থ হলে restart-এ বারবার একই চেষ্টা করে না। Error মিটিয়ে **Setup all tools** চাপুন। Headless CLI startup আবার check করে; প্রয়োজন হলে নিচের opt-out দিন।

| অবস্থা | অর্থ | কী করবেন |
|---|---|---|
| `ready` | স্থানীয় help/পরিচয় ও adapter-এর flag মিলেছে; Nuclei-র স্থানীয় official template version-ও পাওয়া গেছে। | প্রতিটি template file বা provider যাচাই নয়। প্রয়োজনীয় check বেছে নিয়ে ফল দেখুন। |
| `missing` | Managed path/PATH-এ উপযুক্ত command পাওয়া যায়নি। | এই server যে environment-এ চলে, সেখানেই install করে recheck করুন। |
| `unverified` | Program পাওয়া গেছে, কিন্তু help/পরিচয় মেলেনি। | আগে resolved path ও version দেখুন; অন্ধভাবে reinstall নয়। |

**HTTPX:** এখানে ProjectDiscovery HTTPX লাগে। Python HTTPX আলাদা client। নাম মেলানোর জন্য অন্য program মুছবেন না বা system executable overwrite করবেন না।

### Terminal দিয়ে plan বা retry

আগে assessment শেষ/বন্ধ করুন। Repository folder-এ সাধারণ user দিয়ে দিন।

**Linux / WSL:**

```bash
.venv/bin/python setup_tools.py --plan
.venv/bin/python setup_tools.py --install
.venv/bin/python doctor.py
```

**সরাসরি Windows, Python 3.12 x64:**

```powershell
.\.venv\Scripts\python.exe setup_tools_windows.py --plan
.\.venv\Scripts\python.exe setup_tools_windows.py --install
.\.venv\Scripts\python.exe doctor.py
```

Default/`--plan` শুধু পরিকল্পনা দেখায়; command/help চালায় না, download বা write করে না। `--install` সত্যিই সেটআপ করে, কোনো scan target নেয় না। পুরো Python installer sudo দিয়ে চালাবেন না; প্রয়োজনীয় fixed OS package-এর জন্য আলাদা sudo চায়। সমর্থিত distro/architecture/Python-এর সীমা [TOOLS.md](TOOLS.md)-তে আছে।

নতুন Nuclei engine-এর official template download হয়; আগে থেকে ready engine/template রেখে দেয়, যদি নিজে update না চান। Setup paid account বা API key তৈরি করে না। Template/provider বন্ধ বা বদলে গেলে ready tool-ও অসম্পূর্ণ ফল দিতে পারে।

শুধু dashboard ইনস্টল করতে `bash install.sh --dashboard-only` বা `.\install.ps1 -DashboardOnly` দিন। Automatic startup setup বন্ধ রাখতে `bash run.sh --no-tool-setup`, `.\run.ps1 -NoToolSetup` বা `python app.py --no-tool-setup` দিন। Browser নিজে না খুলতে আলাদা `--no-browser` / `-NoBrowser` আছে।

## ৩. Form-এর ঘরগুলো পূরণ করুন

### Primary domain / মূল ডোমেইন

এখানে অনুমোদিত domain অথবা public HTTP(S) page URL লিখুন। যেমন `https://example.com/help` দিলে HTTPX, Nuclei, Photon ও Arjun `/help` ব্যবহার করবে, আর domain-ভিত্তিক tool `example.com` ব্যবহার করবে। Query ও fragment বাদ যায়। Username, IP, wildcard ও custom port গ্রহণ করে না। Username এই tool-এর সমর্থিত target নয়।

| যা লিখলেন | গ্রহণ করবে? | কারণ |
|---|---|---|
| `example.com` | Hostname-এর format হিসেবে হ্যাঁ | নিজের অনুমোদিত domain দিয়ে বদলাবেন। |
| `app.example.com` | Hostname-এর format হিসেবে হ্যাঁ | এটি primary হলে শুধু এই নাম ও এর নিচের subdomain scope-এ রাখা যাবে। |
| `https://example.com/help` | হ্যাঁ | HTTPX, Nuclei, Photon ও Arjun path নেয়; domain tool hostname নেয়। |
| `http://example.com` | হ্যাঁ | সাধারণ HTTP URL-ও চলে। |
| `https://example.com:443/help` | হ্যাঁ | Scheme-এর standard port গ্রহণ করে। |
| `example.com:8443` | না | Custom port সমর্থিত নয়। |
| `https://name:secret@example.com` | না | Credential থাকা URL গ্রহণ করে না। |
| `*.example.com` | না | Wildcard সমর্থিত নয়। |
| `127.0.0.1`, `192.168.1.10`, `localhost` | না | IP address ও local host live target হিসেবে গ্রহণ করে না। |

Live scanner-এ hostname শুধু public IP-তে resolve করতে হবে। Private/reserved IP পাওয়া গেলে বাতিল হবে। তাই নিজের dashboard-এর localhost ঠিকানাটি target-এর ঘরে দেবেন না।

### বাড়তি অনুমোদিত host / Additional authorized hosts

Primary host target domain/URL থেকে নিজে বের হয়ে scope-এ যোগ হয়। শুধু ওই host পরীক্ষা করতে এই ঘর ফাঁকা রাখুন। অন্য অনুমোদিত host চাইলে প্রতি লাইনে hostname বা সাধারণ HTTP(S) URL দিন; শুধু hostname নেওয়া হয়। সর্বোচ্চ চারটি বাড়তি subdomain দেওয়া যায়, মোট পাঁচটি host।

Form-এর গঠন বোঝার নমুনা:

**Primary domain:**

```text
example.com
```

**Additional authorized hosts (optional):**

```text
app.example.com
```

Start দেওয়ার আগে নমুনাটি নিজের অনুমোদিত subdomain দিয়ে বদলান। Result-এ কোনো subdomain এসেছে বলেই scope-এ যোগ করবেন না; আগে মালিকানা/অনুমতি যাচাই করুন। শুধু primary পরীক্ষা করতে চাইলে বাড়তি host-এর ঘর ফাঁকা রাখুন। অন্য আলাদা domain একই run-এ যোগ করা যায় না; আলাদা assessment করতে হবে।

নতুন subdomain পাওয়া মানেই সেটিতে active scan শুরু হয় না। আবার এই input control **network firewall নয়**: বাইরের টুল DNS নতুন করে resolve করতে পারে বা অন্য service/destination-এ যোগাযোগ করতে পারে। কঠোর network সীমা দরকার হলে আলাদাভাবে isolated environment ব্যবহার করুন।

### Select checks / কোন পরীক্ষা করবেন

প্রথম তিনটি আগে থেকে selected থাকে। অন্যগুলো প্রয়োজন অনুযায়ী বেছে নিন। আপনি যে ক্রমেই box-এ click করেন, selected ধাপগুলো নিচের নির্দিষ্ট ক্রমে চলবে।

| ক্রম | Form-এর নাম / tool | এই adapter কী করে | কোন নাম পায় |
|---|---|---|---|
| ১ | DNS records — DNSRecon | সাধারণ DNS record দেখে। | Primary domain। |
| ২ | Subdomains — Subfinder | Discovery source থেকে subdomain-এর নাম সংগ্রহ করে। নতুন নাম report-এ থাকে; নিজে থেকে active target হয় না। | Primary domain। |
| ৩ | Live hosts — ProjectDiscovery HTTPX | কোন web origin সাড়া দেয় দেখে। সাড়া পাওয়া মানেই application সম্পূর্ণ সচল বা নিরাপদ নয়। | Scope-এর প্রতিটি নির্দিষ্ট host। |
| ৪ | Ports & services — Nmap | TCP connect ও সীমিত service check দিয়ে top 100 port দেখে; সব 65,535 port নয়। | Scope-এর প্রতিটি নির্দিষ্ট host। |
| ৫ | Public-source research — theHarvester | নির্ধারিত `crtsh` ও `otx` source থেকে প্রকাশ্য তথ্য দেখে। Source বন্ধ থাকলে ফলে প্রভাব পড়ে। | Primary domain। |
| ৬ | Shallow web crawl — Photon | একটি worker ও delay দিয়ে এক স্তরের crawl করে। | একই run-এ HTTPX যেসব scoped host-কে live পেয়েছে। |
| ৭ | HTTP parameters — Arjun | একটি worker ও adapter-এর সীমিত settings দিয়ে HTTP input parameter খোঁজে। | একই run-এ HTTPX যেসব scoped host-কে live পেয়েছে। |
| ৮ | Template checks — Nuclei | পাওয়া low/medium/high/critical template চালায়; নির্দিষ্ট উচ্চপ্রভাবের category বাদ থাকে এবং out-of-band interaction বন্ধ থাকে। Match হাতে যাচাই করতে হয়। | Scope-এর প্রতিটি নির্দিষ্ট host। |
| ৯ | Web-server checks — Nikto | Tuning group 1, 2, 3 ও b পরীক্ষা করে: interesting file, ভুল/default config file, তথ্য ফাঁস ও software চেনা। এগুলো active request; ফল যাচাই করতে হবে। | Scope-এর নির্দিষ্ট host-প্রতি সর্বোচ্চ একটি HTTP origin। |

Fallback চালু করতে Nuclei ও Nikto দুটোই বাছুন। Nuclei missing, unverified, timeout বা error হলে Nikto চলবে। Nuclei সফলভাবে শেষ হলেও finding না পেলে Nikto **চলবে না**। শুধু Nikto বাছলে এটি আলাদা phase হিসেবে চলে। Report-এ fallback আলাদা ধাপ হিসেবে থাকে এবং দেওয়া scope বাড়ায় না।

Photon বা Arjun বেছে নিলে একই run-এ **Live hosts / HTTPX**-ও বেছে নিন। না হলে confirmed live-host list থাকবে না; ধাপগুলো skipped হবে। Primary host-এর জন্য URL দিলে Photon/Arjun-এ তার page path যায়; অতিরিক্ত scope host-এ site root ব্যবহার হয়। দেওয়া URL-এর scheme-ই ব্যবহার হয়; ব্যর্থ হলে নিজে থেকে অন্য scheme-এ আবার চেষ্টা হয় না।

## ৪. Rate, চলার সময় ও অগ্রগতি বুঝে নিন

### Tool rate ceiling / গতি সীমা

Form-এ নিজে পূর্ণসংখ্যা লিখুন: **সেকেন্ডে ১–৫**। Default **২**। ১ দিলে যেসব adapter সেটি ব্যবহার করে, সেগুলোকে তুলনামূলক ধীর setting দেওয়া হয়। এর মানে পুরো কম্পিউটার, পুরো assessment বা প্রতিটি secondary connection মিলিয়ে সেকেন্ডে একটি request-এর নিশ্চয়তা নয়।

| Adapter | বেছে দেওয়া rate কীভাবে ব্যবহার করে |
|---|---|
| HTTPX | Request-rate setting হিসেবে দেয়; একটি worker, retry নেই। |
| Nuclei | Request-rate setting হিসেবে দেয়; concurrency ও batch size এক, retry নেই। |
| Arjun | Rate-limit setting হিসেবে দেয়; একটি worker। |
| Photon | `1 / rate` সেকেন্ড delay দেয়; একটি worker। Rate ২ হলে চাওয়া delay ০.৫ সেকেন্ড। |
| Nikto | একেক test-এর মাঝে `1 / rate` সেকেন্ড বিরতি দেয়। Rate ২ হলে চাওয়া বিরতি ০.৫ সেকেন্ড। |
| Nmap | `--max-rate` দেয়। এটি scan-packet-এর setting, সব ধরনের web request-এর সর্বজনীন সীমা নয়। সব service check বা OS/network কাজ এতে বাঁধা থাকে না। |
| DNSRecon, Subfinder, theHarvester | এই adapter-গুলোতে selected rate দেওয়া হয় না। DNS ও public provider-এর যোগাযোগ তাদের নিজস্ব আচরণ অনুযায়ী হয়। |

একেক tool একেক ধরনের কাজ গোনে। Nikto-র বিরতি একেক test-এর মাঝে; এটি সব network request গোনার কঠোর মিটার নয়। তাই এই setting **সব টুলের জন্য একটি মিটারে মাপা মোট request budget নয়**। Rate কম রাখলে traffic burst কমে, তবে run ধীর হতে পারে।

### চলার সময় ও অগ্রগতি

Dashboard থেকে **প্রতি tool বা পুরো assessment-এর সময় বেঁধে দেওয়া নেই**। Tool নিজে শেষ হবে অথবা **Stop** চাপলে থামবে। Tool/provider নিজের network error বা request timeout দিতে পারে; সেটি dashboard timer নয়। একসঙ্গে একটি assessment চলে, প্রত্যেক tool-এর output-এর সীমা আছে এবং Stop process tree বন্ধ করে।

Overall bar-এ শেষ হওয়া ও বাকি phase-এর শতাংশ দেখা যায়। প্রতিটি tool row-তে শেষ হওয়া/বাকি host attempt-এর শতাংশ ও বর্তমান attempt-এর elapsed time থাকে। Tool-এর অন্তত একটি host শেষ হলে তার গড় সময় ধরে ওই row-তে আনুমানিক বাকি সময় দেখায়। Overall estimate এই run-এর শেষ হওয়া phase দেখে হিসাব করে। দুটোই ধারণা: tool ও network-এর গতি আলাদা। অনেক command-line tool একটি host-এর ভেতরের progress percent দেয় না; UI অনুমান না করে সেটি জানায়।

কোনো tool নিজে `timeout` বা network error দিলে তার evidence পড়ুন। Dashboard-এর process time limit সরানো হয়েছে। অনুমতি ও traffic বুঝে প্রয়োজন হলে তবেই আবার চালান।

## ৫. Start ও Stop

1. Primary domain ও exact scope আবার পড়ুন। পরীক্ষা করতে চান না এমন host সরিয়ে দিন।
2. প্রয়োজনীয় check ও rate বেছে নিন।
3. মালিকানা/অনুমতির কথা সত্য হলেই confirmation দিন। Network-এর সীমাবদ্ধতা পড়ে acknowledgement দিন।
4. **Start assessment** একবার চাপুন। একই সময়ে একটি job চলতে পারে।
5. **Progress & evidence** ও **Live activity** দেখুন। শুরুতে local tool check বা DNS preflight-এর জন্য অপেক্ষা হতে পারে; সবসময় page আটকে যাওয়া নয়।
6. থামাতে **Stop** চাপুন। Cancellation শেষ হওয়া পর্যন্ত অপেক্ষা করে তারপর নতুন কাজ দিন। Linux-এ বর্তমান process group বন্ধ হয়। Windows-এ kill-on-close Job Object-এর contained process tree বন্ধ হয়; parent আগে শেষ হলেও ভেতরের child অন্তর্ভুক্ত থাকে। Containment তৈরি না হলে tool চালায় না। অস্বাভাবিক OS shutdown বা tool-এর ত্রুটিতে পরে system দেখতে হতে পারে।
7. Dashboard server বন্ধ করতে **যে Terminal থেকে চালু করেছেন সেখানে Ctrl+C** দিন। শুধু browser tab বন্ধ করলে server বা assessment থামে না।

প্রথম অনুমোদিত run-এ scope-এ শুধু primary host রাখুন, আগে থেকে selected তিনটি check রাখুন এবং rate ১ দিন। অন্য check-এর যোগাযোগ বুঝে ও অনুমতি থাকলে পরে যোগ করুন। এটি form পূরণের উদাহরণ; এই গাইড নিজে কোনো scan করে না।

## ৬. History ও report বুঝুন

Job শেষ হলে **View report**, **HTML** বা **JSON** ব্যবহার করুন। HTML report-এ একটি ধাপের ওপর click করলে প্রমাণ, diagnostic ও প্রতি host-এর record দেখা যায়। **Saved history** পুরোনো অবস্থা খোলে; নতুন scan চালায় না। Browser refresh করাও নতুন assessment নয়।

| অবস্থা | অর্থ |
|---|---|
| `pending` / `running` | ধাপের জন্য অপেক্ষা / কাজ চলছে। |
| `done` | Captured limit-এর মধ্যে command সফল exit করেছে। নিরাপত্তার সনদ নয়। |
| `missing` | প্রয়োজনীয় executable পাওয়া যায়নি। |
| `unverified` | পরিচয়/help যাচাই পাস হয়নি; প্রস্তুত tool হিসেবে ধরা হয়নি। |
| `error` | Command, parsing বা অন্য প্রয়োজনীয় কাজ ব্যর্থ হয়েছে; diagnostic পড়ুন। |
| `timeout` | কোনো tool বা provider নিজের network/request সময়সীমা জানিয়েছে; dashboard elapsed time দেখে process বন্ধ করেনি। পরীক্ষা অসম্পূর্ণ। |
| `output_limit` | Output-এর সীমা হয়েছে; সংরক্ষিত প্রমাণ অসম্পূর্ণ। |
| `skipped` | পূর্বশর্ত মেলেনি বা আগের সমস্যায় ধাপ চালানো হয়নি। |
| `cancelled` | Stop দেওয়া হয়েছে; বাকি কাজ শেষ হয়নি। |
| `interrupted` | কাজ চলার সময় server restart হয়েছে; নিজে থেকে resume হয় না। |
| `complete` | সব selected ধাপ `done` হয়েছে। Command সফল, কিন্তু সাইট নিরাপদ প্রমাণ নয়। |
| `partial` | অন্তত একটি selected ধাপ অসম্পূর্ণ বা অসফল। |

Report-এর **Selected Tools**, **Completed Phases** ও **Incomplete Phases** ধাপের সংখ্যা; যাচাই করা vulnerability-এর সংখ্যা নয়। **Automated Findings** হলো parse করা finding-এর সংখ্যা; সব নিরাপত্তা সমস্যার হিসাব নয়। Nuclei match হাতে পরীক্ষা না করা পর্যন্ত **unverified automated finding**। Nikto-র output report-এ evidence text হিসেবে থাকে, আলাদা finding হিসেবে parse হয় না। শূন্য finding-এর কারণ সীমিত coverage, template-এর সমস্যা, source বন্ধ থাকা বা এই run-এ match না পাওয়া হতে পারে।

Report-এর **Tool execution time** scanner-এর record করা সময়ের যোগফল। আপনি মোট যতক্ষণ অপেক্ষা করেছেন তার সমান নয়; help check ও DNS-এর overhead এতে নেই। Report-এর timestamp UTC-তে থাকে; dashboard আপনার browser-এর স্থানীয় সময় দেখাতে পারে।

History ও raw evidence project-এর private `data/`-তে থাকে। কিছু secret আড়াল হলেও সংবেদনশীল তথ্য থাকতে পারে। Share করার আগে পড়ুন; আসল report বা secret GitHub-এ দেবেন না। Demo তৈরির ব্যবস্থা সরানো হয়েছে। পুরোনো saved demo মুছতে [README-এর stopped-server maintenance নির্দেশনা](../README.bn.md#আগের-সংস্করণের-saved-demo-মুছতে) অনুসরণ করুন।

## দ্রুত সমস্যা খুঁজুন

| সমস্যা | আগে যা দেখবেন |
|---|---|
| Target URL গ্রহণ হচ্ছে না | Domain অথবা public `http://` / `https://` URL দিন। Username/password, IP, wildcard বা standard নয় এমন port গ্রহণ করা হয় না। |
| Scope বাতিল | সর্বোচ্চ চারটি বাড়তি host দিন; প্রতিটি primary host-এর exact subdomain হতে হবে। Primary host নিজে থেকে যোগ হয়। |
| Non-public DNS error | এই live mode private/reserved target address নেয় না। |
| Setup-এর পরেও missing | একই Kali-তে ইনস্টল হয়েছে কি না ও PATH দেখুন। Recheck করুন; PATH বদলালে restart দিন। |
| HTTPX unverified | ProjectDiscovery HTTPX কি না দেখুন; Python HTTPX আলাদা। |
| Photon/Arjun skipped | একই run-এ HTTPX বেছে নিন এবং live-host result পড়ুন। |
| Timeout/partial | ব্যর্থ ধাপ ও প্রতি host-এর diagnostic পড়ুন; নিরাপদ বলে সিদ্ধান্ত দেবেন না। |
| Server restart | নতুন session-এর জন্য dashboard reload করুন। Interrupted কাজ নিজে থেকে resume হয় না। |

