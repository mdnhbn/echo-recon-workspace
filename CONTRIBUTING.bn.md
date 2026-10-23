# Echo Recon-এ অবদান রাখুন

Student, classmate এবং অন্য contributor—সবাই code, test, বাংলা অনুবাদ ও documentation উন্নত করার প্রস্তাব দিতে পারেন। শুরুতেই expert হতে হবে না।

[English guide](CONTRIBUTING.md) · [আচরণবিধি](CODE_OF_CONDUCT.md) · [নিরাপত্তার সীমাবদ্ধতা](SECURITY.md)

## Fork ও Pull Request কী?

**Fork** হলো আপনার GitHub account-এ project-এর একটি copy। সেখানে পরিবর্তন করে **Pull Request (PR)** পাঠালে maintainer তা দেখে মূল project-এ যুক্ত করার সিদ্ধান্ত নেন। সবাই PR পাঠাতে পারেন; public repository মানে সবাই সরাসরি `main` branch বদলাতে পারবেন—এমন নয়।

ছোট বানান ভুল ঠিক করতে GitHub-এ ফাইল খুলে pencil/edit বোতাম ব্যবহার করতে পারেন। GitHub-এর ধাপ অনুসরণ করে পরিবর্তনের প্রস্তাব দিন। বড় পরিবর্তনের জন্য নিচের পদ্ধতি ব্যবহার করুন।

## প্রথম পরিবর্তন পাঠানোর ধাপ

1. [বাংলা README](README.bn.md), [architecture](docs/ARCHITECTURE.md) এবং [নিরাপত্তা নির্দেশনা](SECURITY.md) পড়ুন।
2. একই কাজ নিয়ে issue বা PR আছে কি না দেখুন। বড় feature হলে আগে issue খুলে আলোচনা করুন। ছোট documentation সংশোধন সরাসরি PR করা যায়।
3. [মূল repository](https://github.com/mdnhbn/echo-recon-workspace)-তে **Fork** চাপুন।
4. আপনার fork ডাউনলোড করুন। `YOUR-USERNAME`-এর জায়গায় নিজের GitHub username দিন:

   ```bash
   git clone https://github.com/YOUR-USERNAME/echo-recon-workspace.git
   cd echo-recon-workspace
   git switch -c improve-install-guide
   ```

5. নিজের operating system অনুযায়ী README দেখে dashboard ইনস্টল করুন। সাধারণ user এবং project-এর `.venv` ব্যবহার করুন।
6. একটি নির্দিষ্ট বিষয় ঠিক করুন। সম্ভব হলে English ও বাংলা নির্দেশনা একসঙ্গে আপডেট করুন; অনুবাদে সাহায্য চাইতে পারেন।
7. নিচের পরীক্ষা চালান। `git diff` দিয়ে পরিবর্তন দেখুন। নিজের report, password, token, `.venv` বা scanner binary commit করবেন না।
8. পরিবর্তন save করে নিজের fork-এ পাঠান:

   ```bash
   git add path/to/changed-file
   git commit -m "Clarify installation instructions"
   git push -u origin improve-install-guide
   ```

   উদাহরণের file path ও branch name নিজের কাজ অনুযায়ী বদলান। শুধু প্রয়োজনীয় ফাইল add করুন।

9. GitHub-এ নিজের fork খুলে **Compare & pull request** চাপুন। destination হবে `mdnhbn/echo-recon-workspace`-এর `main` branch।
10. কী সমস্যা ছিল, কী বদলেছেন এবং কীভাবে পরীক্ষা করেছেন লিখুন। Maintainer-এর review অনুযায়ী একই branch-এ নতুন commit দিলে PR আপডেট হবে।

অন্যের কাজ force-push বা delete করবেন না। Conflict বুঝতে না পারলে সাহায্য চান; না বুঝে reset করবেন না।

## পরীক্ষা

আগে dashboard-এর dependency ইনস্টল করুন। Repository folder থেকে চালান। এই test-এর জন্য বাইরের scanner প্রয়োজন নেই।

Kali / Linux:

```bash
.venv/bin/python -m unittest discover -s tests -v
bash -n install.sh run.sh
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Test-এ mock scanner output, নকল DNS result, offline demo ও local process ব্যবহার করুন। Public website, আসল password বা paid service-এর ওপর test নির্ভর করবে না। UI বদলালে offline demo এবং report দেখুন। কোনো operating system-এ পরীক্ষা না করলে সেটি স্পষ্ট লিখুন।

## কাজ করার সময় খেয়াল রাখুন

- ছোট, সহজে review করা যায় এমন পরিবর্তন করুন এবং কারণ লিখুন।
- সাধারণ user, local dashboard ও অনুমোদিত scope-এর নিয়ন্ত্রণ রাখুন।
- Tool ব্যর্থ বা অসম্পূর্ণ হলে সেই অবস্থা দেখাতে হবে। Finding-কে যাচাই ছাড়া নিশ্চিত vulnerability বলবেন না।
- User input দিয়ে shell command string বানাবেন না। গুরুত্বপূর্ণ bug fix-এর জন্য regression test দিন।
- Portable path ও Python API ব্যবহার করুন। Linux-only সুবিধার Windows/WSL বিকল্প বা সীমাবদ্ধতা লিখুন।
- Scanner optional রাখুন। অনুমতি ছাড়া অতিরিক্ত tool download বা চালু করবেন না।
- Screenshot ও উদাহরণে নকল তথ্য ব্যবহার করুন। Secret ও ব্যক্তিগত তথ্য প্রকাশ করবেন না।

সহজ শুরুর কাজ: বানান সংশোধন, পরিষ্কার error message, বাংলা অনুবাদ, form-এর label অথবা জানা bug-এর test।

## Bug ও feature প্রস্তাব

GitHub-এর **Issues → New issue** থেকে template বেছে নিন। Operating system, Python/tool version, সমস্যা ঘটানোর ধাপ এবং প্রত্যাশিত/আসল ফল লিখুন। Windows হলে native নাকি WSL—জানান। নিরাপত্তাসংক্রান্ত সংবেদনশীল বিষয় হলে [SECURITY.md](SECURITY.md) অনুসরণ করুন; public issue-তে secret বা আসল target report দেবেন না।

## Credit ও license

মূল লেখক **Ahammed / Auto-Recon**-এর credit এবং [NOTICE.md](NOTICE.md) রাখুন। অন্যের কাজ নিজের বলে লিখবেন না। নিজের তৈরি বা share করার অনুমতি আছে এমন লেখা/code দিন; third-party code হলে source ও license জানান।

Maintainer-এর নির্দেশে project-এ **[MIT License](LICENSE)** ব্যবহার করা হচ্ছে। Contribution পাঠালে আপনার পরিবর্তনও project-এর MIT License-এর অধীনে দেওয়ার সম্মতি দিচ্ছেন। Software বা তার উল্লেখযোগ্য অংশ অন্যদের দেওয়ার সময় copyright ও permission notice রাখুন। আলাদা contributor license agreement (CLA) প্রয়োজন নেই। Third-party tool ও dependency-এর নিজস্ব license প্রযোজ্য থাকবে।
