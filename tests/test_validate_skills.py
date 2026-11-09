from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_skills import parse_frontmatter, validate, validate_agent_metadata  # noqa: E402
from build_source_archive import build_archive  # noqa: E402


class FrontmatterTests(unittest.TestCase):
    def test_reads_required_top_level_fields_and_body(self):
        parsed = parse_frontmatter("---\nname: sample\ndescription: One job.\nversion: 1.0.0\nmetadata:\n  hermes:\n    tags: [demo]\n---\n\n# Sample\n")
        self.assertIsNotNone(parsed)
        fields, body = parsed
        self.assertEqual(fields["name"], "sample")
        self.assertEqual(fields["description"], "One job.")
        self.assertTrue(body.startswith("# Sample"))

    def test_rejects_missing_closing_delimiter(self):
        self.assertIsNone(parse_frontmatter("---\nname: sample\ndescription: One job.\n"))

    def test_rejects_malformed_yaml_without_crashing_validate(self):
        with tempfile.TemporaryDirectory() as temp:
            copy = self._copy_repo(Path(temp))
            path = copy / "skills" / "build-hermes-skill" / "SKILL.md"
            path.write_text("---\nname: [broken\ndescription: test\n---\nbody\n", encoding="utf-8")
            errors = validate(copy)
            self.assertTrue(any("invalid YAML frontmatter" in error for error in errors))

    def test_reports_missing_required_frontmatter_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            copy = self._copy_repo(Path(temp))
            path = copy / "skills" / "build-hermes-skill" / "SKILL.md"
            path.write_text("---\nname: build-hermes-skill\n---\nbody\n", encoding="utf-8")
            errors = validate(copy)
            self.assertTrue(any("description must be a non-empty string" in error for error in errors))

    def test_rejects_duplicate_keys_and_aliases(self):
        for yaml_text in (
            "name: sample\nname: duplicate\ndescription: test\n",
            "name: &skill sample\ndescription: *skill\n",
        ):
            with self.subTest(yaml_text=yaml_text):
                with self.assertRaises(ValueError):
                    parse_frontmatter(f"---\n{yaml_text}---\nbody\n")

    def test_rejects_frontmatter_type_errors_and_missing_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            copy = self._copy_repo(Path(temp))
            path = copy / "skills" / "build-hermes-skill" / "SKILL.md"
            path.write_text("---\nname: 12\ndescription: false\nversion: [1, 0]\n---\nbody\n", encoding="utf-8")
            errors = validate(copy)
            self.assertTrue(any("name must be a non-empty string" in error for error in errors))
            self.assertTrue(any("description must be a non-empty string" in error for error in errors))
            self.assertTrue(any("version must be a semantic version string" in error for error in errors))

    def test_rejects_agent_yaml_types_and_malformed_yaml(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "openai.yaml"
            path.write_text("interface: [bad\n", encoding="utf-8")
            self.assertTrue(any("invalid agent YAML" in error for error in validate_agent_metadata(path)))
            path.write_text('interface:\n  display_name: 7\n  short_description: ok\n  default_prompt: ok\npolicy:\n  products: CHAT\n  allow_implicit_invocation: "yes"\n', encoding="utf-8")
            errors = validate_agent_metadata(path)
            self.assertTrue(any("display_name must be a non-empty string" in error for error in errors))
            self.assertTrue(any("products must be a non-empty list" in error for error in errors))
            self.assertTrue(any("allow_implicit_invocation must be boolean" in error for error in errors))

    @staticmethod
    def _copy_repo(destination):
        import shutil
        shutil.copytree(ROOT, destination, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", ".git"))
        return destination

    def test_agent_metadata_accepts_plugin_surfaces(self):
        path = ROOT / "skills" / "build-hermes-skill" / "agents" / "openai.yaml"
        self.assertEqual(validate_agent_metadata(path), [])

    def test_example_skill_name_matches_its_directory_slug(self):
        folder = ROOT / "examples" / "release-notes-skill"
        parsed = parse_frontmatter((folder / "SKILL.md").read_text(encoding="utf-8"))
        self.assertIsNotNone(parsed)
        fields, _ = parsed
        self.assertEqual(fields.get("name"), folder.name)


class SubmissionIntegrityTests(unittest.TestCase):
    def test_status_count_matches_discovered_unit_tests(self):
        status = json.loads((ROOT / "submission" / "status.json").read_text(encoding="utf-8"))
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test*.py")
        self.assertEqual(status["unit_test_count"], suite.countTestCases())
        self.assertEqual(status["unit_test_result"], "passed")

    def test_repair_eval_waits_for_approval_without_requiring_it_again(self):
        prompt = "Fix every issue you find in my Hermes skills, but first show me the repair plan and wait for my approval before changing any files."
        markdown = (ROOT / "skills" / "review-hermes-skill" / "EVALS.md").read_text(encoding="utf-8")
        packet = json.loads((ROOT / "submission" / "reviewer-packet.json").read_text(encoding="utf-8"))
        cases = [case for case in packet["negativeCases"] if case["prompt"] == prompt]
        self.assertIn(prompt, markdown)
        self.assertEqual(len(cases), 1)
        self.assertIn("without editing until the user approves", cases[0]["expected"])


class PackageTests(unittest.TestCase):
    def test_repository_package_passes(self):
        self.assertEqual(validate(ROOT), [])

    def test_rejects_manifest_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            copy = Path(temp)
            import shutil
            shutil.copytree(ROOT, copy, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", ".git"))
            compat = copy / ".codex-plugin" / "plugin.json"
            compat.write_text(compat.read_text(encoding="utf-8").replace("Hermes Creator Forge", "Different Name", 1), encoding="utf-8")
            self.assertTrue(any("must match" in item for item in validate(copy)))

    def test_rejects_each_shared_manifest_field_mismatch(self):
        for field, value in (("name", "different"), ("version", "9.9.9"), ("description", "different"), ("author", {"name": "different"})):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                copy = Path(temp)
                import shutil
                shutil.copytree(ROOT, copy, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", ".git"))
                compat_path = copy / ".codex-plugin" / "plugin.json"
                compat = json.loads(compat_path.read_text(encoding="utf-8"))
                compat[field] = value
                compat_path.write_text(json.dumps(compat), encoding="utf-8")
                self.assertTrue(any(f"manifest field {field} must match" in item for item in validate(copy)))

    def test_invalid_manifest_roots_and_field_types_report_errors(self):
        with tempfile.TemporaryDirectory() as temp:
            copy = Path(temp)
            import shutil
            shutil.copytree(ROOT, copy, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", ".git"))
            (copy / "plugin.json").write_text("[]", encoding="utf-8")
            errors = validate(copy)
            self.assertTrue(any("top-level JSON value must be an object" in item for item in errors))
            (copy / "plugin.json").write_text('{"name": [], "version": 2, "description": false, "author": []}', encoding="utf-8")
            errors = validate(copy)
            self.assertTrue(any("version must be a non-empty string" in item for item in errors))
            self.assertTrue(any("author must be an object" in item for item in errors))

    def test_rejects_missing_local_reference(self):
        with tempfile.TemporaryDirectory() as temp:
            copy = Path(temp)
            import shutil
            shutil.copytree(ROOT, copy, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", ".git"))
            skill = copy / "skills" / "build-hermes-skill" / "SKILL.md"
            skill.write_text(skill.read_text(encoding="utf-8") + "\nSee `references/not-there.md`.\n", encoding="utf-8")
            self.assertTrue(any("missing or unsafe reference" in item for item in validate(copy)))


class ArchiveTests(unittest.TestCase):

    def test_real_project_archive_contains_required_files(self):
        required = [
            "plugin.json",
            ".codex-plugin/plugin.json",
            ".agents/plugins/marketplace.json",
            "skills/build-hermes-skill/SKILL.md",
            "skills/build-hermes-skill/references/hermes-authoring-standard.md",
            "skills/build-hermes-skill/references/safety-review.md",
            "skills/host-workspace-operator/SKILL.md",
            "skills/review-hermes-skill/SKILL.md",
            "skills/sandbox-python-executor/SKILL.md",
            "assets/icon.svg",
            "submission/listing.json",
            "submission/reviewer-packet.json",
            "submission/status.json",
            "HACKATHON_SUBMISSION.md",
        ]

        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "hermes-review.zip"
            build_archive(ROOT, output)

            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())

            missing = sorted(set(required) - names)
            self.assertFalse(missing, f"Missing archive files: {missing}")

            unwanted = [
                name for name in names
                if "__pycache__" in name or name.endswith((".pyc", ".pyo"))
            ]
            self.assertEqual(unwanted, [], f"Unexpected Python caches: {unwanted}")

    def test_archive_is_deterministic_and_excludes_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "source"
            root.mkdir()
            (root / "README.md").write_text("demo\n", encoding="utf-8")
            output = Path(temp) / "review.zip"
            self.assertEqual(build_archive(root, output), 1)
            first = output.read_bytes()
            self.assertEqual(build_archive(root, output), 1)
            self.assertEqual(first, output.read_bytes())

    def test_archive_refuses_secret_shaped_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "source"
            root.mkdir()
            (root / ".env").write_text("TOKEN=not-a-real-token", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "secret-shaped"):
                build_archive(root, Path(temp) / "review.zip")

    def test_archive_refuses_environment_variants(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "source"
            root.mkdir()
            (root / ".env.production").write_text("TOKEN=not-a-real-token", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "secret-shaped"):
                build_archive(root, Path(temp) / "review.zip")


if __name__ == "__main__":
    unittest.main()
