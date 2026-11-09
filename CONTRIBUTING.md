# Contributing

## Local checks

Use Python 3.10 or newer and install the pinned validator dependency:

```powershell
python -m pip install -r requirements.txt
python scripts/validate_skills.py --root .
python -m unittest discover -s tests -v
```

The local plugin catalog is `.agents/plugins/marketplace.json`. Keep its source path relative to the repository root and ensure it resolves to the plugin manifest. Skill folders under `skills/` can also be copied manually to a Hermes profile; this does not publish a plugin or add a Hermes Hub listing.

## Skill changes

- Keep each skill focused on one user job.
- Ground procedures in documented behavior; label assumptions and unknowns.
- Include positive and boundary evaluation prompts for new workflows.
- Keep review workflows read-only unless a separate user request authorizes a change.
- Do not add secrets, credentials, or local personal paths.
- Update both manifests together; the regression checker verifies parity.

## Pull requests

Explain the user outcome, safety boundary, tests run, and any unverified behavior. Do not claim a fresh Hermes or ChatGPT/Codex smoke test unless one was actually performed.
