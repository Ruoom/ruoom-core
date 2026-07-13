import json
from pathlib import Path

from ruoom.plugin_metadata import get_enabled_plugin_names, load_plugin_metadata


def _load_release_manifest():
    manifest_path = Path(__file__).resolve().parents[2] / "release" / "repos.json"
    with manifest_path.open(encoding="utf-8") as manifest_file:
        return json.load(manifest_file)


def test_release_manifest_has_core_and_all_enabled_plugin_entries():
    manifest = _load_release_manifest()

    assert manifest["schema_version"] == 1
    assert "core" in manifest
    assert "plugins" in manifest
    assert set(manifest["plugins"]) == set(get_enabled_plugin_names())


def test_release_manifest_core_entry_has_required_fields():
    core = _load_release_manifest()["core"]

    assert core["source"] == "."
    assert core["package"] == "ruoom-core"
    assert core["version"]
    assert core["repo"].startswith("https://github.com/ruoom/")
    assert core["test_command"]
    assert core["dependencies"] == {"required": [], "optional": []}
    assert "release" in core["export"]["include"]
    assert "include" in core["export"]
    assert "exclude" in core["export"]


def test_release_manifest_plugin_entries_match_plugin_metadata():
    manifest_plugins = _load_release_manifest()["plugins"]

    for plugin_name, manifest_entry in manifest_plugins.items():
        metadata = load_plugin_metadata(plugin_name)

        assert metadata is not None
        assert manifest_entry["source"] == f"plugins/{plugin_name}"
        assert manifest_entry["package"] == metadata.export_package_name
        assert manifest_entry["version"] == metadata.package_version
        assert manifest_entry["repo"] == metadata.repository_url
        assert manifest_entry["test_command"] == metadata.test_command
        assert manifest_entry["dependencies"]["required"] == list(metadata.dependencies)
        assert manifest_entry["dependencies"]["optional"] == list(metadata.optional_dependencies)
        assert manifest_entry["export"]["include"] == [f"plugins/{plugin_name}"]
