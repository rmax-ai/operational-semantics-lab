"""Maps domain models to provenance event types."""

from typing import Any

from operational_semantics.domain.models import (
    ActionProposal,
    Approval,
    AuditRecord,
    Evidence,
    Execution,
    Outcome,
    PolicyDecision,
)
from operational_semantics.provenance.ledger import EventType, LedgerEvent


class ProvenanceMapper:
    """Maps domain operations to structured provenance events."""

    @staticmethod
    def evidence_registered(
        evidence: Evidence,
        actor_id: str,
    ) -> LedgerEvent:
        """Create an event for evidence registration."""
        return LedgerEvent(
            event_type=EventType.EVIDENCE_REGISTERED,
            actor_id=actor_id,
            aggregate_id=evidence.id,
            payload={
                "evidence_id": evidence.id,
                "evidence_type": evidence.evidence_type.value,
                "source": evidence.source,
            },
        )

    @staticmethod
    def proposal_created(
        proposal: ActionProposal,
    ) -> LedgerEvent:
        """Create an event for proposal creation."""
        return LedgerEvent(
            event_type=EventType.PROPOSAL_CREATED,
            actor_id=proposal.actor_id,
            aggregate_id=proposal.id,
            payload={
                "action_type": proposal.action_type,
                "operation_class": proposal.operation_class.value,
                "system_type": proposal.system_type.value,
                "payload_hash": proposal.payload_hash,
                "risk_level": proposal.risk_level.value,
                "contains_restricted_data": proposal.contains_restricted_data,
            },
            related_ids={"evidence_ids": list(proposal.evidence_ids)},
        )

    @staticmethod
    def policy_evaluated(
        proposal: ActionProposal,
        decision: PolicyDecision,
    ) -> LedgerEvent:
        """Create an event for policy evaluation."""
        return LedgerEvent(
            event_type=EventType.POLICY_EVALUATED,
            actor_id=proposal.actor_id,
            aggregate_id=proposal.id,
            payload={
                "decision": decision.decision.value,
                "policy_id": decision.policy_id,
                "reason_codes": decision.reason_codes,
                "required_approver_role": decision.required_approver_role,
                "remediation": decision.remediation,
            },
            related_ids={"policy_decision_ids": [decision.id]},
        )

    @staticmethod
    def approval_requested(
        proposal: ActionProposal,
        approval: Approval,
    ) -> LedgerEvent:
        """Create an event for approval request."""
        return LedgerEvent(
            event_type=EventType.APPROVAL_REQUESTED,
            actor_id=proposal.actor_id,
            aggregate_id=proposal.id,
            payload={
                "approval_id": approval.id,
                "required_role": approval.requested_approver_role,
                "payload_hash": approval.proposal_payload_hash,
                "expires_at": approval.expires_at.isoformat() if approval.expires_at else None,
            },
            related_ids={"approval_ids": [approval.id]},
        )

    @staticmethod
    def approval_granted(
        approval: Approval,
        approver_id: str,
        proposal_id: str,
    ) -> LedgerEvent:
        """Create an event for approval granted."""
        return LedgerEvent(
            event_type=EventType.APPROVAL_GRANTED,
            actor_id=approver_id,
            aggregate_id=proposal_id,
            payload={
                "approval_id": approval.id,
                "payoad_hash": approval.proposal_payload_hash,
                "role": approval.requested_approver_role,
            },
            related_ids={"approval_ids": [approval.id]},
        )

    @staticmethod
    def approval_rejected(
        approval: Approval,
        approver_id: str,
        proposal_id: str,
    ) -> LedgerEvent:
        """Create an event for approval rejected."""
        return LedgerEvent(
            event_type=EventType.APPROVAL_REJECTED,
            actor_id=approver_id,
            aggregate_id=proposal_id,
            payload={"approval_id": approval.id},
            related_ids={"approval_ids": [approval.id]},
        )

    @staticmethod
    def execution_blocked(
        execution: Execution,
        reason: str,
    ) -> LedgerEvent:
        """Create an event for a blocked execution."""
        return LedgerEvent(
            event_type=EventType.EXECUTION_BLOCKED,
            actor_id=execution.proposal_id,
            aggregate_id=execution.proposal_id,
            payload={
                "execution_id": execution.id,
                "reason": reason,
            },
            related_ids={"execution_ids": [execution.id]},
        )

    @staticmethod
    def execution_succeeded(
        execution: Execution,
        outcome: Outcome,
    ) -> LedgerEvent:
        """Create an event for a successful execution."""
        return LedgerEvent(
            event_type=EventType.EXECUTION_SUCCEEDED,
            actor_id=execution.proposal_id,
            aggregate_id=execution.proposal_id,
            payload={
                "execution_id": execution.id,
                "external_reference": outcome.external_reference,
            },
            related_ids={
                "execution_ids": [execution.id],
                "outcome_ids": [outcome.id],
            },
        )

    @staticmethod
    def execution_failed(
        execution: Execution,
        error_message: str,
    ) -> LedgerEvent:
        """Create an event for a failed execution."""
        return LedgerEvent(
            event_type=EventType.EXECUTION_FAILED,
            actor_id=execution.proposal_id,
            aggregate_id=execution.proposal_id,
            payload={
                "execution_id": execution.id,
                "error": error_message,
            },
            related_ids={"execution_ids": [execution.id]},
        )

    @staticmethod
    def outcome_recorded(
        outcome: Outcome,
        execution_id: str,
        actor_id: str,
    ) -> LedgerEvent:
        """Create an event for an outcome being recorded."""
        return LedgerEvent(
            event_type=EventType.OUTCOME_RECORDED,
            actor_id=actor_id,
            aggregate_id=outcome.execution_id,
            payload={
                "outcome_id": outcome.id,
                "system_type": outcome.system_type.value if hasattr(outcome.system_type, 'value') else outcome.system_type,
                "external_reference": outcome.external_reference,
                "before_state": outcome.before_state,
                "after_state": outcome.after_state,
            },
            related_ids={"outcome_ids": [outcome.id]},
        )
