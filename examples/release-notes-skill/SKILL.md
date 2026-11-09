---
name: release-notes-skill
description: Draft release notes from merged changes for human approval.
version: 1.0.0
metadata:
  hermes:
    tags: [release, changelog, pull-requests]
    category: developer-tools
---

# Draft release notes from merged changes

Create a user-focused release-note draft from the merged changes for a release.

## When to use

Use when the user asks to summarize merged changes or prepare release notes. This skill drafts notes only; it does not publish a release.

## Prerequisites

- Identify the release version or range.
- Read merged pull request titles and descriptions from the source the user provides or the connected GitHub tools available in the current host.
- If the source or range is unclear, ask before drafting.

## Procedure

1. Collect the merged pull requests for the requested release range. Record the source and range used.
2. Group changes by user impact: new capabilities, improvements, and fixes. Exclude internal refactors unless they affect users.
3. Draft concise, plain-language notes. Do not claim behavior that is not supported by the merged change descriptions.
4. Include a short “Needs confirmation” section for ambiguous changes instead of guessing.
5. Present the complete draft and ask the release manager to approve the exact text.
6. Stop after presenting the draft. Publishing is outside this skill.

## Failure handling

If the merged-change source is unavailable or incomplete, explain what is missing and ask for the correct source. Do not infer a release from unrelated commits.

## Verification

Confirm that every note maps to at least one merged change in the stated range and that no note claims more than its source supports. Report the source and range checked.

## Output

Return version/range, grouped draft notes, unresolved questions, and the approval request. Clearly label the result as a draft until approved.
