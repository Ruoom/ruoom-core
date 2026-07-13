import json
import subprocess
import sys
import tempfile
from pathlib import Path


def _workspace_tempdir():
    base_dir = Path(__file__).resolve().parents[2] / ".tmp-test-export"
    base_dir.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=base_dir)


def _write_manifest(tmp_path):
    manifest = {
        "schema_version": 1,
        "core": {
            "source": ".",
            "package": "demo-core",
            "version": "1.0.0",
            "repo": "https://example.com/demo-core",
            "test_command": "pytest -q",
            "dependencies": {"required": [], "optional": []},
            "export": {
                "include": ["pkg", "README.md"],
                "exclude": ["pkg/__pycache__"],
            },
        },
        "plugins": {
            "demo": {
                "source": "pkg",
                "package": "demo-plugin",
                "version": "1.0.0",
                "repo": "https://example.com/demo-plugin",
                "test_command": "pytest pkg/tests -q",
                "dependencies": {"required": [], "optional": []},
                "export": {
                    "include": ["pkg"],
                    "exclude": ["pkg/__pycache__"],
                },
            }
        },
    }
    manifest_path = tmp_path / "repos.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def _run_export_script(cwd, *args):
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "export_repos.py"
    return subprocess.run(
        [sys.executable, str(script_path), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def test_export_script_dry_run_prints_source_and_destination():
    with _workspace_tempdir() as temp_dir:
        temp_path = Path(temp_dir)
        source_dir = temp_path / "source"
        package_dir = source_dir / "pkg"
        package_dir.mkdir(parents=True)
        (package_dir / "module.py").write_text("print('demo')\n", encoding="utf-8")
        (source_dir / "README.md").write_text("# Demo\n", encoding="utf-8")
        manifest_path = _write_manifest(temp_path)

        result = _run_export_script(
            source_dir,
            "--repo-root",
            str(source_dir),
            "--manifest",
            str(manifest_path),
            "--action",
            "dry-run",
            "--package",
            "demo",
        )

        assert result.returncode == 0
        assert "PACKAGE demo" in result.stdout
        assert "source: pkg" in result.stdout
        assert "destination: https://example.com/demo-plugin" in result.stdout


def test_export_script_check_drift_passes_for_matching_destination():
    with _workspace_tempdir() as temp_dir:
        temp_path = Path(temp_dir)
        source_dir = temp_path / "source"
        package_dir = source_dir / "pkg"
        package_dir.mkdir(parents=True)
        (package_dir / "module.py").write_text("print('demo')\n", encoding="utf-8")
        manifest_path = _write_manifest(temp_path)

        destination_dir = temp_path / "destination"
        destination_dir.mkdir()
        (destination_dir / "module.py").write_text("print('demo')\n", encoding="utf-8")

        result = _run_export_script(
            source_dir,
            "--repo-root",
            str(source_dir),
            "--manifest",
            str(manifest_path),
            "--action",
            "check-drift",
            "--package",
            "demo",
            "--destination",
            str(destination_dir),
        )

        assert result.returncode == 0
        assert "DRIFT CHECK PASSED for demo" in result.stdout


def test_export_script_check_drift_reports_missing_or_changed_files():
    with _workspace_tempdir() as temp_dir:
        temp_path = Path(temp_dir)
        source_dir = temp_path / "source"
        package_dir = source_dir / "pkg"
        package_dir.mkdir(parents=True)
        (package_dir / "module.py").write_text("print('demo')\n", encoding="utf-8")
        manifest_path = _write_manifest(temp_path)

        destination_dir = temp_path / "destination"
        destination_dir.mkdir()
        (destination_dir / "module.py").write_text("print('changed')\n", encoding="utf-8")
        (destination_dir / "extra.py").write_text("print('extra')\n", encoding="utf-8")

        result = _run_export_script(
            source_dir,
            "--repo-root",
            str(source_dir),
            "--manifest",
            str(manifest_path),
            "--action",
            "check-drift",
            "--package",
            "demo",
            "--destination",
            str(destination_dir),
        )

        assert result.returncode == 1
        assert "DRIFT CHECK FAILED for demo" in result.stdout
        assert "extra.py" in result.stdout
        assert "module.py" in result.stdout
