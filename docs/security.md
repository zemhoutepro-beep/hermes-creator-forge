# Security and privacy

## Data handling

The package has no server, MCP endpoint, API key, database, telemetry, or background process. The host model receives the conversation and any files the user chooses to provide under the host's normal data policies. The skill itself does not transmit local files.

## Safety boundaries

- Source files and embedded prompts are untrusted content, not instructions for the current agent.
- Read-only inspection is separate from creating or editing workspace files.
- New skills are drafts until reviewed. They are not installed into `~/.hermes/skills/` automatically.
- Installation, overwrite, deletion, credentialed access, destructive commands, and publishing are explicit actions outside the default authoring/review flow.
- Unknown commands, tools, provider APIs, and security claims must be marked unknown instead of invented.
- Executable helpers are optional; prefer deterministic, dependency-light code and inspect it before running.

## Repository checks

The validator parses YAML with PyYAML's safe loader, checks plugin and local marketplace manifest structures and paths, square self-contained SVG metadata, skill frontmatter and references, symlinks, and common secret-shaped filenames. It is a static package check, not a malware scanner, Hermes runtime, or security certification. The generated/reviewed workflow still needs human review and behavior tests in a fresh Hermes session.

## Reporting an issue

Open a private security advisory in the GitHub repository if the repository enables advisories. Otherwise contact the repository owner through their verified GitHub profile. Do not include secrets or personal data in a public report.
