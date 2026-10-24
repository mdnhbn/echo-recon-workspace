# Kali APT updates for Echo Recon

**English** · [বাংলা](#kali-তে-apt-দিয়ে-echo-recon-আপডেট)

This project is normally installed from a Git checkout. APT does not update that checkout. The signed APT feed is live and installs Echo Recon as a Debian package. After adding the feed and installing the package once, `sudo apt update && sudo apt upgrade` updates Echo Recon when a newer signed release is published.

APT receives **published release tags**, not every Git commit. The initial signed package is already published in the [`apt-repo` branch](https://github.com/mdnhbn/echo-recon-workspace/tree/apt-repo). For each later release, the maintainer bumps the project version and pushes the matching `vX.Y.Z` tag. That tag starts the release workflow, which builds an architecture-independent `.deb`, publishes it in `apt-repo`, and signs the repository indexes. A push to `main` alone does not change the APT feed. Never bypass signature verification with `trusted=yes`.

## Maintainer: configure the signing key once

Create and keep the archive key under the repository owner's control. On Kali or another Linux machine:

```bash
sudo apt install gnupg
gpg --full-generate-key
```

Choose an RSA signing key of at least 3072 bits and set a strong passphrase. Then find its complete fingerprint:

```bash
gpg --list-secret-keys --keyid-format long
```

Export the **private key** locally, substituting the full fingerprint:

```bash
gpg --armor --export-secret-keys FULL_FINGERPRINT > echo-recon-apt-private.asc
```

In the GitHub repository's **Settings → Secrets and variables → Actions**:

- Add secret `APT_REPO_SIGNING_KEY` with the complete contents of the `.asc` file.
- Add secret `APT_REPO_SIGNING_PASSPHRASE` with the key passphrase.
- Add variable `APT_REPO_SIGNING_FINGERPRINT` with the full fingerprint, with no spaces.

Keep a protected backup of the private key. Do not commit it or send it in chat. The release workflow checks that the secret key matches the public fingerprint variable before publishing. After the first signed release, the public key and fingerprint appear in the generated `apt-repo` branch.

For every later package release, update `echo_recon/__init__.py` to the new version, commit the release changes, then push the matching tag (for example, version `6.7.0` uses tag `v6.7.0`). The workflow validates, builds, signs, and publishes the package automatically. Confirm the workflow succeeds before telling Kali users to upgrade.

## Kali user: add the feed and install

Supported architectures are `amd64` and `arm64`. The signed feed already contains its public key and initial package. Download and inspect the public key once on each Kali installation:

```bash
BASE=https://raw.githubusercontent.com/mdnhbn/echo-recon-workspace/apt-repo
curl -fsSLo /tmp/echo-recon-archive-keyring.gpg "$BASE/archive-keyring.gpg"
gpg --show-keys --with-fingerprint /tmp/echo-recon-archive-keyring.gpg
cat <(curl -fsSL "$BASE/KEY-FINGERPRINT.txt")
```

Check that the two fingerprints match the `APT_REPO_SIGNING_FINGERPRINT` variable in the GitHub repository settings before trusting the key. Then install the key and source:

```bash
sudo install -d -m 0755 /etc/apt/keyrings
sudo install -m 0644 /tmp/echo-recon-archive-keyring.gpg /etc/apt/keyrings/echo-recon.gpg
printf 'deb [signed-by=/etc/apt/keyrings/echo-recon.gpg] %s stable main\n' "$BASE" \
  | sudo tee /etc/apt/sources.list.d/echo-recon.list >/dev/null
sudo apt update
sudo apt install echo-recon
```

Start it as your ordinary user with `echo-recon`. The desktop menu also gets an **Echo Recon** entry. Do not run the dashboard as root. Package files are read-only under `/usr/lib`; report history and evidence are kept under `~/.local/share/echo-recon`, so normal package upgrades preserve them. The scanner backends remain user-local and are managed by Echo Recon's existing setup flow.

### Move saved history from the Git checkout

If you already have reports under `~/Tools/02-Custom/echo-recon-workspace/data`, stop its dashboard first. Keep a private backup, then copy the saved SQLite files before opening the APT-installed version:

```bash
mkdir -p ~/.local/share/echo-recon
cp -a ~/Tools/02-Custom/echo-recon-workspace/data/history.sqlite3* ~/.local/share/echo-recon/
chmod 700 ~/.local/share/echo-recon
chmod 600 ~/.local/share/echo-recon/history.sqlite3*
```

If the checkout is in another folder, replace that path. Keep the old checkout until the new dashboard shows your saved reports. Use `echo-recon` after migration; `bash run.sh` continues to launch the separate source checkout, which APT does not update.

## Kali-তে APT দিয়ে Echo Recon আপডেট

GitHub থেকে clone করা source install-এ `apt update` বা `apt upgrade` code বদলায় না। Signed APT feed-টি এখন চালু আছে। Kali-তে feed ও `echo-recon` package একবার বসানোর পর নতুন signed release এলে `sudo apt update && sudo apt upgrade` Echo Recon-সহ system package update করবে।

APT-তে **প্রকাশিত release tag**-গুলো যায়; `main`-এর প্রতিটি commit নয়। প্রথম signed package [`apt-repo` branch](https://github.com/mdnhbn/echo-recon-workspace/tree/apt-repo)-এ আছে। পরের release-এর জন্য version বাড়িয়ে মেলা `vX.Y.Z` tag push করলে workflow package তৈরি, sign ও publish করে। `main`-এ commit push করলেই APT feed বদলায় না। Signature এড়াতে `trusted=yes` ব্যবহার করবেন না।

### Maintainer: signing key একবার configure করুন

Repository owner-এর নিয়ন্ত্রণে থাকা signing key Kali বা Linux-এ তৈরি করুন:

```bash
sudo apt install gnupg
gpg --full-generate-key
```

কমপক্ষে 3072-bit RSA key এবং শক্ত passphrase বেছে নিন। Fingerprint দেখুন:

```bash
gpg --list-secret-keys --keyid-format long
```

পূর্ণ fingerprint বসিয়ে private key নিজের মেশিনে export করুন:

```bash
gpg --armor --export-secret-keys FULL_FINGERPRINT > echo-recon-apt-private.asc
```

GitHub repository-এর **Settings → Secrets and variables → Actions**-এ:

- `APT_REPO_SIGNING_KEY` secret-এ `.asc` ফাইলের পুরো লেখা দিন।
- `APT_REPO_SIGNING_PASSPHRASE` secret-এ key-এর passphrase দিন।
- `APT_REPO_SIGNING_FINGERPRINT` variable-এ পুরো fingerprint দিন, space ছাড়া।

Private key নিরাপদে backup রাখুন; GitHub-এ commit বা chat-এ পাঠাবেন না। Release workflow secret key ও public fingerprint মিলিয়ে তারপর publish করে। প্রথম signed release-এর পরে public key ও fingerprint `apt-repo` branch-এ থাকবে।

পরের package release-এ `echo_recon/__init__.py`-এর version বাড়িয়ে সেই version-এর tag দিন—যেমন version `6.7.0` হলে `v6.7.0`। Workflow পরীক্ষা, package build, sign ও publish করবে। Kali user-দের upgrade বলতে হলে আগে workflow সফল হয়েছে নিশ্চিত করুন।

### Kali user: feed যোগ ও install করুন

সমর্থিত architecture `amd64` ও `arm64`। Feed-এ public key ও প্রথম package প্রকাশিত আছে। প্রতিটি Kali-তে public key একবার নামিয়ে fingerprint দেখুন:

```bash
BASE=https://raw.githubusercontent.com/mdnhbn/echo-recon-workspace/apt-repo
curl -fsSLo /tmp/echo-recon-archive-keyring.gpg "$BASE/archive-keyring.gpg"
gpg --show-keys --with-fingerprint /tmp/echo-recon-archive-keyring.gpg
cat <(curl -fsSL "$BASE/KEY-FINGERPRINT.txt")
```

দুই fingerprint GitHub repository settings-এর `APT_REPO_SIGNING_FINGERPRINT` variable-এর সঙ্গে মিলিয়ে নিন। তারপর key ও source যোগ করুন:

```bash
sudo install -d -m 0755 /etc/apt/keyrings
sudo install -m 0644 /tmp/echo-recon-archive-keyring.gpg /etc/apt/keyrings/echo-recon.gpg
printf 'deb [signed-by=/etc/apt/keyrings/echo-recon.gpg] %s stable main\n' "$BASE" \
  | sudo tee /etc/apt/sources.list.d/echo-recon.list >/dev/null
sudo apt update
sudo apt install echo-recon
```

সাধারণ user হিসেবে `echo-recon` চালান; desktop menu-তেও **Echo Recon** থাকবে। Dashboard root হিসেবে চালাবেন না। App-এর package `/usr/lib`-এ read-only থাকবে, আর report/history `~/.local/share/echo-recon`-এ থাকবে—তাই package upgrade-এ history থাকবে। Scanner backend আগের মতো user-এর নিজের folder-এ থাকবে।

### Git clone-এর saved report সরিয়ে নিন

আগের install-এ report থাকলে dashboard বন্ধ করুন, private backup রাখুন, তারপর APT version প্রথমবার চালানোর আগে SQLite history copy করুন:

```bash
mkdir -p ~/.local/share/echo-recon
cp -a ~/Tools/02-Custom/echo-recon-workspace/data/history.sqlite3* ~/.local/share/echo-recon/
chmod 700 ~/.local/share/echo-recon
chmod 600 ~/.local/share/echo-recon/history.sqlite3*
```

Clone অন্য folder-এ থাকলে path বদলান। নতুন dashboard-এ saved report দেখা পর্যন্ত পুরোনো folder রাখুন। Migration-এর পরে `echo-recon` চালান; `bash run.sh` আলাদা Git clone চালায়, যা APT update করে না।
