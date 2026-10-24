# Echo Recon ব্যবহার করবেন যেভাবে

**[English guide](USAGE.md)** · [ইনস্টল](../README.bn.md) · [টুল সেটআপ](TOOLS.md) · [Windows / WSL](WINDOWS.md)

Echo Recon একটি স্থানীয় dashboard। এটি নির্দিষ্ট ক্রমে আটটি আলাদা টুল চালায় এবং তাদের প্রমাণ রিপোর্টে রাখে। Dashboard খুললেই scan শুরু হয় না। এই গাইডে `example.com` শুধু form বোঝানোর নমুনা: **নিজের বা স্পষ্ট অনুমতি থাকা domain দিয়ে এটি বদলাবেন। নমুনা ঠিকানাগুলোতে Start চাপবেন না।**

## ১. Dashboard খুলুন

Kali-র Terminal থেকে নিজের ইনস্টল করা project folder-এ গিয়ে চালান:

```bash
cd ~/Tools/02-Custom/echo-recon-workspace
bash run.sh
```

Terminal খোলা রাখুন। Firefox-এ **http://127.0.0.1:8001** খোলার কথা। না খুললে নিজে ঠিকানাটি লিখুন। এটি আপনার নিজের Kali-র dashboard-এর ঠিকানা; assessment form-এ যে domain লিখবেন, এটি সেই domain নয়।

সাধারণ user দিয়ে চালান; dashboard চালাতে root লাগে না। সরাসরি Windows-এ dashboard, সংরক্ষিত history ও report দেখা যায়। আটটি টুলের পুরো workflow চালাতে **Kali WSL2** ব্যবহার করুন। বিস্তারিত [WINDOWS.md](WINDOWS.md)।

### দুই ধরনের layout বদলাবেন যেভাবে

Header-এর **Light layout / হালকা** চাপলে dashboard-এর হালকা layout খুলবে। এরপর বোতামে **Dark layout / ডার্ক** লেখা থাকবে; আবার চাপলে dark layout ফিরবে। বোতামে পরের যে layout খুলবে তার নাম লেখা থাকে, বর্তমান layout-এর নাম নয়।

Layout বদলালে form-এ লেখা নাম, চলমান job ও দেখানো ফল একই জায়গায় থাকে। Browser-এর local storage চালু থাকলে এই dashboard address-এর জন্য পছন্দটি একই browser-এ মনে রাখে। নতুন browser/profile, storage পরিষ্কার করা বা storage বন্ধ থাকলে default dark layout আসতে পারে। একই address-এর আরেকটি tab খোলা থাকলে browser storage event সমর্থিত অবস্থায় সেটিও সংরক্ষিত পছন্দ অনুসরণ করে।

দুই layout-এই background-এর matrix animation আছে; reduced-motion preference থাকলে animation বন্ধ থাকে। এই বোতাম dashboard-এর চেহারা বদলায়, scan setting নয়। App-এর ভেতরে নির্দেশনা দেখতে header-এর **How to use / ব্যবহারবিধি** অথবা sidebar-এর **Full usage guide / বিস্তারিত নিয়ম** চাপুন।

## ২. টুল আছে কি না দেখুন এবং সেটআপ করুন

1. **Check installed tools** চাপুন। পরিচয়/help যাচাই শেষ হওয়া পর্যন্ত অপেক্ষা করুন।
2. প্রতিটি টুলের অবস্থা পড়ুন:

   | অবস্থা | অর্থ | কী করবেন |
   |---|---|---|
   | `ready` | উপযুক্ত executable-এর পরিচয়/help যাচাই পাস করেছে। | প্রয়োজন হলে check বেছে নিতে পারেন; এটি সম্পূর্ণ compatibility test নয়। |
   | `missing` | Server-এর PATH-এ executable পাওয়া যায়নি। | Dashboard যে Kali-তে চলছে, সেই Kali-তেই tool সেটআপ করুন। |
   | `unverified` | Program আছে, কিন্তু পরিচয় বা প্রয়োজনীয় help flag মেলেনি। | আগে version ও PATH দেখুন; আবার ইনস্টল করা নাও লাগতে পারে। |

3. **Download / Setup tools** চাপলে আটটি টুলের official source ও setup guide পাবেন। Missing/unverified টুলের row-তেও setup shortcut আছে।
4. সমর্থিত Kali desktop-এ **Setup all tools** চাপলে project-এর নির্দিষ্ট installer একটি স্থানীয় Terminal-এ খুলবে। কী করতে বলছে পড়ে তারপর এগোন। Administrator অনুমতি প্রয়োজন হলে sudo password **শুধু ওই Terminal-এ** লিখুন; dashboard বা chat-এ নয়। Password লেখার সময় অক্ষর দেখা না যাওয়া স্বাভাবিক।
5. Installer সফল বা ব্যর্থ হওয়ার বার্তা না দেওয়া পর্যন্ত Terminal খোলা রাখুন। Terminal খুলেছে মানেই সব tool ইনস্টল হয়েছে নয়। Source download হওয়া আর ব্যবহারযোগ্য program ইনস্টল হওয়া আলাদা কাজ।
6. Terminal নিজে থেকে না খুললে, অথবা desktop ছাড়া Windows/WSL ব্যবহার করলে, নিচের নির্দিষ্ট command ও [TOOLS.md](TOOLS.md) অনুসরণ করে Kali Terminal-এ কাজ করুন। Windows-এ tool ইনস্টল করলেই Linux adapter Windows-এ কাজ করবে না।
7. শেষে **Check installed tools** আবার চাপুন। Shell-এর PATH বা environment বদলালে dashboard বন্ধ করে আবার চালিয়ে check করুন। যেটুকু পরীক্ষা প্রয়োজন, সেটুকুই বেছে নিন; tool ইনস্টল থাকলেই সবগুলো চালাতে হবে না।

**HTTPX নিয়ে খেয়াল করুন:** এখানে **ProjectDiscovery HTTPX** লাগে। Python HTTPX আলাদা program, যদিও নাম এক। সমস্যা মেটাতে Python HTTPX মুছবেন না বা `/usr/bin/httpx` overwrite করবেন না; টুল গাইড দেখুন।

Nuclei-র উপযুক্ত template-ও লাগবে। কিছু বাইরের data provider বন্ধ থাকতে পারে বা আলাদা account configuration চাইতে পারে। Tool setup আপনার জন্য paid account বা API key তৈরি করে না।

### Desktop ছাড়া Kali / Kali WSL-এর command

নিজের **Kali Terminal** খুলুন। ইনস্টল করা repository-তে গিয়ে আগে নির্দিষ্ট plan দেখুন:

```bash
cd ~/Tools/02-Custom/echo-recon-workspace
.venv/bin/python setup_tools.py --plan
```

`--plan` শুধু স্থানীয় path পড়ে setup-এর পরিকল্পনা দেখায়। কোনো command বা tool help চালায় না, download/install/scan করে না। শুধু path দেখালেই readiness check পাস হয়েছে বোঝায় না।

পরিবর্তন করতে প্রস্তুত হলে চলমান assessment আগে শেষ বা বন্ধ করুন। তারপর দিন:

```bash
.venv/bin/python setup_tools.py --install
```

`--install` সত্যিই নির্দিষ্ট installation workflow শুরু করে; এটি শুধু plan দেখানো নয়। আগে tool যাচাই করে, check পাস করা tool বাদ রাখে এবং যেগুলোতে setup প্রয়োজন সেগুলো নিয়ে কাজ করে। নির্দিষ্ট Kali package-এর জন্য ওই interactive Terminal-এ sudo চাইতে পারে। Python command সাধারণ user দিয়ে দিন, **`sudo python` দিয়ে নয়**। একই সঙ্গে একাধিক installer চালাবেন না। Error হলে পড়ে তারপর retry করুন; অন্য project-এর existing launcher নিজে থেকে overwrite করবে না।

নতুন করে Nuclei engine ইনস্টল হলে official template-ও download হয়। আগে থেকে ready Nuclei ও তার template default অবস্থায় রেখে দেয়। Setup শেষে installer Terminal বন্ধ করুন। Environment বদলালে dashboard restart করুন এবং **Check installed tools** আবার চাপুন। এই installer command-এ scan target দেওয়া যায় না; assessment চালায় না। Windows হলে command দেওয়ার আগে Kali WSL-এর মধ্যে ঢুকুন। `--install` Kali-র জন্য; সরাসরি Windows বা যেকোনো Linux distribution-এর জন্য নয়।

## ৩. Form-এর ঘরগুলো পূরণ করুন

### Primary domain / মূল ডোমেইন

এখানে শুধু hostname লিখবেন। অর্থাৎ এই assessment-এর মূল নাম। নিচে বোঝানোর জন্য `example.com` ব্যবহার করা হয়েছে।

| যা লিখলেন | গ্রহণ করবে? | কারণ |
|---|---|---|
| `example.com` | Hostname-এর format হিসেবে হ্যাঁ | নিজের অনুমোদিত domain দিয়ে বদলাবেন। |
| `app.example.com` | Hostname-এর format হিসেবে হ্যাঁ | এটি primary হলে শুধু এই নাম ও এর নিচের subdomain scope-এ রাখা যাবে। |
| `https://example.com` | না | URL-এর scheme আছে। |
| `example.com/login` | না | Page path আছে। |
| `example.com:443` | না | Port লেখা আছে। |
| `*.example.com` | না | Wildcard সমর্থিত নয়। |
| `127.0.0.1`, `192.168.1.10`, `localhost` | না | IP address ও local host live target হিসেবে গ্রহণ করে না। |

Live scanner-এ hostname শুধু public IP-তে resolve করতে হবে। Private/reserved IP পাওয়া গেলে বাতিল হবে। তাই নিজের dashboard-এর localhost ঠিকানাটি target-এর ঘরে দেবেন না।

### Exact authorized hosts / অনুমোদিত host

এটি সেই **নির্দিষ্ট hostname-এর তালিকা, যেগুলো active check-কে দিতে অনুমতি দিচ্ছেন**। প্রতি লাইনে একটি নাম দিন। Primary domain-টিও থাকতে হবে। **সর্বোচ্চ পাঁচটি entry** দেওয়া যায়। বাড়তি নামগুলো primary domain-এর subdomain হতে হবে।

Form-এর গঠন বোঝার নমুনা:

**Primary domain:**

```text
example.com
```

**Exact authorized hosts:**

```text
example.com
app.example.com
```

Start দেওয়ার আগে দুই জায়গার নমুনা বদলে নিজের অনুমোদিত নাম দিন। Result-এ কোনো subdomain এসেছে বলেই scope-এ যোগ করবেন না; আগে মালিকানা/অনুমতি যাচাই করুন। শুধু primary পরীক্ষা করতে চাইলে scope-এ শুধু সেই একটি লাইন দিন। অন্য আলাদা domain একই run-এ যোগ করা যায় না; আলাদা assessment করতে হবে।

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

Photon বা Arjun বেছে নিলে একই run-এ **Live hosts / HTTPX**-ও বেছে নিন। না হলে confirmed live-host list থাকবে না; ধাপগুলো skipped হবে। বর্তমান Photon/Arjun adapter `https://HOST`-এর মূল ঠিকানা ব্যবহার করে। আলাদা page path দেওয়া যায় না এবং HTTPS ব্যর্থ হলে নিজে থেকে HTTP-তে বদলায় না। HTTPX শুধু HTTP-তে সাড়া পেলেও এই HTTPS check সফল হবে—এমন নিশ্চয়তা নেই।

## ৪. Rate ও সময়সীমা বুঝে নিন

### Tool rate ceiling / গতি সীমা

Form-এ **সেকেন্ডে ১, ২ বা ৫** বেছে নেওয়া যায়। Default **২**। ১ দিলে যেসব adapter সেটি ব্যবহার করে, সেগুলোকে তুলনামূলক ধীর setting দেওয়া হয়। এর মানে পুরো কম্পিউটার, পুরো assessment বা প্রতিটি secondary connection মিলিয়ে সেকেন্ডে একটি request-এর নিশ্চয়তা নয়।

| Adapter | বেছে দেওয়া rate কীভাবে ব্যবহার করে |
|---|---|
| HTTPX | Request-rate setting হিসেবে দেয়; একটি worker, retry নেই। |
| Nuclei | Request-rate setting হিসেবে দেয়; concurrency ও batch size এক, retry নেই। |
| Arjun | Rate-limit setting হিসেবে দেয়; একটি worker। |
| Photon | `1 / rate` সেকেন্ড delay দেয়; একটি worker। Rate ২ হলে চাওয়া delay ০.৫ সেকেন্ড। |
| Nmap | `--max-rate` দেয়। এটি scan-packet-এর setting, সব ধরনের web request-এর সর্বজনীন সীমা নয়। সব service check বা OS/network কাজ এতে বাঁধা থাকে না। |
| DNSRecon, Subfinder, theHarvester | এই adapter-গুলোতে selected rate দেওয়া হয় না। DNS ও public provider-এর যোগাযোগ তাদের নিজস্ব আচরণ অনুযায়ী হয়। |

একেক tool একেক ধরনের কাজ গোনে। তাই এই setting **সব টুলের জন্য একটি মিটারে মাপা মোট request budget নয়**। খুব কম rate বা অল্প সময় দিলে পরীক্ষা অসম্পূর্ণ থাকতে পারে।

### Time per tool / host / প্রতি টুল-হোস্টের সময়

Form-এ **৩০, ৬০, ১২০ বা ১৮০ সেকেন্ড** পাওয়া যায়; default **১২০ সেকেন্ড**। এটি **একটি host-এর জন্য একটি tool চালানোর process-এর সময়সীমা**। পুরো assessment-এর মোট সময়সীমা নয়।

যেমন, ১২০ সেকেন্ড বেছে নিলে প্রথম scoped host-এর HTTPX নিজের সময় পায়। দ্বিতীয় host-এর HTTPX আবার আলাদা সময় পায়। এরপর অন্য selected tool নিজের সময় পায়। কিছু tool-এর ভেতরে আরও ছোট connection/request timeout আছে; তাই কোনো request আগেও ব্যর্থ হতে পারে।

ধাপ ও তাদের host-গুলো একটির পরে আরেকটি চলে। সব কাজ মিলে একটি ১২০-সেকেন্ডের timer ভাগ করে না।

- সহজ বড়সড় হিসাব: `৮ টুল × ৫ host × ১২০ সেকেন্ড = ৪,৮০০ সেকেন্ড`, অর্থাৎ **৮০ মিনিট** process allowance। বর্তমান pipeline-এ এই হিসাব বেশি হয়ে যায়, কারণ তিনটি tool শুধু primary domain-এ চলে।
- বর্তমান code-এ আটটি check ও পাঁচটি উপযুক্ত host থাকলে সর্বোচ্চ `৩ + (৫ × ৫) = ২৮` বার scanner process চলে। তাই `২৮ × ১২০ = ৩,৩৬০ সেকেন্ড`, অর্থাৎ **৫৬ মিনিট** scanner allowance। Photon/Arjun কম host পেতে পারে বা skipped হতে পারে।
- কোনো হিসাবই ঘড়ি ধরে মোট সময়ের কঠোর সীমা বা আপনার run-এর নিশ্চিত সময় নয়। পরিচয়/help check, বারবার DNS preflight, process খোলা/বন্ধ করা, provider ও অন্যান্য overhead-এ আরও সময় লাগে। DNS lookup scanner process-এর timer-এর মধ্যে নয়। অনেক tool আগেই শেষ হবে, ব্যর্থ হবে বা missing থাকবে। আলাদা whole-job deadline নেই।

কোনো process সময়সীমা পেরোলে সেটি বন্ধ করে **timeout** লেখা হয়। এর অর্থ **পরীক্ষা অসম্পূর্ণ**; “দুর্বলতা নেই” বা “সাইট নিরাপদ” নয়। অন্য selected ধাপ চলতে পারে। সব selected ধাপ সফলভাবে শেষ না হলে সাধারণত পুরো job **partial** হয়। Pipeline-এর গুরুতর সমস্যায় পুরো job **error**-ও হতে পারে। সময় বাড়ালে বেশি সময় পাবে; কিন্তু missing tool, ভুল scope বা বন্ধ provider ঠিক হবে না।

## ৫. Start ও Stop

1. Primary domain ও exact scope আবার পড়ুন। পরীক্ষা করতে চান না এমন host সরিয়ে দিন।
2. প্রয়োজনীয় check, rate ও প্রতি tool/host-এর সময় বেছে নিন।
3. মালিকানা/অনুমতির কথা সত্য হলেই confirmation দিন। Network-এর সীমাবদ্ধতা পড়ে acknowledgement দিন।
4. **Start assessment** একবার চাপুন। একই সময়ে একটি job চলতে পারে।
5. **Progress & evidence** ও **Live activity** দেখুন। শুরুতে local tool check বা DNS preflight-এর জন্য অপেক্ষা হতে পারে; সবসময় page আটকে যাওয়া নয়।
6. থামাতে **Stop** চাপুন। Cancellation শেষ হওয়া পর্যন্ত অপেক্ষা করে তারপর নতুন কাজ দিন। Linux-এ বর্তমান process group বন্ধের অনুরোধ যায়। অস্বাভাবিকভাবে বন্ধ হলে বা child process আলাদা হয়ে গেলে পরে system দেখতে হতে পারে।
7. Dashboard server বন্ধ করতে **যে Terminal থেকে চালু করেছেন সেখানে Ctrl+C** দিন। শুধু browser tab বন্ধ করলে server বা assessment থামে না।

প্রথম অনুমোদিত run-এ scope-এ শুধু primary host রাখুন, আগে থেকে selected তিনটি check রাখুন, rate ১ ও সময় ১২০ সেকেন্ড দিন। অন্য check-এর যোগাযোগ বুঝে ও অনুমতি থাকলে পরে যোগ করুন। এটি form পূরণের উদাহরণ; এই গাইড নিজে কোনো scan করে না।

## ৬. History ও report বুঝুন

Job শেষ হলে **View report**, **HTML** বা **JSON** ব্যবহার করুন। HTML report-এ একটি ধাপের ওপর click করলে প্রমাণ, diagnostic ও প্রতি host-এর record দেখা যায়। **Saved history** পুরোনো অবস্থা খোলে; নতুন scan চালায় না। Browser refresh করাও নতুন assessment নয়।

| অবস্থা | অর্থ |
|---|---|
| `pending` / `running` | ধাপের জন্য অপেক্ষা / কাজ চলছে। |
| `done` | Captured limit-এর মধ্যে command সফল exit করেছে। নিরাপত্তার সনদ নয়। |
| `missing` | প্রয়োজনীয় executable পাওয়া যায়নি। |
| `unverified` | পরিচয়/help যাচাই পাস হয়নি; প্রস্তুত tool হিসেবে ধরা হয়নি। |
| `error` | Command, parsing বা অন্য প্রয়োজনীয় কাজ ব্যর্থ হয়েছে; diagnostic পড়ুন। |
| `timeout` | একটি tool process নিজের সময়সীমা পেরিয়েছে; পরীক্ষা অসম্পূর্ণ। |
| `output_limit` | Output-এর সীমা হয়েছে; সংরক্ষিত প্রমাণ অসম্পূর্ণ। |
| `skipped` | পূর্বশর্ত মেলেনি বা আগের সমস্যায় ধাপ চালানো হয়নি। |
| `cancelled` | Stop দেওয়া হয়েছে; বাকি কাজ শেষ হয়নি। |
| `interrupted` | কাজ চলার সময় server restart হয়েছে; নিজে থেকে resume হয় না। |
| `complete` | সব selected ধাপ `done` হয়েছে। Command সফল, কিন্তু সাইট নিরাপদ প্রমাণ নয়। |
| `partial` | অন্তত একটি selected ধাপ অসম্পূর্ণ বা অসফল। |

Report-এর **Selected Tools**, **Completed Phases** ও **Incomplete Phases** ধাপের সংখ্যা; যাচাই করা vulnerability-এর সংখ্যা নয়। **Automated Findings** হলো parse করা finding-এর সংখ্যা; সব নিরাপত্তা সমস্যার হিসাব নয়। Nuclei match হাতে পরীক্ষা না করা পর্যন্ত **unverified automated finding**। শূন্য finding-এর কারণ সীমিত coverage, template-এর সমস্যা, source বন্ধ থাকা বা এই run-এ match না পাওয়া হতে পারে।

Report-এর **Tool execution time** scanner-এর record করা সময়ের যোগফল। আপনি মোট যতক্ষণ অপেক্ষা করেছেন তার সমান নয়; help check ও DNS-এর overhead এতে নেই। Report-এর timestamp UTC-তে থাকে; dashboard আপনার browser-এর স্থানীয় সময় দেখাতে পারে।

History ও raw evidence project-এর private `data/`-তে থাকে। কিছু secret আড়াল হলেও সংবেদনশীল তথ্য থাকতে পারে। Share করার আগে পড়ুন; আসল report বা secret GitHub-এ দেবেন না। Demo তৈরির ব্যবস্থা সরানো হয়েছে। পুরোনো saved demo মুছতে [README-এর stopped-server maintenance নির্দেশনা](../README.bn.md#আগের-সংস্করণের-saved-demo-মুছতে) অনুসরণ করুন।

## দ্রুত সমস্যা খুঁজুন

| সমস্যা | আগে যা দেখবেন |
|---|---|
| “Enter a hostname” | `https://`, path, port, wildcard বা IP সরিয়ে শুধু hostname দিন। |
| “Primary domain must appear” | Scope তালিকায় primary নামটি হুবহু রাখুন। |
| Scope বাতিল | সর্বোচ্চ পাঁচটি host দিন; প্রতিটি primary বা তার exact subdomain হবে। |
| Non-public DNS error | এই live mode private/reserved target address নেয় না। |
| Setup-এর পরেও missing | একই Kali-তে ইনস্টল হয়েছে কি না ও PATH দেখুন। Recheck করুন; PATH বদলালে restart দিন। |
| HTTPX unverified | ProjectDiscovery HTTPX কি না দেখুন; Python HTTPX আলাদা। |
| Photon/Arjun skipped | একই run-এ HTTPX বেছে নিন এবং live-host result পড়ুন। |
| Timeout/partial | ব্যর্থ ধাপ ও প্রতি host-এর diagnostic পড়ুন; নিরাপদ বলে সিদ্ধান্ত দেবেন না। |
| Server restart | নতুন session-এর জন্য dashboard reload করুন। Interrupted কাজ নিজে থেকে resume হয় না। |

