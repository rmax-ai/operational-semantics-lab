"""Build RDFLib graphs from domain models."""

from datetime import datetime
from typing import Any

import rdflib
from rdflib import BNode, Graph, Literal, URIRef

from operational_semantics.domain.models import (
    ActionProposal,
    Actor,
    Approval,
    AuditRecord,
    Evidence,
    Execution,
    Outcome,
    PolicyDecision,
    SaaSResource,
    Tool,
)
from operational_semantics.ontology.namespace import OS, RDF, RDFS, XSD, PREFIX_MAP


def _bind_prefixes(graph: Graph) -> None:
    """Bind standard prefixes to a graph for clean serialization."""
    for prefix, ns in PREFIX_MAP.items():
        graph.bind(prefix, ns)


def _uri(resource_id: str) -> URIRef:
    """Convert a domain resource ID to a full URI."""
    return OS[resource_id]


def _literal(value: Any, datatype: URIRef | None = None) -> Literal:
    """Create a typed literal."""
    if isinstance(value, datetime):
        return Literal(value.isoformat(), datatype=XSD.dateTime)
    if isinstance(value, bool):
        return Literal(str(value).lower(), datatype=XSD.boolean)
    if datatype:
        return Literal(str(value), datatype=datatype)
    return Literal(str(value))


class GraphBuilder:
    """Constructs RDFLib graphs from domain models.

    Builds individual sub-graphs for each entity type, or a combined
    domain graph spanning all entities in a workflow.
    """

    @staticmethod
    def build_actor_graph(actor: Actor) -> Graph:
        """Build an RDF graph for an actor and their roles."""
        g = Graph()
        _bind_prefixes(g)

        actor_uri = _uri(actor.id)
        actor_type = OS.HumanActor  # default
        g.add((actor_uri, RDF.type, actor_type))
        g.add((actor_uri, RDFS.label, _literal(actor.name)))

        for role_id in actor.role_ids:
            role_uri = _uri(role_id)
            g.add((role_uri, RDF.type, OS.Role))
            g.add((actor_uri, OS.holdsRole, role_uri))

        return g

    @staticmethod
    def build_evidence_graph(evidence: Evidence) -> Graph:
        """Build an RDF graph for an evidence item."""
        g = Graph()
        _bind_prefixes(g)

        ev_uri = _uri(evidence.id)
        g.add((ev_uri, RDF.type, OS.Evidence))
        g.add((ev_uri, OS.evidenceType, _literal(evidence.evidence_type.value)))
        g.add((ev_uri, RDFS.label, _literal(evidence.content[:100])))
        g.add((ev_uri, OS.externalReference, _literal(evidence.source)))
        g.add((ev_uri, OS.timestamp, _literal(evidence.recorded_at)))

        return g

    @staticmethod
    def build_proposal_graph(
        proposal: ActionProposal,
        action_type: str = "WriteAction",
    ) -> Graph:
        """Build an RDF graph for an action proposal.

        Creates both the ActionProposal node and the embedded Action node.
        """
        g = Graph()
        _bind_prefixes(g)

        prop_uri = _uri(proposal.id)
        g.add((prop_uri, RDF.type, OS.ActionProposal))
        g.add((prop_uri, OS.actionType, _literal(proposal.action_type)))
        g.add((prop_uri, OS.operationClass, _literal(proposal.operation_class.value)))
        g.add((prop_uri, OS.payloadHash, _literal(proposal.payload_hash)))
        g.add((prop_uri, OS.containsRestrictedData, _literal(proposal.contains_restricted_data)))
        g.add((prop_uri, OS.timestamp, _literal(proposal.proposed_at)))

        # Create action node
        action_uri = _uri(f"{proposal.id}-action")
        action_type_uri = OS.WriteAction if "write" in proposal.operation_class.value else OS.ReadAction
        g.add((action_uri, RDF.type, action_type_uri))
        g.add((action_uri, OS.actionType, _literal(proposal.action_type)))
        g.add((action_uri, OS.operationClass, _literal(proposal.operation_class.value)))
        g.add((action_uri, OS.riskLevel, _literal(proposal.risk_level.value)))
        g.add((prop_uri, OS.proposedAction, action_uri))

        # Target resource
        target_uri = _uri(proposal.target_resource_id)
        g.add((prop_uri, OS.targets, target_uri))

        # Evidence references
        for ev_id in proposal.evidence_ids:
            ev_uri = _uri(ev_id)
            g.add((prop_uri, OS.supportedBy, ev_uri))
            g.add((prop_uri, OS.referencesEvidence, ev_uri))

        # Actor
        actor_uri = _uri(proposal.actor_id)
        g.add((actor_uri, OS.proposes, prop_uri))

        return g

    @staticmethod
    def build_policy_decision_graph(decision: PolicyDecision) -> Graph:
        """Build an RDF graph for a policy decision."""
        g = Graph()
        _bind_prefixes(g)

        dec_uri = _uri(decision.id)
        g.add((dec_uri, RDF.type, OS.PolicyDecision))
        g.add((dec_uri, OS.decisionType, _literal(decision.decision.value)))
        g.add((dec_uri, OS.requiredApproverRole, _literal(decision.required_approver_role or "")))
        g.add((dec_uri, OS.timestamp, _literal(decision.evaluated_at)))
        if decision.explanation:
            g.add((dec_uri, RDFS.comment, _literal(decision.explanation)))

        # Link to proposal
        prop_uri = _uri(decision.proposal_id)
        g.add((prop_uri, OS.hasPolicyDecision, dec_uri))

        return g

    @staticmethod
    def build_approval_graph(approval: Approval) -> Graph:
        """Build an RDF graph for an approval."""
        g = Graph()
        _bind_prefixes(g)

        app_uri = _uri(approval.id)
        g.add((app_uri, RDF.type, OS.Approval))
        g.add((app_uri, OS.approvalStatus, _literal(approval.status.value)))
        g.add((app_uri, OS.approvedPayloadHash, _literal(approval.proposal_payload_hash)))
        g.add((app_uri, OS.timestamp, _literal(approval.requested_at)))

        # Link to proposal
        prop_uri = _uri(approval.proposal_id)
        g.add((app_uri, OS.forProposal, prop_uri))

        # If granted, link to approver
        if approval.decided_by_actor_id:
            actor_uri = _uri(approval.decided_by_actor_id)
            g.add((app_uri, OS.grantedBy, actor_uri))

        return g

    @staticmethod
    def build_execution_graph(execution: Execution) -> Graph:
        """Build an RDF graph for an execution."""
        g = Graph()
        _bind_prefixes(g)

        exec_uri = _uri(execution.id)
        g.add((exec_uri, RDF.type, OS.Execution))
        g.add((exec_uri, OS.executionStatus, _literal(execution.status.value)))
        g.add((exec_uri, OS.timestamp, _literal(execution.executed_at)))

        # Link to proposal
        prop_uri = _uri(execution.proposal_id)
        g.add((exec_uri, OS.forProposalExecution, prop_uri))

        # Link to policy decision
        if execution.policy_decision_id:
            dec_uri = _uri(execution.policy_decision_id)
            g.add((exec_uri, OS.referencesPolicyDecision, dec_uri))

        # Link to approval
        if execution.approval_id:
            app_uri = _uri(execution.approval_id)
            g.add((exec_uri, OS.referencesApproval, app_uri))

        if execution.error_message:
            g.add((exec_uri, RDFS.comment, _literal(execution.error_message)))

        return g

    @staticmethod
    def build_outcome_graph(outcome: Outcome) -> Graph:
        """Build an RDF graph for an execution outcome."""
        g = Graph()
        _bind_prefixes(g)

        out_uri = _uri(outcome.id)
        g.add((out_uri, RDF.type, OS.Outcome))
        g.add((out_uri, OS.outcomeOf, _uri(outcome.execution_id)))
        g.add((out_uri, OS.outcomeStatus, _literal("succeeded" if outcome.external_reference else "failed")))
        g.add((out_uri, OS.externalReference, _literal(outcome.external_reference)))
        g.add((out_uri, OS.timestamp, _literal(outcome.recorded_at)))

        return g

    @staticmethod
    def build_audit_record_graph(record: AuditRecord) -> Graph:
        """Build an RDF graph for an audit record."""
        g = Graph()
        _bind_prefixes(g)

        rec_uri = _uri(record.id)
        g.add((rec_uri, RDF.type, OS.AuditRecord))
        g.add((rec_uri, OS.eventType, _literal(record.event_type)))
        g.add((rec_uri, OS.timestamp, _literal(record.timestamp)))

        # Link to proposal via related_ids
        for key, ids in record.related_ids.items():
            for ref_id in ids:
                ref_uri = _uri(ref_id)
                if key == "proposal_ids":
                    g.add((rec_uri, OS.referencesProposal, ref_uri))
                elif key == "execution_ids":
                    g.add((rec_uri, OS.referencesExecution, ref_uri))
                    g.add((rec_uri, OS.records, ref_uri))
                elif key == "outcome_ids":
                    g.add((rec_uri, OS.referencesOutcome, ref_uri))

        return g

    @staticmethod
    def build_full_graph(
        actor: Actor | None = None,
        evidence: list[Evidence] | None = None,
        proposal: ActionProposal | None = None,
        decision: PolicyDecision | None = None,
        approval: Approval | None = None,
        execution: Execution | None = None,
        outcome: Outcome | None = None,
        audit_record: AuditRecord | None = None,
    ) -> Graph:
        """Build a complete domain graph from all provided entities."""
        g = Graph()
        _bind_prefixes(g)

        if actor:
            g += GraphBuilder.build_actor_graph(actor)
        if evidence:
            for ev in evidence:
                g += GraphBuilder.build_evidence_graph(ev)
        if proposal:
            g += GraphBuilder.build_proposal_graph(proposal)
        if decision:
            g += GraphBuilder.build_policy_decision_graph(decision)
        if approval:
            g += GraphBuilder.build_approval_graph(approval)
        if execution:
            g += GraphBuilder.build_execution_graph(execution)
        if outcome:
            g += GraphBuilder.build_outcome_graph(outcome)
        if audit_record:
            g += GraphBuilder.build_audit_record_graph(audit_record)

        return g
