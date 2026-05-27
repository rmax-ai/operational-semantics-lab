"""Lifecycle state machine for proposals, approvals, and executions.

Encodes the rules:
- Proposal → Policy Decision → (Approval?) → Execution → Outcome
- A prohibited proposal cannot be approved
- An approval-required proposal cannot execute without granted approval
- Approval is valid only for the payload hash approved
- Changed payload invalidates prior approval
"""

from datetime import datetime, timezone

from operational_semantics.domain.enums import ApprovalStatus, DecisionType, ExecutionStatus
from operational_semantics.domain.errors import ApprovalError, ExecutionError, ValidationError
from operational_semantics.domain.models import ActionProposal, Approval, Execution, Outcome


def validate_proposal_for_policy(proposal: ActionProposal) -> None:
    """Validate that a proposal is structurally complete before policy evaluation."""
    errors: list[str] = []
    if not proposal.action_type:
        errors.append("Proposal must have an action type")
    if not proposal.target_resource_id:
        errors.append("Proposal must target a resource")
    if not proposal.evidence_ids:
        errors.append("Write proposal must have at least one evidence reference")
    if not proposal.payload_hash:
        errors.append("Proposal must have a computed payload hash")
    if errors:
        raise ValidationError("Proposal validation failed", details=errors)


def apply_policy_decision(proposal: ActionProposal, decision: DecisionType) -> None:
    """Ensure the policy decision is compatible with the proposal state."""
    if decision == DecisionType.PROHIBITED:
        raise ValidationError(
            "Cannot proceed with a prohibited proposal",
            details=[f"Proposal {proposal.id} was prohibited by policy"],
        )


def validate_approval_grant(approval: Approval, proposal: ActionProposal) -> None:
    """Validate that an approval can be granted for a proposal."""
    if approval.status not in (ApprovalStatus.PENDING,):
        raise ApprovalError(
            f"Cannot grant approval in status {approval.status}",
            reason=f"Expected PENDING, got {approval.status}",
        )
    if approval.proposal_payload_hash != proposal.payload_hash:
        raise ApprovalError(
            "Approval payload hash does not match proposal",
            reason="Payload changed since approval request was created",
        )


def validate_execution(
    proposal: ActionProposal,
    approval: Approval | None,
    decision_type: DecisionType,
) -> None:
    """Validate that execution can proceed."""
    if decision_type == DecisionType.PROHIBITED:
        raise ExecutionError("Execution blocked by policy", reason="PROHIBITED")

    if decision_type == DecisionType.APPROVAL_REQUIRED:
        if approval is None:
            raise ExecutionError("Approval required but none provided", reason="NO_APPROVAL")
        if approval.status != ApprovalStatus.GRANTED:
            raise ExecutionError(
                f"Approval status is {approval.status}, not GRANTED",
                reason=f"APPROVAL_{approval.status.upper()}",
            )
        if approval.proposal_payload_hash != proposal.payload_hash:
            raise ExecutionError(
                "Payload changed since approval was granted",
                reason="PAYLOAD_CHANGED_AFTER_APPROVAL",
            )
        now = datetime.now(timezone.utc)
        if approval.expires_at and now > approval.expires_at:
            raise ExecutionError("Approval has expired", reason="APPROVAL_EXPIRED")

    if decision_type == DecisionType.PERMITTED:
        # No approval needed, proceed
        pass


def create_outcome(execution: Execution, before: dict | None = None) -> Outcome:
    """Create an outcome record for a successful execution."""
    return Outcome(
        id=f"outcome-{execution.id}",
        execution_id=execution.id,
        system_type=execution.proposal_id.split("-")[0] if "-" in execution.proposal_id else "unknown",
        external_reference="",
        before_state=before or {},
    )
