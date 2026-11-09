#!/usr/bin/env python3
"""Validate the structure and safety of this Hermes skill/plugin package."""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # Keep CLI failures actionable when dependencies were not installed.
    yaml = None  # type: ignore[assignment]

SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REFERENCE = re.compile(r"(?<![A-Za-z0-9_-])(references|templates|scripts|assets)/([A-Za-z0-9_./-]+)")
FORBIDDEN_BASENAMES = {".env", ".npmrc", "auth.json", "credentials.json", "secrets.json"}
COMMON_MANIFEST_FIELDS = ("name", "version", "description", "author")


class StrictSafeLoader(yaml.SafeLoader if yaml is not None else object):
    """Safe YAML loader that rejects duplicate mapping keys."""

    def compose_node(self, parent: Any, index: Any) -> Any:
        if self.check_event(yaml.AliasEvent):
            event = self.get_event()
            raise yaml.composer.ComposerError(None, None, "YAML aliases are not allowed", event.start_mark)
        return super().compose_node(parent, index)


def _construct_mapping(loader: StrictSafeLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise yaml.constructor.ConstructorError("while constructing a mapping", node.start_mark,
                                                    "unhashable mapping key", key_node.start_mark) from exc
        if duplicate:
            raise yaml.constructor.ConstructorError("while constructing a mapping", node.start_mark,
                                                    f"duplicate key {key!r}", key_node.start_mark)
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


if yaml is not None:
    StrictSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def is_secret_name(name: str) -> bool:
    lowered = name.lower()
    return lowered in FORBIDDEN_BASENAMES or lowered.startswith(".env.")


def _yaml_load(text: str) -> Any:
    if yaml is None:
        raise RuntimeError("PyYAML is required; install dependencies with: python -m pip install -r requirements.txt")
    return yaml.load(text, Loader=StrictSafeLoader)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str] | None:
    """Parse a SKILL.md frontmatter YAML mapping and its non-empty body."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    closing = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if closing is None:
        return None
    try:
        fields = _yaml_load("\n".join(lines[1:closing]))
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML frontmatter: {exc}") from exc
    body = "\n".join(lines[closing + 1:]).strip()
    if not isinstance(fields, dict) or not body:
        return None
    return fields, body


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _read_json_object(path: Path, label: str, errors: list[str]) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_json_object)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"{label}: cannot read valid JSON: {exc}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{label}: top-level JSON value must be an object")
        return None
    return data


def _validate_manifest(manifest: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    for field in COMMON_MANIFEST_FIELDS:
        value = manifest.get(field)
        if field == "author":
            if not isinstance(value, dict):
                errors.append(f"{label}: author must be an object with a non-empty name")
            elif not isinstance(value.get("name"), str) or not value["name"].strip():
                errors.append(f"{label}: author.name must be a non-empty string")
            elif "url" in value and (not isinstance(value["url"], str) or not value["url"].strip()):
                errors.append(f"{label}: author.url must be a non-empty string when provided")
        elif not isinstance(value, str) or not value.strip():
            errors.append(f"{label}: {field} must be a non-empty string")
        elif field == "version" and not SEMVER.fullmatch(value):
            errors.append(f"{label}: version must follow semantic versioning")
    if "repository" in manifest and (not isinstance(manifest["repository"], str) or not manifest["repository"].strip()):
        errors.append(f"{label}: repository must be a non-empty string when provided")
    if "keywords" in manifest and (not isinstance(manifest["keywords"], list) or any(not isinstance(v, str) or not v.strip() for v in manifest["keywords"])):
        errors.append(f"{label}: keywords must be a list of non-empty strings")
    return errors


def _validate_interface(interface: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    for field in ("displayName", "shortDescription", "longDescription", "category", "brandColor", "logo", "composerIcon"):
        if not isinstance(interface.get(field), str) or not interface[field].strip():
            errors.append(f"{label}: interface.{field} must be a non-empty string")
    for field in ("capabilities", "defaultPrompt"):
        value = interface.get(field)
        if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item.strip() for item in value):
            errors.append(f"{label}: interface.{field} must be a non-empty list of strings")
    if isinstance(interface.get("brandColor"), str) and not re.fullmatch(r"#[0-9A-Fa-f]{6}", interface["brandColor"]):
        errors.append(f"{label}: interface.brandColor must be a six-digit hex color string")
    return errors


def _validate_asset_paths(interface: dict[str, Any], label: str, root: Path) -> list[str]:
    errors: list[str] = []
    for field in ("logo", "composerIcon"):
        relative = interface.get(field)
        if not isinstance(relative, str) or not relative.startswith("./"):
            errors.append(f"{label}: interface.{field} must be a ./ path")
            continue
        asset = (root / relative.removeprefix("./")).resolve()
        if root not in asset.parents or not asset.is_file():
            errors.append(f"{label}: interface.{field} points to a missing or unsafe asset")
    return errors


def validate_agent_metadata(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = _yaml_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return [f"{path}: invalid agent YAML: {exc}"]
    if not isinstance(data, dict):
        return [f"{path}: agent YAML must contain a top-level mapping"]
    interface, policy = data.get("interface"), data.get("policy")
    if not isinstance(interface, dict):
        errors.append(f"{path}: interface must be a mapping")
        interface = {}
    for key in ("display_name", "short_description", "default_prompt"):
        if not isinstance(interface.get(key), str) or not interface[key].strip():
            errors.append(f"{path}: interface.{key} must be a non-empty string")
    if "brand_color" in interface and (not isinstance(interface["brand_color"], str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", interface["brand_color"])):
        errors.append(f"{path}: interface.brand_color must be a six-digit hex color string")
    if not isinstance(policy, dict):
        errors.append(f"{path}: policy must be a mapping")
        policy = {}
    products = policy.get("products")
    if not isinstance(products, list) or not products or any(not isinstance(p, str) or p not in {"CHAT", "CODEX"} for p in products):
        errors.append(f"{path}: policy.products must be a non-empty list containing only CHAT and CODEX")
    if not isinstance(policy.get("allow_implicit_invocation"), bool):
        errors.append(f"{path}: policy.allow_implicit_invocation must be boolean")
    return errors


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    root = root.resolve()
    if yaml is None:
        return ["PyYAML is required; install dependencies with: python -m pip install -r requirements.txt"]
    manifest = _read_json_object(root / "plugin.json", "plugin.json", errors)
    compatibility = _read_json_object(root / ".codex-plugin" / "plugin.json", ".codex-plugin/plugin.json", errors)
    if manifest is not None:
        errors.extend(_validate_manifest(manifest, "plugin.json"))
        if manifest.get("name") != "hermes-creator-forge":
            errors.append("plugin.json: name must be hermes-creator-forge")
        extensions = manifest.get("extensions")
        if not isinstance(extensions, dict):
            errors.append("plugin.json: extensions must be an object")
            openai = {}
        else:
            openai = extensions.get("com.openai")
            if not isinstance(openai, dict):
                errors.append("plugin.json: extensions.com.openai must be an object")
                openai = {}
        public_interface = openai.get("interface")
        if not isinstance(public_interface, dict):
            errors.append("plugin.json: extensions.com.openai.interface must be an object")
        else:
            errors.extend(_validate_interface(public_interface, "plugin.json"))
            errors.extend(_validate_asset_paths(public_interface, "plugin.json", root))
    else:
        public_interface = None

    marketplace_path = root / ".agents" / "plugins" / "marketplace.json"
    if marketplace_path.exists():
        marketplace = _read_json_object(marketplace_path, ".agents/plugins/marketplace.json", errors)
        if marketplace is not None:
            if not isinstance(marketplace.get("name"), str) or not marketplace["name"].strip():
                errors.append(".agents/plugins/marketplace.json: name must be a non-empty string")
            interface = marketplace.get("interface")
            if not isinstance(interface, dict) or not isinstance(interface.get("displayName"), str) or not interface["displayName"].strip():
                errors.append(".agents/plugins/marketplace.json: interface.displayName must be a non-empty string")
            plugins = marketplace.get("plugins")
            if not isinstance(plugins, list) or not plugins:
                errors.append(".agents/plugins/marketplace.json: plugins must be a non-empty list")
            else:
                for index, entry in enumerate(plugins):
                    label = f".agents/plugins/marketplace.json: plugins[{index}]"
                    if not isinstance(entry, dict):
                        errors.append(f"{label} must be an object")
                        continue
                    source = entry.get("source")
                    if not isinstance(source, dict) or source.get("source") != "local" or not isinstance(source.get("path"), str):
                        errors.append(f"{label}.source must declare a local path")
                        continue
                    relative = source["path"]
                    candidate = (root / relative.removeprefix("./")).resolve()
                    if not relative.startswith("./") or root not in candidate.parents and candidate != root:
                        errors.append(f"{label}.source.path must be a ./ path inside the repository")
                        continue
                    entry_name = entry.get("name")
                    if not isinstance(entry_name, str) or not entry_name.strip():
                        errors.append(f"{label}.name must be a non-empty string")
                    candidate_manifest = _read_json_object(candidate / "plugin.json", f"{label} plugin.json", errors)
                    if candidate_manifest is not None and candidate_manifest.get("name") != entry_name:
                        errors.append(f"{label}.name must match the plugin manifest at source.path")
                    policy = entry.get("policy")
                    if not isinstance(policy, dict) or policy.get("installation") not in {"AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"} or policy.get("authentication") not in {"ON_INSTALL", "ON_FIRST_USE"}:
                        errors.append(f"{label}.policy must declare valid installation and authentication values")
                    if not isinstance(entry.get("category"), str) or not entry["category"].strip():
                        errors.append(f"{label}.category must be a non-empty string")
    if compatibility is not None:
        errors.extend(_validate_manifest(compatibility, ".codex-plugin/plugin.json"))
        if compatibility.get("skills") != "./skills/":
            errors.append(".codex-plugin/plugin.json: skills must be ./skills/")
        compat_interface = compatibility.get("interface")
        if not isinstance(compat_interface, dict):
            errors.append(".codex-plugin/plugin.json: interface must be an object")
        else:
            errors.extend(_validate_interface(compat_interface, ".codex-plugin/plugin.json"))
            errors.extend(_validate_asset_paths(compat_interface, ".codex-plugin/plugin.json", root))
        if manifest is not None:
            for field in COMMON_MANIFEST_FIELDS:
                if manifest.get(field) != compatibility.get(field):
                    errors.append(f"manifest field {field} must match between plugin.json and .codex-plugin/plugin.json")
            if isinstance(public_interface, dict) and isinstance(compat_interface, dict) and public_interface != compat_interface:
                errors.append("portable OpenAI interface and Codex compatibility interface must match")

    for asset in ("logo-light.svg", "logo-dark.svg", "icon.svg"):
        path = root / "assets" / asset
        try:
            tree = ET.parse(path)
            svg = tree.getroot()
            if not svg.tag.endswith("svg"):
                errors.append(f"assets/{asset} must have an SVG root")
            if svg.attrib.get("viewBox") != "0 0 512 512":
                errors.append(f"assets/{asset} must use the square 0 0 512 512 viewBox")
            if svg.attrib.get("width") != "512" or svg.attrib.get("height") != "512":
                errors.append(f"assets/{asset} must declare 512 by 512 dimensions")
            if any(k.lower() in {"href", "xlink:href"} and str(v).startswith(("http:", "https:")) for el in svg.iter() for k, v in el.attrib.items()):
                errors.append(f"assets/{asset} must not load remote resources")
        except (OSError, ET.ParseError) as exc:
            errors.append(f"assets/{asset} is missing or invalid SVG: {exc}")

    skills_root = root / "skills"
    if not skills_root.is_dir():
        return sorted(set(errors + ["skills/ directory is required"]))
    skill_dirs = sorted(p for p in skills_root.iterdir() if p.is_dir() and not p.name.startswith((".", "_")))
    if not skill_dirs:
        errors.append("at least one skill directory is required")
    names: set[str] = set()
    for folder in skill_dirs:
        if not SLUG.fullmatch(folder.name):
            errors.append(f"skills/{folder.name}: directory must be lowercase kebab-case")
        skill_file = folder / "SKILL.md"
        if not skill_file.is_file() or skill_file.is_symlink():
            errors.append(f"skills/{folder.name}/SKILL.md must be a regular file")
            continue
        try:
            text = skill_file.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"skills/{folder.name}/SKILL.md: cannot read file: {exc}")
            continue
        try:
            parsed = parse_frontmatter(text)
        except ValueError as exc:
            errors.append(f"skills/{folder.name}/SKILL.md: {exc}")
            continue
        if parsed is None:
            errors.append(f"skills/{folder.name}/SKILL.md: frontmatter must be a YAML mapping followed by an instruction body")
            continue
        fields, body = parsed
        name, description, version = fields.get("name"), fields.get("description"), fields.get("version")
        if not isinstance(name, str) or not name.strip() or name != folder.name:
            errors.append(f"skills/{folder.name}/SKILL.md: name must be a non-empty string matching the directory slug")
        elif name in names:
            errors.append(f"skills/{folder.name}/SKILL.md: duplicate skill name {name!r}")
        if isinstance(name, str):
            names.add(name)
        if not isinstance(description, str) or not description.strip():
            errors.append(f"skills/{folder.name}/SKILL.md: description must be a non-empty string")
        elif len(description) > 300:
            errors.append(f"skills/{folder.name}/SKILL.md: description exceeds 300 characters")
        if version is not None and (not isinstance(version, str) or not SEMVER.fullmatch(version)):
            errors.append(f"skills/{folder.name}/SKILL.md: version must be a semantic version string")
        if "metadata" in fields and not isinstance(fields["metadata"], dict):
            errors.append(f"skills/{folder.name}/SKILL.md: metadata must be a mapping")
        for match in REFERENCE.finditer(text):
            target = (folder / f"{match.group(1)}/{match.group(2)}").resolve()
            if folder.resolve() not in target.parents or not target.is_file():
                errors.append(f"skills/{folder.name}/SKILL.md: missing or unsafe reference {match.group(0)}")
        for item in folder.rglob("*"):
            if item.is_symlink():
                errors.append(f"skills/{folder.name}: symlinks are not allowed ({item.relative_to(root)})")
            if item.is_file() and (is_secret_name(item.name) or item.suffix.lower() in {".pem", ".key"}):
                errors.append(f"skills/{folder.name}: secret-shaped file is not allowed ({item.relative_to(root)})")
        agent_metadata = folder / "agents" / "openai.yaml"
        if agent_metadata.exists():
            errors.extend(validate_agent_metadata(agent_metadata))
        if not body.strip():
            errors.append(f"skills/{folder.name}/SKILL.md: instructions must not be empty")

    for path in root.rglob("*"):
        if path.is_dir() and path.name == "__pycache__":
            continue
        if path.is_dir() and path.name == "node_modules":
            errors.append(f"transient or dependency directory is not allowed: {path.relative_to(root)}")
        if path.is_file() and is_secret_name(path.name):
            errors.append(f"secret-shaped file is not allowed: {path.relative_to(root)}")
        if path.is_symlink():
            errors.append(f"symlinks are not allowed: {path.relative_to(root)}")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Validation failed with {len(errors)} issue(s).")
        return 1
    skills = sum(1 for p in (args.root / "skills").iterdir() if p.is_dir() and not p.name.startswith((".", "_")))
    print(f"Validated plugin package: {skills} skill folders, 3 square SVG assets, synchronized manifests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
