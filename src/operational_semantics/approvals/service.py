"""Approval lifecycle service.

Manages the approval state machine:
PENDING → GRANTED | REJECTED | EXPIRED | INVALIDATED
"""

from datetime import datetime, timedelta, timezone

from operational_semantics.domain.enums import ApprovalStatus
from operational_semantics.domain.errors import ApprovalError
from operational_semantics.domain.models import ActionProposal, Approval, PolicyDecision


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ApprovalService:
    """Manages the approval lifecycle."""

    def __init__(self, approval_ttl_minutes: int = 60) -> None:
        self.approval_ttl_minutes = approval_ttl_minutes

    def create_request(
        self,
        proposal: ActionProposal,
        policy_decision: PolicyDecision,
    ) -> Approval:
        """Create an approval request for a proposal.

        The approval is bound to the exact payload hash of the proposal.
        """
        if not policy_decision.required_approver_role:
            msg = "Policy decision does not require approval"
            raise ApprovalError(msg, reason="NO_APPROVER_ROLE")

        expires_at = _utcnow() + timedelta(minutes=self.approval_ttl_minutes)

        return Approval(
            id=f"apr-{proposal.id}-{_utcnow().timestamp():.0f}",
            proposal_id=proposal.id,
            requested_approver_role=policy_decision.required_approver_role,
            status=ApprovalStatus.PENDING,
            proposal_payload_hash=proposal.payload_hash,
            requested_at=_utcnow(),
            expires_at=expires_at,
        )

    def grant(
        self,
        approval: Approval,
        approver_id: str,
        approver_role: str,
        proposal: ActionProposal | None = None,
    ) -> Approval:
        """Grant an approval.

        Validates:
        - Approval is in PENDING status
        - Approver has the required role
        - Payload hash matches (if proposal provided)
        """
        if approval.status != ApprovalStatus.PENDING:
            raise ApprovalError(
                f"Cannot grant approval in status {approval.status}",
                reason=f"Expected PENDING, got {approval.status}",
            )

        if approver_role != approval.requested_approver_role:
            raise ApprovalError(
                f"Approver role '{approver_role}' does not match required role "
                f"'{approval.requested_approver_role}'",
                reason="UNAUTHORIZED_APPROVER",
            )

        if proposal and approval.proposal_payload_hash != proposal.payload_hash:
            raise ApprovalError(
                "Payload hash mismatch — proposal payload changed since approval was requested",
                reason="PAYLOAD_CHANGED_AFTER_APPROVAL",
            )

        approval.status = ApprovalStatus.GRANTED
        approval.decided_at = _utcnow()
        approval.decided_by_actor_id = approver_id
        return approval

    def reject(
        self,
        approval: Approval,
        decided_by: str,
    ) -> Approval:
        """Reject an approval."""
        if approval.status != ApprovalStatus.PENDING:
            raise ApprovalError(
                f"Cannot reject approval in status {approval.status}",
                reason=f"Expected PENDING, got {approval.status}",
            )
        approval.status = ApprovalStatus.REJECTED
        approval.decided_at = _utcnow()
        approval.decided_by_actor_id = decided_by
        return approval

    def invalidate(self, approval: Approval) -> Approval:
        """Invalidate an approval (e.g., payload changed)."""
        if approval.status != ApprovalStatus.GRANTED:
            raise ApprovalError(
                f"Cannot invalidate approval in status {approval.status}",
                reason=f"Expected GRANTED, got {approval.status}",
            )
        approval.status = ApprovalStatus.INVALIDATED
        return approval

    def check_expired(self, approval: Approval) -> bool:
        """Check if an approval has expired and update its status if so."""
        if approval.status != ApprovalStatus.GRANTED:
            return False
        if approval.expires_at and _utcnow() > approval.expires_at:
            approval.status = ApprovalStatus.EXPIRED
            return True
        return False
