# Hermes Creator Forge — Hackathon Submission

## One-line pitch

Turn the work your team repeats into a safe, testable Hermes Agent skill you can reuse tomorrow.

## The problem

Teams repeat useful procedures in chat, docs, and tribal memory. Copying those instructions into a skill is easy; making the skill focused, portable, honest about its tools, safe around real actions, and testable is the hard part.

## The solution

Hermes Creator Forge is a portable AI workflow for authoring and reviewing Hermes Agent skills. It guides the model through a source-grounded creation loop: identify the user job, map the procedure, state permissions and failure cases, write the smallest skill package, and generate positive and boundary eval prompts. A complementary reviewer audits existing skills and returns evidence without silently changing files.

## What makes it useful

- **Proof-oriented output:** a new skill ships with eval prompts that make expected behavior concrete.
- **Safety in the authoring loop:** source documents are treated as untrusted data; destructive/external actions get explicit boundaries; unknown commands and APIs are not invented.
- **Portable by design:** the output follows Hermes's folder-plus-`SKILL.md` format and uses no server or provider-specific SDK.
- **Review without surprise edits:** the audit workflow reports findings first and keeps repair, installation, and publication as separate user-directed actions.

## Architecture

Skills-only Agent Plugin. ChatGPT/Codex supplies the model; the plugin packages the workflow instructions and review guidance. Host-native file/search/shell/Python capabilities are used where the host provides them. No MCP service, API key, database, telemetry, or background process is needed.

```text
Workflow / source files
        │
        ▼
Build Hermes Skill ──► SKILL.md + optional references + eval prompts
        │                                     │
        └──────────────────────────────► package validation
                                              │
Existing skill ──► Review Hermes Skill ──► findings + minimal repair plan
```

## Demo

Use the release-notes workflow in [examples/workflow-brief.md](examples/workflow-brief.md). Ask the plugin to build a skill, then ask it to audit the generated example in [examples/release-notes-skill/SKILL.md](examples/release-notes-skill/SKILL.md). Demonstrate that the skill requires approval before publishing, maps output back to source evidence, and does not publish itself. Full narration and expected outputs are in [docs/demo-script.md](docs/demo-script.md).

## Validation evidence

- The package has a Python validator with pinned PyYAML and regression tests.
- GitHub Actions now runs validation and tests on pushes, pull requests, and manual dispatches with read-only repository permissions.
- The original branch had no source code, README, tests, or package metadata. Its only workflow run succeeded by printing a message; it did not test a product.
- Local checks and clean-copy validation are recorded in the project handoff. The local marketplace manifest follows the documented repo-marketplace format, but host installation has not been tested here. CI has not run on the remote branch because the checkout uses a source archive and GitHub credentials are unavailable in this environment.

## Impact measures to collect in a live demo

1. Time from raw workflow to reviewable first draft.
2. Fraction of generated steps that trace to source evidence or are clearly marked as assumptions.
3. Positive and boundary evaluation prompts passed on a fresh Hermes session.
4. Number of unsafe side effects caught before a skill is installed or used.

These are proposed measurements; no performance gains are claimed yet.

## Submission state

**Local preview prepared.** The local `developerName` is set to `zemhoutepro-beep`; public publisher identity verification remains pending. Public support, privacy, and terms URLs are not provided. Live ChatGPT/Codex installation, live Hermes Agent behavior, public directory review, and the video walkthrough remain unverified.
