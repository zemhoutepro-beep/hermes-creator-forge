# Hermes skill authoring standard

## Package layout

```text
<skill-slug>/
├── SKILL.md
├── EVALS.md                 # recommended for new skills
├── references/              # optional, loaded only when relevant
├── templates/               # optional, reusable output shapes
└── scripts/                 # optional, deterministic helpers only
```

Hermes discovers each skill folder by its `SKILL.md`. The folder name is the install slug; keep it lowercase kebab-case. Use standard YAML frontmatter with a matching `name`, a short trigger-oriented `description`, a semantic `version`, and optional `metadata.hermes.tags` / `metadata.hermes.category`. Keep descriptions concise (aim for 60 characters or fewer) so skill lists stay scannable.

```yaml
---
name: update-release-notes
description: Draft release notes from merged changes and version details.
version: 1.0.0
metadata:
  hermes:
    tags: [release, changelog]
    category: developer-tools
---
```

## Recommended instruction order

1. Title and one-sentence outcome.
2. **When to use**: specific user requests and exclusions.
3. **Prerequisites**: source of truth, access, tools, and missing input behavior.
4. **Procedure**: ordered actions with branches and checkpoints.
5. **Safety**: what requires explicit approval, handling of untrusted content, and prohibited shortcuts.
6. **Failure handling**: what to do when a source/tool fails or evidence conflicts.
7. **Verification**: a check that can actually be performed and reported.
8. **Output**: the concrete shape of the result, including uncertainty.

## Quality checklist

- One skill serves one recognizable, repeatable job.
- The trigger and finished result are concrete.
- Every named tool, command, file path, and dependency is real or clearly marked as a user-provided prerequisite.
- The procedure uses evidence from the requested source and does not fabricate results.
- Instructions separate read-only discovery from file changes and external actions.
- References are relative to the skill folder, focused, and loaded only when needed.
- Tests include normal input, incomplete or ambiguous input, and a meaningful boundary case.
- The skill still works after it is copied out of this repository.

## Hermes documentation

Hermes skills are Markdown files with YAML frontmatter and can include references, templates, and scripts. Official guidance: https://hermes-agent.nousresearch.com/docs/guides/work-with-skills/
