.PHONY: install seed api mcp demo evaluate test lint typecheck graph audit-report clean

install:
	uv sync

seed:
	uv run python scripts/seed_demo.py

api:
	uv run uvicorn operational_semantics.main:app --reload --host 0.0.0.0 --port 8000

mcp:
	uv run python -m operational_semantics.mcp_server.server

demo:
	uv run python scripts/run_demo.py

evaluate:
	uv run python scripts/run_evaluation.py

test:
	uv run pytest -v --tb=short

lint:
	uv run ruff format .
	uv run ruff check --fix .

typecheck:
	uv run mypy src

graph:
	uv run python scripts/export_graph.py

audit-report:
	uv run python scripts/export_audit_report.py

clean:
	rm -rf *.db *.sqlite3 __pycache__ .pytest_cache .ruff_cache .mypy_cache
	rm -rf data/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
