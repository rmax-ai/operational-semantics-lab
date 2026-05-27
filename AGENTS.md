# AGENTS.md — Operational Semantics Lab

This document captures conventions and rules for all contributors and AI coding agents working on this repository.

---

## 1. Core Principles

- **Proposal ≠ Execution** — Never conflate proposing an action with executing it
- **Deterministic governance core** — Policy decisions, approval binding, and audit must never depend on an LLM
- **Payload-bound approval** — An approval is valid only for the exact SHA-256 hash of the approved payload
- **No real SaaS writes** — All external-system interactions go through synthetic adapters backed by SQLite
- **Gateway is the only path** — No code outside the governed gateway may mutate synthetic system state

## 2. Code Organisation

- `src/operational_semantics/` — Python package (src-layout)
- Domain logic in `domain/`, persistence in `persistence/`, ontology in `ontology/`
- API routes in `api/`, MCP server in `mcp_server/`, tools in `tools/`
- Policy engine in `policy/`, approvals in `approvals/`, provenance in `provenance/`
- Use cases in `use_cases/`, evaluation in `evaluation/`
- Tests mirror source structure under `tests/unit/`, `tests/integration/`, `tests/evaluation/`

## 3. Error Handling

- Define structured error types in `domain/errors.py`
- API endpoints return appropriate HTTP status codes (422, 403, 409, 201)
- Never silently swallow exceptions
- Use `Result`-like patterns or raise typed exceptions — no bare `except:`

## 4. Testing

- All tests must use temporary DB fixtures — no shared state between tests
- Unit tests: per-module, fast, no network
- Integration tests: full workflow from proposal → execution
- Evaluation tests: competency scenarios, comparative configs
- `uv run pytest` must pass before any commit

## 5. Critical Rules

- ❌ Do NOT bypass the governed gateway to write to synthetic systems
- ❌ Do NOT add real SaaS credentials
- ❌ Do NOT convert deterministic policy decisions into LLM judgments
- ❌ Do NOT skip SHACL validation in any execution path
- ❌ Do NOT leave placeholder implementations as working features
- ✅ Always run `uv run ruff format . && uv run ruff check --fix . && uv run mypy src` before committing
- ✅ Update docs when altering domain concepts or lifecycle behavior
