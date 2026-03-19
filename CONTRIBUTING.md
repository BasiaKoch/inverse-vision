# Contributing

## Development setup

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install          # installs commit-time hooks
pre-commit install --hook-type pre-push   # installs push-time pytest hook
```

## Pre-commit hooks

Hooks run automatically on every `git commit` (formatting + linting) and
every `git push` (full test suite).  To run them manually:

```bash
pre-commit run --all-files
```

## Running tests

```bash
pytest tests/ -v
pytest tests/test_mri.py -v     # MRI module only
pytest tests/test_ct.py  -v     # CT module only
```

## Code style

- **black** for formatting (line length 100).
- **ruff** for linting and import sorting (`ruff --fix`).
- NumPy-style docstrings for all public functions.

## Branch workflow

- Work on feature branches: `git checkout -b feat/my-change`
- Keep `main` passing CI at all times.
- Open a pull request and ensure all checks pass before merging.

## Module 3 note

All written content in `report.txt` for the literature review section
must be original student work.  Generative AI must not be used for that
section per the coursework specification.
