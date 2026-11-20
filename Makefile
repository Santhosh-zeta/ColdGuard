# Run from the repository root with GNU Make.
PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python)
NPM ?= npm
HOST ?= 127.0.0.1
API_PORT ?= 8000
WEB_PORT ?= 8501

.DEFAULT_GOAL := help
.PHONY: help install test lint api web mobile-test

help:
	@printf '%s\n' 'ColdGuard development targets:' '  install      Install Python and mobile dependencies' '  test         Run Python tests' '  lint         Run CI Ruff checks' '  api          Start the local API' '  web          Start the local Streamlit app' '  mobile-test  Run mobile Jest tests'

install:
	"$(PYTHON)" -m pip install -r requirements.txt
	$(NPM) --prefix mobile_app ci --no-audit --no-fund

test:
	"$(PYTHON)" -m pytest tests/ -v --tb=short

lint:
	"$(PYTHON)" -m ruff check core/ api/ tests/ simulation/ validation/ coldguard_cli.py --select E,W,F --ignore E501

api:
	"$(PYTHON)" -m uvicorn api.main:app --host "$(HOST)" --port "$(API_PORT)" --reload

web:
	"$(PYTHON)" -m streamlit run web_app/app.py --server.address "$(HOST)" --server.port "$(WEB_PORT)" --server.headless true

mobile-test:
	$(NPM) --prefix mobile_app test -- --ci --passWithNoTests
