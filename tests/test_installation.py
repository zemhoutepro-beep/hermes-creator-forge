from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_skills import validate  # noqa: E402


class InstallationTests(unittest.TestCase):
    def test_clean_copy_has_valid_marketplace_and_all_four_skills(self):
        with tempfile.TemporaryDirectory() as temp:
            clean_copy = Path(temp) / "checkout"
            shutil.copytree(ROOT, clean_copy, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))

            self.assertEqual(validate(clean_copy), [])
            skill_dirs = sorted(path.name for path in (clean_copy / "skills").iterdir() if path.is_dir())
            self.assertEqual(
                skill_dirs,
                ["build-hermes-skill", "host-workspace-operator", "review-hermes-skill", "sandbox-python-executor"],
            )
            for slug in skill_dirs:
                self.assertTrue((clean_copy / "skills" / slug / "SKILL.md").is_file())
            self.assertTrue((clean_copy / "skills" / "build-hermes-skill" / "references" / "hermes-authoring-standard.md").is_file())
            self.assertTrue((clean_copy / "skills" / "build-hermes-skill" / "references" / "safety-review.md").is_file())
            self.assertTrue((clean_copy / "skills" / "build-hermes-skill" / "EVALS.md").is_file())
            self.assertTrue((clean_copy / "skills" / "review-hermes-skill" / "EVALS.md").is_file())

            hermes_skills = Path(temp) / "hermes-profile" / "skills"
            hermes_skills.mkdir(parents=True)
            for slug in skill_dirs:
                shutil.copytree(clean_copy / "skills" / slug, hermes_skills / slug)
                self.assertEqual(
                    (hermes_skills / slug / "SKILL.md").read_bytes(),
                    (clean_copy / "skills" / slug / "SKILL.md").read_bytes(),
                )
            self.assertTrue((hermes_skills / "build-hermes-skill" / "references" / "hermes-authoring-standard.md").is_file())

            marketplace = json.loads((clean_copy / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
            source = marketplace["plugins"][0]["source"]["path"]
            plugin_path = (clean_copy / source.removeprefix("./")).resolve()
            self.assertEqual(plugin_path, clean_copy.resolve())
            self.assertEqual(json.loads((plugin_path / "plugin.json").read_text(encoding="utf-8"))["name"], "hermes-creator-forge")

    def test_missing_skill_file_is_reported_in_clean_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            clean_copy = Path(temp) / "checkout"

            def omit_build_skill(directory: str, names: list[str]) -> set[str]:
                ignored = {".git", "__pycache__"}.intersection(names)
                if Path(directory).name == "build-hermes-skill" and "SKILL.md" in names:
                    ignored.add("SKILL.md")
                return ignored

            shutil.copytree(ROOT, clean_copy, ignore=omit_build_skill)
            errors = validate(clean_copy)
            self.assertTrue(any("skills/build-hermes-skill/SKILL.md must be a regular file" in error for error in errors))

    def test_missing_repository_entry_points_return_diagnostics(self):
        with tempfile.TemporaryDirectory() as temp:
            errors = validate(Path(temp) / "missing-checkout")
            self.assertTrue(any("plugin.json: cannot read valid JSON" in error for error in errors))
            self.assertTrue(any("skills/ directory is required" in error for error in errors))

    def test_marketplace_path_outside_checkout_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            clean_copy = Path(temp) / "checkout"
            shutil.copytree(ROOT, clean_copy, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
            path = clean_copy / ".agents" / "plugins" / "marketplace.json"
            market = json.loads(path.read_text(encoding="utf-8"))
            market["plugins"][0]["source"]["path"] = "./../outside"
            path.write_text(json.dumps(market), encoding="utf-8")
            self.assertTrue(any("must be a ./ path inside the repository" in error for error in validate(clean_copy)))

    def test_manifest_asset_path_must_exist_inside_checkout(self):
        with tempfile.TemporaryDirectory() as temp:
            clean_copy = Path(temp) / "checkout"
            shutil.copytree(ROOT, clean_copy, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
            path = clean_copy / "plugin.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["extensions"]["com.openai"]["interface"]["logo"] = "./assets/missing.svg"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertTrue(any("interface.logo points to a missing or unsafe asset" in error for error in validate(clean_copy)))

    def test_missing_yaml_dependency_has_actionable_cli_error(self):
        result = subprocess.run(
            [sys.executable, "-S", str(ROOT / "scripts" / "validate_skills.py"), "--root", str(ROOT)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PyYAML is required", result.stdout)
        self.assertIn("pip install -r requirements.txt", result.stdout)


if __name__ == "__main__":
    unittest.main()
