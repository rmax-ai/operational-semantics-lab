"""Payload integrity verification for approval-bound writes."""

from operational_semantics.domain.hashing import compute_payload_hash
from operational_semantics.domain.models import ActionProposal, Approval


class ApprovalIntegrity:
    """Verifies that approval payload hashes match execution-time payloads."""

    @staticmethod
    def verify_payload_hash(approval: Approval, proposal: ActionProposal) -> bool:
        """Verify that the proposal's current payload hash matches the approved hash.

        Returns True if the hashes match, False otherwise.
        """
        current_hash = compute_payload_hash(proposal.payload)
        return current_hash == approval.proposal_payload_hash

    @staticmethod
    def verify_proposal_hash(proposal: ActionProposal) -> bool:
        """Verify that the proposal's payload hash is correctly computed."""
        expected = compute_payload_hash(proposal.payload)
        return expected == proposal.payload_hash
