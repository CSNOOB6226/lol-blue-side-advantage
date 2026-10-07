PY ?= python3

.PHONY: all analysis data figures audit test check clean

# Full analysis + figures from the committed derived table (no raw data needed)
all analysis:
	$(PY) run_all.py

# Rebuild everything from raw Oracle's Elixir CSVs in data/raw/
data:
	$(PY) run_all.py --from-raw

figures:
	$(PY) src/figures.py

audit:
	$(PY) src/paper_claim_audit.py

test:
	$(PY) -m unittest discover -s tests

check: test audit

clean:
	rm -f results/*.txt results/*.csv figures/*.png figures/en/*.png
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
