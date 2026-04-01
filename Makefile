PYTHON ?= python3

.PHONY: install install-dev install-docs lint format test coverage docs clean-docs

install:
	$(PYTHON) -m pip install -e .

install-dev:
	$(PYTHON) -m pip install -e ".[dev]"

install-docs:
	$(PYTHON) -m pip install -e ".[docs]"

lint:
	$(PYTHON) -m ruff check ct_reconstruction mri_denoising tests
	$(PYTHON) -m black --check ct_reconstruction mri_denoising tests

format:
	$(PYTHON) -m ruff check --fix ct_reconstruction mri_denoising tests
	$(PYTHON) -m black ct_reconstruction mri_denoising tests

test:
	$(PYTHON) -m pytest tests/ -v --tb=short

coverage:
	$(PYTHON) -m pytest tests/ --cov=ct_reconstruction --cov=mri_denoising --cov-report=term-missing

docs:
	$(PYTHON) -m sphinx -W -b html docs docs/_build/html

clean-docs:
	rm -rf docs/_build
