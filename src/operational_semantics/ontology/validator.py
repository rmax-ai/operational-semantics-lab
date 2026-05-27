"""SHACL validation using pyshacl for operational semantics domain objects."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel
from rdflib import Graph

from operational_semantics.domain.models import (
    ActionProposal,
    Approval,
    AuditRecord,
    Evidence,
    Execution,
)
from operational_semantics.ontology.graph_builder import GraphBuilder
from operational_semantics.ontology.namespace import PREFIX_MAP


class ValidationResult(BaseModel):
    """A single SHACL validation result."""

    path: str = ""
    value: str = ""
    message: str = ""


class ValidationReport(BaseModel):
    """Structured SHACL validation report."""

    conforms: bool
    results: list[ValidationResult] = []
    result_count: int = 0
    shapes_graph_well_formed: bool = True

    @property
    def summary(self) -> str:
        """Return a human-readable summary."""
        if self.conforms:
            return "SHACL validation: PASS"
        return f"SHACL validation: FAILED ({self.result_count} violations)"


def _load_shapes() -> Graph:
    """Load the SHACL shapes graph from the ontology directory."""
    import os as std_os

    # Search for shapes.ttl relative to this file or in the project root
    search_paths = [
        Path(__file__).parent.parent.parent.parent.parent / "ontology" / "shapes.ttl",
        Path.cwd() / "ontology" / "shapes.ttl",
    ]
    for sp in search_paths:
        if sp.exists():
            shapes = Graph()
            for prefix, ns in PREFIX_MAP.items():
                shapes.bind(prefix, ns)
            shapes.parse(str(sp), format="turtle")
            return shapes

    msg = "shapes.ttl not found. Checked: " + ", ".join(str(p) for p in search_paths)
    raise FileNotFoundError(msg)


def _run_shacl(data_graph: Graph, shapes_graph: Graph | None = None) -> ValidationReport:
    """Run pyshacl validation and return a structured report."""
    from pyshacl import validate

    if shapes_graph is None:
        shapes_graph = _load_shapes()

    conforms, results_graph, results_text = validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
        abort_on_first=False,
        meta_shacl=False,
        debug=False,
    )

    # Parse results
    results: list[ValidationResult] = []
    if results_graph is not None:
        from rdflib import RDF as RDF_TERM
        from rdflib import SH as SH_TERM

        for result_node in results_graph.subjects(RDF_TERM.type, SH_TERM.ValidationResult):
            msgs = list(results_graph.objects(result_node, SH_TERM.resultMessage))
            paths = list(results_graph.objects(result_node, SH_TERM.resultPath))
            values = list(results_graph.objects(result_node, SH_TERM.value))

            results.append(
                ValidationResult(
                    path=str(paths[0]) if paths else "",
                    value=str(values[0]) if values else "",
                    message=str(msgs[0]) if msgs else "",
                )
            )

    return ValidationReport(
        conforms=bool(conforms),
        results=results,
        result_count=len(results),
    )


class SHACLValidator:
    """Validates domain objects against SHACL constraint shapes."""

    def __init__(self, shapes_graph: Graph | None = None) -> None:
        self._shapes_graph = shapes_graph

    def _get_shapes(self) -> Graph:
        if self._shapes_graph is not None:
            return self._shapes_graph
        return _load_shapes()

    def validate_proposal(self, proposal: ActionProposal, evidence: list[Evidence] | None = None) -> ValidationReport:
        """Validate an action proposal against SHACL shapes."""
        data = GraphBuilder.build_proposal_graph(proposal)
        if evidence:
            for ev in (evidence or []):
                data += GraphBuilder.build_evidence_graph(ev)
        return _run_shacl(data, self._get_shapes())

    def validate_approval(self, approval: Approval) -> ValidationReport:
        """Validate an approval against SHACL shapes."""
        data = GraphBuilder.build_approval_graph(approval)
        return _run_shacl(data, self._get_shapes())

    def validate_execution(self, execution: Execution) -> ValidationReport:
        """Validate an execution against SHACL shapes."""
        data = GraphBuilder.build_execution_graph(execution)
        return _run_shacl(data, self._get_shapes())

    def validate_audit_record(self, record: AuditRecord) -> ValidationReport:
        """Validate an audit record against SHACL shapes."""
        data = GraphBuilder.build_audit_record_graph(record)
        return _run_shacl(data, self._get_shapes())

    def validate_graph(self, data_graph: Graph) -> ValidationReport:
        """Validate an arbitrary RDFLib Graph against all shapes."""
        return _run_shacl(data_graph, self._get_shapes())
