PY ?= python3
PIP ?= $(PY) -m pip

.PHONY: setup lint format test cov pre-commit

setup:
	$(PIP) install -r requirements.txt || true
	$(PIP) install -r dev-requirements.txt || true

lint:
	ruff check .
	black --check .

format:
	black .
	ruff check . --fix

test:
	$(PY) -m pytest -q

cov:
	$(PY) -m pytest -q && cat coverage.xml | head -n 5

pre-commit:
	pre-commit install