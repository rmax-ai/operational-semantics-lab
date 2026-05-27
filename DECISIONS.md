# Architectural Decisions

## ADR-001: Deterministic Governance Core with Optional LLM Layer
**Decision:** The system core (policy, approval, execution, audit) is fully deterministic. An optional LLM layer may generate proposals but never makes governance decisions.
**Rationale:** Ensures safety guarantees are independent of model quality. The research contribution is the governance substrate itself.
**Rejected alternative:** Fully LLM-based policy evaluation — non-deterministic, testable guarantees impossible.

## ADR-002: SQLite Rather Than Graph Database
**Decision:** Use SQLite for persistence and RDFLib for in-memory graph construction.
**Rationale:** Zero configuration, perfectly adequate for a research prototype. A graph database would add deployment complexity without research value at this stage.
**Trade-off:** Graph queries require loading into RDFLib rather than native SPARQL endpoint.

## ADR-003: RDF/SHACL Retained for Semantic Validation
**Decision:** Use RDFLib for RDF graph construction and pyshacl for SHACL validation at runtime.
**Rationale:** Demonstrates that semantic validation is feasible without a graph database. The ontology is actively used, not decorative.
**Trade-off:** Performance limits for large graphs — acceptable for research prototype.

## ADR-004: Python Policy Evaluator Default, OPA Optional
**Decision:** Built-in deterministic YAML-based policy evaluator is the default. OPA adapter satisfies the same interface but is optional and not tested in CI.
**Rationale:** Zero external dependency for core functionality. OPA demonstrates production extensibility.
**Trade-off:** Policy definition lacks OPA's ecosystem but is simpler to understand and debug.

## ADR-005: Payload-Bound Approval Using SHA-256
**Decision:** Approval binds to the exact canonical SHA-256 hash of the proposed payload.
**Rationale:** Any payload modification (even whitespace or key ordering) invalidates the approval. Canonical JSON encoding ensures determinism.
**Trade-off:** Cannot approve "similar" payloads — any change requires re-approval.

## ADR-006: Synthetic SaaS Adapters
**Decision:** Implement Jira, Slack, and CRM as local in-memory/SQLite adapters rather than real integrations.
**Rationale:** Zero cloud dependencies, fully controlled test scenarios, instant reproducibility.
**Trade-off:** Not a production integration — but the adapter interface is clean enough that real connectors could replace them.

## ADR-007: Business-Level Provenance (Not Transcript Storage)
**Decision:** Provenance records structured business events (proposal, evidence, policy decision, approval, execution, outcome) — not raw LLM chain-of-thought or tool call transcripts.
**Rationale:** Audit records should answer governance questions ("why was this action taken?") not reconstruct LLM reasoning. Hidden chain-of-thought is explicitly excluded.
**Trade-off:** Cannot debug LLM behavior from audit records — but that's not the purpose of this system.

## ADR-008: src-layout with Hatch Build Backend
**Decision:** Use `src/operational_semantics/` layout with Hatch as the build backend.
**Rationale:** Prevents import confusion, follows Python packaging best practices, works cleanly with uv.
