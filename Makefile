PY ?= python3
PIP ?= $(PY) -m pip

.PHONY: setup lint format test cov pre-commit

setup:
	python3 -m venv .venv && . .venv/bin/activate && pip install -r dev-requirements.txt -r requirements.txt

lint:
	ruff check .

format:
	black .

typecheck:
	mypy msf || true

safety:
	safety check -r requirements.txt || true

test:
	pytest -q

cov:
	pytest -q --cov=msf --cov-report=term-missing:skip-covered --cov-report=xml

pre-commit:
	ruff check . && black --check . && mypy msf || true && pytest -q