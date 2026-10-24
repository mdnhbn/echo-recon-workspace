# Contributing to Echo Recon

Students, classmates and other contributors are welcome. You can improve code, tests, translations, installation instructions or documentation. You do not need to be an expert.

**[বাংলা নির্দেশনা / Bengali guide](CONTRIBUTING.bn.md)** · [Code of conduct](CODE_OF_CONDUCT.md) · [Security guidance](SECURITY.md)

## How contributions reach the project

Anyone with a GitHub account can propose a change through a **fork and pull request (PR)**. A fork is your own copy; a PR asks the maintainers to review your changes. Maintainers decide what merges into this repository. A public repository does not give everyone permission to push directly to its main branch.

For a small typo, open the file on GitHub, select the pencil icon, edit it and follow GitHub's prompts to propose a change. For a larger change, use the steps below.

## First contribution, step by step

1. Read the [README](README.md), [architecture](docs/ARCHITECTURE.md) and [security limits](SECURITY.md).
2. Check existing issues and pull requests to avoid duplicating work. Open an issue for a substantial feature so its scope can be discussed first. A small documentation correction can go straight to a PR.
3. Select **Fork** on the [project page](https://github.com/mdnhbn/echo-recon-workspace). Keep the default branch selected.
4. Clone **your fork**, replacing `YOUR-USERNAME` with your GitHub username:

   ```bash
   git clone https://github.com/YOUR-USERNAME/echo-recon-workspace.git
   cd echo-recon-workspace
   git switch -c improve-install-guide
   ```

5. Follow the README installation instructions for your operating system. Use the project's virtual environment and a normal user account.
6. Make one focused change. Update English and Bengali documentation together where practical; ask for translation help if needed.
7. Run the relevant checks below. Review `git diff` before committing. Keep private reports, credentials, environments and downloaded scanner binaries out of the commit.
8. Save and upload your change to your fork:

   ```bash
   git add path/to/changed-file
   git commit -m "Clarify installation instructions"
   git push -u origin improve-install-guide
   ```

   Replace the example file path and branch name with your actual ones. Add only the files you intend to contribute.

9. On your fork's GitHub page, select **Compare & pull request**. The destination should be `mdnhbn/echo-recon-workspace`, branch `main`.
10. Explain the problem, what changed and how you checked it. Respond to review comments. Further commits on the same branch update the PR automatically.

Do not force-push or delete someone else's work. If the main branch has moved, ask for help resolving a conflict rather than resetting changes you do not understand.

## Local checks

Run these from the repository folder after installing dashboard dependencies. Optional scanners are not required for the automated tests.

Kali / Linux:

```bash
.venv/bin/python -m unittest discover -s tests -v
bash -n install.sh run.sh
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests should use mocked scanner responses, simulated DNS and local child processes in temporary directories. Do not make the test suite depend on a public website, real credentials or a paid service. Keep fixtures isolated from the production `data/` directory; do not add a demo generator or seed fake history. For a visual change, check the empty dashboard and tool-setup view, and render report fixtures only through a temporary test application. Describe any checks you could not run; do not claim an untested platform works.

## What makes a useful change

- Keep changes small enough to review and explain the reason behind them.
- Preserve the normal-user, loopback-only dashboard and explicit scope controls.
- Treat scanner findings as unverified evidence. Missing tools, failures and incomplete work must stay visible.
- Keep user input out of shell command strings. Add regression coverage for a meaningful behavior fix.
- Use portable paths and Python APIs when possible. Linux-only commands need a documented Windows/WSL alternative or an explicit unsupported result.
- Keep each scanner optional. Document its identity, supported platform and limitations; do not silently download or launch additional tools.
- Keep official sources and setup commands reviewed and fixed. The no-argument **Setup all tools** launcher opens a local terminal; never accept shell input, versions, paths or sudo credentials through HTTP. Preserve missing/unverified distinctions, isolated user environments and refreshable diagnostics. Test installation with mocked subprocesses, not real apt/pip/Go changes in CI.
- Use mock or synthetic evidence in examples. Redact any screenshot before sharing it.

Good starting points include a documentation typo, a clearer error message, a Bengali translation, an accessible form label or a test for a previously reported bug.

## Report a bug or request a feature

Use the repository's **Issues → New issue** templates. Include your operating system, Python version, relevant tool version, reproduction steps and expected/actual behavior. For Windows, say whether the dashboard or scanner runs natively or inside WSL.

Do not post passwords, tokens, real target reports or another person's information. Follow [SECURITY.md](SECURITY.md) for a security-sensitive report; public issues are not a place to upload exploit evidence or secrets.

## Credit and licensing

Keep the original **Ahammed / Auto-Recon** attribution and [NOTICE.md](NOTICE.md). Credit other people's contributions accurately. Submit only material you wrote or have permission to share, and identify any third-party source and its license.

The project uses the **[MIT License](LICENSE)**, selected at the maintainer's direction. By submitting a contribution, you agree that it is available under the project's MIT License. Keep the copyright and permission notice when redistributing the software or substantial portions. No separate contributor license agreement (CLA) is required. Third-party tools and dependencies retain their own licenses.
