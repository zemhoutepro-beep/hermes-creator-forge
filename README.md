# Hermes Creator Forge

**Turn a repeatable workflow into a reviewed, reusable Hermes Agent skill.**

Hermes Creator Forge is a skills-only ChatGPT/Codex plugin for people who want their agent workflows to be more than a pasted prompt. It helps turn a procedure, source document, or rough idea into a portable Hermes `SKILL.md` package, add realistic evaluation prompts, and review existing skills for safety and clarity.

## What it does

- **Build a skill:** define one user job, ground it in source material, write the procedure and safety boundaries, and include positive and boundary evaluation prompts.
- **Review a skill:** inspect its frontmatter, referenced files, tools, portability, failure behavior, and safety posture, then return an evidence-based report without silently editing the source.
- **Check this package:** run the YAML-aware repository validator and focused unit tests.

The authoring and review workflows use the model available in the current ChatGPT/Codex host. There is no bundled model, hosted service, API key, MCP server, telemetry, or install hook. Host-native workspace access is used only when available; file creation and changes stay subject to the user's request and host controls.

## Installation

This repository contains two distinct installation formats:

- **OpenAI plugin package:** root `plugin.json` is the portable manifest. Its `extensions.com.openai` block provides the OpenAI presentation and takes precedence over `.codex-plugin/plugin.json`. The repository marketplace at `.agents/plugins/marketplace.json` makes this local checkout discoverable in supported ChatGPT desktop marketplace flows. It is a local development catalog, not an official public listing.
- **Hermes skills:** Hermes consumes individual `SKILL.md` folders. Copy the chosen folders from `skills/` into your Hermes skills directory; this does not install the OpenAI plugin or register the package in a Hermes marketplace.

### Check a clean checkout

Use Python 3.10 or newer. PyYAML 6.0.3 is needed only for repository validation; plugin and skill loading do not invoke the validator.

```powershell
git clone https://github.com/zemhoutepro-beep/hermes-creator-forge.git
cd hermes-creator-forge
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/validate_skills.py --root .
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

These commands use the published repository revision. The installation catalog and instructions in this checkout are still local changes, so a fresh remote clone will not include them until a later authorized publication. To verify this exact revision before then, use a clean copy of the current checkout.

The repository marketplace points at the checkout root. In ChatGPT desktop, restart the app, select the `Hermes Creator Forge (local)` repository marketplace in the Plugins Directory, and install the available plugin. If you use the Codex CLI to register the local marketplace, run `codex plugin marketplace add <repository-path>` and inspect it with `codex plugin marketplace list`; use the desktop Plugins Directory to install and try the plugin. Remove the plugin through the host's plugin management UI when finished.

### Install Skills into Hermes manually

The repository includes four top-level Skills. In PowerShell, from the repository root, copy each folder and its support files into Hermes' user skills directory. Your account must be able to create folders under `$HOME\.hermes\skills`; the commands stop before copying if a same-named Skill already exists:

```powershell
$source = (Resolve-Path .\skills).Path
$destination = Join-Path $HOME ".hermes\skills"
$skills = Get-ChildItem $source -Directory
$conflicts = $skills | Where-Object { Test-Path (Join-Path $destination $_.Name) }
if ($conflicts) { throw "Existing Skills would be overwritten: $($conflicts.Name -join ', ')" }
New-Item -ItemType Directory -Force -Path $destination | Out-Null
foreach ($skill in $skills) { Copy-Item -Recurse $skill.FullName (Join-Path $destination $skill.Name) }
```

Start a new Hermes session and confirm the Skills are listed (`hermes skills list`, where supported). To uninstall these manual copies, remove only the four folders you copied from `$HOME\.hermes\skills`; retain any local edits you want to keep. Hermes' own installer, Hub publication, and automatic repository tap are separate flows and are not configured here.

### Try the workflows

In a host where the plugin has been installed, ask:

> Turn this workflow into a Hermes Agent skill: every Friday I review merged changes, draft user-focused release notes, and get approval before publishing.

Review a package with:

> Audit this Hermes skill and its references for unsafe actions, unsupported commands, and missing tests. Do not edit the files.

The build workflow should produce a focused `SKILL.md`, only necessary support files, and evaluation prompts. It must label the result as a draft and keep installation/publication separate from authoring.

## Repository layout

```text
plugin.json                      Portable Agent Plugin manifest
.codex-plugin/plugin.json        Codex compatibility presentation layer
skills/build-hermes-skill/       Workflow-to-Hermes-skill authoring
skills/review-hermes-skill/      Evidence-based quality and safety review
skills/host-workspace-operator/  Host-native local file/repository operations
skills/sandbox-python-executor/  Deterministic execution evidence
scripts/validate_skills.py       YAML-aware package checks
tests/                           Regression coverage for the validator
examples/                        Workflow brief and example skill output
docs/                            Architecture, safety, demo, and brand notes
submission/                      Draft listing and reviewer scenarios
```

The validator parses YAML with PyYAML's safe loader, checks the local marketplace path and plugin identity, validates manifest and skill metadata, and checks assets, references, and package safety. It does not simulate a Hermes or OpenAI host.

## Hackathon materials

- [Submission narrative](HACKATHON_SUBMISSION.md)
- [Architecture](docs/architecture.md)
- [Three-minute demo](docs/demo-script.md)
- [Security and privacy notes](docs/security.md)
- [Reviewer scenarios](submission/reviewer-packet.json)
- [Draft directory listing](submission/listing.json)
- [Submission readiness](submission/status.json)
- [Brand rationale](docs/brand.md)

The listing intentionally leaves publisher identity and public legal/support URLs blank until the owner supplies verified details. No license is declared because this repository had none when inspected; choose one before redistributing the source under an open-source license.

## Current status

This is a local preview. The marketplace file is for local development and does not publish the plugin to an official marketplace. ChatGPT desktop, Codex, and Hermes runtime installation have not been exercised in this checkout; the package and copy paths are covered by local structural tests only. The GitHub Actions workflow has not been run for the current local changes. The reviewer cases are plans, not claims that a live host or model behavior has been tested.

## Hermes format

Hermes discovers each skill by a folder containing `SKILL.md`; references, templates, and scripts are optional. See the [official Hermes Skills guide](https://hermes-agent.nousresearch.com/docs/guides/work-with-skills/) and [OpenAI Plugin packaging guide](https://developers.openai.com/plugins/build/plugins).
