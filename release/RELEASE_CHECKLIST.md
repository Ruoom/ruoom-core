# Release Checklist

Use this checklist before exporting core or plugin repositories from the open-core integration repo.

## 1. Confirm the source repo state

- Work from `C:\Ruoom\ruoom branch3\ruoom-collab`.
- Confirm the intended branch and release commit.
- Review `git status` and decide whether a dirty worktree is acceptable for the release.
- Update `release/repos.json` if package metadata, dependencies, or export rules changed.

## 2. Validate the release manifest

- Run:

```powershell
.\.venv\Scripts\python.exe scripts\export_repos.py --action dry-run
```

- Review package names, source folders, destination repos, test commands, and file counts.

## 3. Run tests

- Run the smoke suite:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_tests.ps1 tests\smoke -q
```

- Run focused plugin tests for every changed plugin using the test commands in `release/repos.json`.
- Run `.\.venv\Scripts\python.exe manage.py check`.

## 4. Check drift against a destination repo checkout

- For a plugin checkout that exists locally, run:

```powershell
.\.venv\Scripts\python.exe scripts\export_repos.py --action check-drift --package booking --destination C:\path\to\booking-plugin
```

- Resolve any missing, extra, or changed files before export.

## 5. Export readiness review

- Verify required and optional dependencies still match `PLUGIN_METADATA`.
- Confirm any new migrations, templates, static assets, and tests are included by the export rules.
- Review version placeholders or package versions for changed packages.
- Confirm release-specific docs under `release/` are current.

## 6. Publish/export follow-up

- Export the target package repos using the approved manifest and file rules.
- Commit exported changes in the destination repos with the same release identifier.
- Tag compatible versions only after exported repos pass their own validation.
