# Three-minute demo

## 0:00 — Set the problem

“We repeat useful workflows, but a copied prompt is not a durable, safe skill. We need a focused procedure, evidence for its steps, and a way to try its boundaries.”

## 0:20 — Build from a real workflow

Open [the example workflow brief](../examples/workflow-brief.md). Ask Hermes Creator Forge:

> Turn this workflow into a reusable Hermes Agent skill. Preserve the approval gate and include tests for missing source data and attempted early publication.

Show the generated skill's trigger, ordered steps, failure handling, verification rule, and positive/boundary evals. Point out that the skill drafts notes but stops before publication.

## 1:30 — Review the result

Ask:

> Audit this skill for unsupported commands, unsafe side effects, and missing verification. Do not edit it.

Show that the reviewer checks claims against the source, reports findings with evidence, and keeps the source untouched.

## 2:15 — Show package checks

Run `python scripts/validate_skills.py --root .` and `python -m unittest discover -s tests -v`. Explain that the checker verifies package shape; it does not prove an LLM's behavior. The included eval prompts are the next step in a fresh Hermes session.

## 2:45 — Close

“The forge turns a repeated process into a portable skill with a visible safety boundary and a test plan. The user stays in control of edits, installation, and publication.”

## Backup if a live model is unavailable

Use [the example skill](../examples/release-notes-skill/SKILL.md) as the completed output and explain that it was authored as a demo fixture, not generated live during the recording. Do not present a planned test as a passing result.
