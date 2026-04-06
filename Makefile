.PHONY: test lint benchmark quality preflight smoke

PYTHON ?= .venv/bin/python

test:
	$(PYTHON) -m pytest tests/ -q

lint:
	$(PYTHON) -m ruff check markcrawl/ tests/ benchmarks/

benchmark:
	$(PYTHON) benchmarks/benchmark_all_tools.py

quality:
	$(PYTHON) benchmarks/benchmark_quality.py

preflight: lint test

smoke:
	$(PYTHON) -c "from markcrawl import crawl; print('import OK')"
