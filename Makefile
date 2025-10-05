# ---- Project settings -------------------------------------------------------
VENV ?= .venv
PY    := $(VENV)/bin/python
PIP   := $(VENV)/bin/pip
PTW   := $(VENV)/bin/ptw
PYTEST:= $(VENV)/bin/pytest

# ---- Helpers ----------------------------------------------------------------
.DEFAULT_GOAL := help

## help: Show this help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | sed 's/:.*##/: /' | sort

## venv: Create local virtualenv in .venv
venv:
	python3 -m venv $(VENV)
	@echo "→ Activate with: source $(VENV)/bin/activate"

## deps: Install runtime & dev dependencies
deps:
	$(PIP) install -U pip wheel
	@if [ -f requirements.txt ]; then $(PIP) install -r requirements.txt; fi
	@if [ -f requirements-dev.txt ]; then $(PIP) install -r requirements-dev.txt; fi

## test: Run the test suite (respects pytest.ini)
test:
	$(PYTEST)

## testv: Verbose test run
testv:
	$(PYTEST) -v

## watch: Auto-rerun tests on file save (pytest-watch)
watch:
	$(PTW) \
	  --runner "$(PYTEST) -q" \
	  --onpass "printf '\n✅ tests green\n'" \
	  --onfail "printf '\n❌ tests failed\n'" \
	  --ignore .git --ignore $(VENV) --ignore .direnv

## clean: Remove caches and pyc files
clean:
	find . -name "__pycache__" -type d -exec rm -rf {} +; \
	find . -name "*.pyc" -delete

.PHONY: help venv deps test testv watch clean
