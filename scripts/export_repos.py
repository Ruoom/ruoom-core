import argparse
import hashlib
import json
import sys
from pathlib import Path


DEFAULT_MANIFEST = Path(__file__).resolve().parents[1] / "release" / "repos.json"
IGNORED_DESTINATION_PREFIXES = (".git/",)
IGNORED_DESTINATION_DIR_NAMES = {".git", "__pycache__", ".pytest_cache"}
IGNORED_SOURCE_DIR_NAMES = {".git", "__pycache__", ".pytest_cache"}


def _normalize_relpath(path_str):
    normalized = Path(path_str).as_posix()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.rstrip("/")


def load_manifest(manifest_path):
    with manifest_path.open(encoding="utf-8") as manifest_file:
        return json.load(manifest_file)


def iter_manifest_entries(manifest, package_filter=None):
    entries = [("core", manifest["core"])]
    entries.extend(sorted(manifest["plugins"].items()))
    if package_filter:
        entries = [(name, entry) for name, entry in entries if name == package_filter]
        if not entries:
            raise KeyError(f"Unknown package '{package_filter}'.")
    return entries


def is_excluded(source_relpath, exclude_prefixes):
    normalized = _normalize_relpath(source_relpath)
    for prefix in exclude_prefixes:
        if normalized == prefix or normalized.startswith(prefix + "/"):
            return True
    return False


def build_export_mappings(repo_root, entry):
    source_root = (repo_root / entry["source"]).resolve()
    include_prefixes = entry["export"]["include"]
    exclude_prefixes = tuple(_normalize_relpath(item) for item in entry["export"].get("exclude", []))
    seen = {}

    for include_prefix in include_prefixes:
        include_path = (repo_root / include_prefix).resolve()
        if not include_path.exists():
            raise FileNotFoundError(f"Manifest include path does not exist: {include_prefix}")

        if include_path.is_file():
            candidates = [include_path]
        else:
            candidates = sorted(
                path
                for path in include_path.rglob("*")
                if path.is_file() and not any(part in IGNORED_SOURCE_DIR_NAMES for part in path.parts)
            )
        for candidate in candidates:
            source_rel = candidate.relative_to(repo_root).as_posix()
            if is_excluded(source_rel, exclude_prefixes):
                continue

            try:
                destination_rel = candidate.relative_to(source_root).as_posix()
            except ValueError:
                destination_rel = candidate.name

            seen[source_rel] = destination_rel

    return sorted(seen.items())


def hash_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for chunk in iter(lambda: source_file.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_destination_files(destination_root):
    files = {}
    for path in sorted(destination_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(destination_root).as_posix()
        if any(part in IGNORED_DESTINATION_DIR_NAMES for part in Path(relative).parts):
            continue
        if any(relative == prefix.rstrip("/") or relative.startswith(prefix) for prefix in IGNORED_DESTINATION_PREFIXES):
            continue
        files[relative] = path
    return files


def run_dry_run(repo_root, manifest, package_filter):
    for package_name, entry in iter_manifest_entries(manifest, package_filter):
        mappings = build_export_mappings(repo_root, entry)
        print(f"PACKAGE {package_name}")
        print(f"  source: {entry['source']}")
        print(f"  destination: {entry['repo']}")
        print(f"  files: {len(mappings)}")
        print(f"  test_command: {entry['test_command']}")
        for source_rel, destination_rel in mappings[:10]:
            print(f"    {source_rel} -> {destination_rel}")
        if len(mappings) > 10:
            print(f"    ... {len(mappings) - 10} more")


def run_check_drift(repo_root, manifest, package_name, destination_root):
    entry = dict(iter_manifest_entries(manifest, package_name))[package_name]
    expected_mappings = build_export_mappings(repo_root, entry)
    expected_by_destination = {destination_rel: source_rel for source_rel, destination_rel in expected_mappings}
    actual_files = collect_destination_files(destination_root)

    missing = sorted(set(expected_by_destination) - set(actual_files))
    extra = sorted(set(actual_files) - set(expected_by_destination))
    changed = []

    for destination_rel, source_rel in expected_by_destination.items():
        if destination_rel not in actual_files:
            continue
        source_path = repo_root / source_rel
        destination_path = actual_files[destination_rel]
        if hash_file(source_path) != hash_file(destination_path):
            changed.append(destination_rel)

    if not missing and not extra and not changed:
        print(f"DRIFT CHECK PASSED for {package_name}")
        return 0

    print(f"DRIFT CHECK FAILED for {package_name}")
    if missing:
        print("  missing:")
        for item in missing[:20]:
            print(f"    {item}")
        if len(missing) > 20:
            print(f"    ... {len(missing) - 20} more")
    if extra:
        print("  extra:")
        for item in extra[:20]:
            print(f"    {item}")
        if len(extra) > 20:
            print(f"    ... {len(extra) - 20} more")
    if changed:
        print("  changed:")
        for item in changed[:20]:
            print(f"    {item}")
        if len(changed) > 20:
            print(f"    ... {len(changed) - 20} more")
    return 1


def parse_args():
    parser = argparse.ArgumentParser(description="Release manifest dry-run and drift-check tooling.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Path to the release manifest JSON file.")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Source repo root used to resolve manifest include paths.",
    )
    parser.add_argument("--package", help="Filter to a single package name such as 'core' or 'booking'.")
    parser.add_argument(
        "--action",
        choices=("dry-run", "check-drift"),
        default="dry-run",
        help="Perform a dry-run summary or compare one package against a destination repo checkout.",
    )
    parser.add_argument(
        "--destination",
        help="Destination repo root used by --action check-drift.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    manifest_path = Path(args.manifest).resolve()
    manifest = load_manifest(manifest_path)

    try:
        if args.action == "dry-run":
            run_dry_run(repo_root, manifest, args.package)
            return 0

        if not args.package:
            raise ValueError("--package is required for --action check-drift.")
        if not args.destination:
            raise ValueError("--destination is required for --action check-drift.")

        destination_root = Path(args.destination).resolve()
        if not destination_root.exists():
            raise FileNotFoundError(f"Destination path does not exist: {destination_root}")

        return run_check_drift(repo_root, manifest, args.package, destination_root)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
