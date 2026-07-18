# Testing

Run the standard open-core test gate with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_tests.ps1 -q
```

For plugin-local checks, run the `test_command` listed for each package in `release/repos.json`.

To generate the core coverage report locally:

```powershell
python -m coverage run --branch --rcfile=.coveragerc -m pytest
python -m coverage report --rcfile=.coveragerc
```

For release/export validation, run:

```powershell
python scripts\export_repos.py --action dry-run
```
