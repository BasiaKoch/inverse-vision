# Contributing

## Development setup

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pip install -e ".[docs]"
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
pytest tests/ --cov=ct_reconstruction --cov=mri_denoising --cov-report=term-missing
```

## Building docs

```bash
python -m sphinx -W -b html docs docs/_build/html
```

## Code style

- **black** for formatting (line length 100).
- **ruff** for linting and import sorting (`ruff --fix`).
- NumPy-style docstrings for all public functions.
- Sphinx-compatible API docs live under `docs/`.

## Branch workflow

- Work on feature branches: `git checkout -b feat/my-change`
- Keep `main` passing CI at all times.
- Open a pull request and ensure all checks pass before merging.
- Protect `main` by requiring CI status checks before merge when using GitHub.

## Module 3 note

All written content in `report/report.txt` for the literature review section
must be original student work.  Generative AI must not be used for that
section per the coursework specification.
