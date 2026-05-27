# Operational Semantics Lab

A governed knowledge layer for enterprise agents — ontology, policy, approval, provenance.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## What this is

A complete, runnable Python research repository demonstrating how enterprise agents can safely move from retrieving information to proposing and executing governed SaaS write operations through:

- A minimal operational ontology (RDF/Turtle + SHACL)
- A graph of actors, roles, actions, policies, evidence, approvals, executions, outcomes, and audit records
- Deterministic policy evaluation (YAML-defined, no LLM dependency)
- Payload-bound approval with SHA-256 integrity verification
- A governed tool gateway separating read / propose-write / execute-write
- A provenance ledger with hash-chained audit events
- Three synthetic SaaS adapters (Jira, Slack, CRM)
- 25 competency scenarios with comparative evaluation (`rag_only` → `graph_grounded` → `operational_semantics`)

## Quickstart

```bash
git clone https://github.com/rmax-ai/operational-semantics-lab
cd operational-semantics-lab
uv sync
uv run python scripts/seed_demo.py
uv run python scripts/run_demo.py
uv run pytest
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the component diagram, lifecycle flows, and data model.

## Research Thesis

> Enterprise agents require more than document retrieval and tool access. Once an agent can change external systems, its knowledge layer must represent action semantics, policy constraints, approval requirements, supporting evidence, resulting outcomes, and durable provenance.

See [ARTICLE_COMPANION.md](ARTICLE_COMPANION.md) for the mapping between article concepts and repository artefacts.

## Commands

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies |
| `make seed` | Seed demo data |
| `make api` | Start FastAPI server |
| `make mcp` | Start MCP server |
| `make demo` | Run terminal demo |
| `make evaluate` | Run evaluation suite |
| `make test` | Run all tests |
| `make lint` | Format and lint |
| `make typecheck` | Run mypy |
| `make graph` | Export RDF graph |
| `make audit-report` | Export audit report |

## License

MIT
