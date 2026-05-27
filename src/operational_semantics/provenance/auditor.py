"""Auditor service — reconstructs complete provenance explanations."""

from typing import Any

from operational_semantics.domain.models import (
    ActionProposal,
    Approval,
    AuditExplanation,
    Evidence,
    Execution,
    Outcome,
    PolicyDecision,
)
from operational_semantics.persistence.repositories import (
    ApprovalRepository,
    AuditRepository,
    EvidenceRepository,
    ExecutionRepository,
    OutcomeRepository,
    PolicyDecisionRepository,
    ProposalRepository,
)
from operational_semantics.provenance.ledger import ProvenanceLedger


class AuditExplanationBuilder:
    """Builds structured AuditExplanation objects."""

    @staticmethod
    def build(
        proposal: ActionProposal | None = None,
        evidence: list[Evidence] | None = None,
        validation_result: dict[str, Any] | None = None,
        policy_decision: PolicyDecision | None = None,
        approval: Approval | None = None,
        execution: Execution | None = None,
        outcome: Outcome | None = None,
    ) -> AuditExplanation:
        """Build a complete audit explanation from domain objects."""
        # Integrity check
        integrity_check: dict[str, Any] = {
            "proposal_exists": proposal is not None,
            "evidence_found": bool(evidence),
            "policy_decision_exists": policy_decision is not None,
            "approval_exists": approval is not None,
            "execution_exists": execution is not None,
            "outcome_exists": outcome is not None,
        }

        # Verify payload hash integrity
        if proposal and approval:
            integrity_check["payload_hash_matches"] = (
                proposal.payload_hash == approval.proposal_payload_hash
            )

        # Build human-readable summary (deterministic, no LLM)
        summary_parts: list[str] = []

        if proposal:
            summary_parts.append(
                f"Proposal {proposal.id}: {proposal.action_type} on {proposal.system_type.value}"
            )

        if evidence:
            summary_parts.append(
                f"Supported by {len(evidence)} evidence item(s)"
            )

        if policy_decision:
            summary_parts.append(
                f"Policy decision: {policy_decision.decision.value}"
            )
            if policy_decision.reason_codes:
                summary_parts.append(
                    f"Reasons: {', '.join(policy_decision.reason_codes)}"
                )

        if approval:
            summary_parts.append(
                f"Approval: {approval.status.value}"
            )
            if approval.decided_by_actor_id:
                summary_parts.append(
                    f"Approved/decided by: {approval.decided_by_actor_id}"
                )

        if execution:
            summary_parts.append(
                f"Execution: {execution.status.value}"
            )

        if outcome:
            summary_parts.append(
                f"Outcome: {outcome.external_reference} ({outcome.description})"
            )

        return AuditExplanation(
            proposal=proposal,
            evidence=evidence or [],
            validation_result=validation_result or {},
            policy_decision=policy_decision,
            approval=approval,
            execution=execution,
            outcome=outcome,
            integrity_check=integrity_check,
            human_readable_summary=" → ".join(summary_parts) if summary_parts else "No audit data available",
        )


class Auditor:
    """Service that queries repositories and the ledger to produce audit trails."""

    def __init__(
        self,
        proposal_repo: ProposalRepository,
        evidence_repo: EvidenceRepository,
        policy_decision_repo: PolicyDecisionRepository,
        approval_repo: ApprovalRepository,
        execution_repo: ExecutionRepository,
        outcome_repo: OutcomeRepository,
        audit_repo: AuditRepository,
        ledger: ProvenanceLedger | None = None,
    ) -> None:
        self._proposal_repo = proposal_repo
        self._evidence_repo = evidence_repo
        self._policy_decision_repo = policy_decision_repo
        self._approval_repo = approval_repo
        self._execution_repo = execution_repo
        self._outcome_repo = outcome_repo
        self._audit_repo = audit_repo
        self._ledger = ledger

    async def explain_execution(self, execution_id: str) -> AuditExplanation:
        """Reconstruct the full provenance chain for an execution."""
        exec_table = await self._execution_repo.get(execution_id)
        if not exec_table:
            return AuditExplanation(
                integrity_check={"execution_found": False},
                human_readable_summary=f"Execution {execution_id} not found",
            )

        execution = Execution(
            id=exec_table.id,
            proposal_id=exec_table.proposal_id,
            approval_id=exec_table.approval_id,
            policy_decision_id=exec_table.policy_decision_id,
            status=exec_table.status,
            payload_hash_at_execution=exec_table.payload_hash_at_execution,
            executed_at=exec_table.executed_at,
            error_message=exec_table.error_message,
        )

        # Get proposal
        proposal = None
        prop_table = await self._proposal_repo.get(execution.proposal_id)
        if prop_table:
            from operational_semantics.domain.enums import OperationClass, RiskLevel, SystemType
            proposal = ActionProposal(
                id=prop_table.id,
                action_type=prop_table.action_type,
                operation_class=OperationClass(prop_table.operation_class),
                system_type=SystemType(prop_table.system_type),
                target_resource_id=prop_table.target_resource_id,
                payload=prop_table.payload or {},
                payload_hash=prop_table.payload_hash,
                evidence_ids=list(prop_table.evidence_ids or []),
                actor_id=prop_table.actor_id,
                risk_level=RiskLevel(prop_table.risk_level) if prop_table.risk_level else RiskLevel.LOW,
                contains_restricted_data=bool(prop_table.contains_restricted_data),
                proposed_at=prop_table.proposed_at,
            )

        # Get policy decision
        policy_decision = None
        if execution.policy_decision_id:
            pd_table = await self._policy_decision_repo.get(execution.policy_decision_id)
            if pd_table:
                from operational_semantics.domain.enums import DecisionType
                policy_decision = PolicyDecision(
                    id=pd_table.id,
                    proposal_id=pd_table.proposal_id,
                    policy_id=pd_table.policy_id,
                    policy_version=pd_table.policy_version,
                    decision=DecisionType(pd_table.decision),
                    reason_codes=list(pd_table.reason_codes or []),
                    explanation=pd_table.explanation or "",
                    required_approver_role=pd_table.required_approver_role,
                    remediation=list(pd_table.remediation or []),
                    evaluated_at=pd_table.evaluated_at,
                )

        # Get approval
        approval = None
        if execution.approval_id:
            app_table = await self._approval_repo.get(execution.approval_id)
            if app_table:
                from operational_semantics.domain.enums import ApprovalStatus
                approval = Approval(
                    id=app_table.id,
                    proposal_id=app_table.proposal_id,
                    requested_approver_role=app_table.requested_approver_role,
                    status=ApprovalStatus(app_table.status),
                    proposal_payload_hash=app_table.proposal_payload_hash,
                    requested_at=app_table.requested_at,
                    decided_at=app_table.decided_at,
                    decided_by_actor_id=app_table.decided_by_actor_id,
                    expires_at=app_table.expires_at,
                )

        # Get evidence
        evidence = []
        if proposal:
            ev_tables = await self._evidence_repo.get_by_ids(proposal.evidence_ids)
            for ev_table in ev_tables:
                from operational_semantics.domain.enums import EvidenceType
                evidence.append(Evidence(
                    id=ev_table.id,
                    evidence_type=EvidenceType(ev_table.evidence_type),
                    content=ev_table.content,
                    source=ev_table.source,
                    recorded_at=ev_table.recorded_at,
                ))

        # Get outcome
        outcome = None
        out_table = await self._outcome_repo.get_by_execution(execution_id)
        if out_table:
            from operational_semantics.domain.enums import SystemType
            outcome = Outcome(
                id=out_table.id,
                execution_id=out_table.execution_id,
                system_type=SystemType(out_table.system_type) if out_table.system_type else "unknown",
                external_reference=out_table.external_reference or "",
                description=out_table.description or "",
                before_state=out_table.before_state or {},
                after_state=out_table.after_state or {},
                recorded_at=out_table.recorded_at,
            )

        return AuditExplanationBuilder.build(
            proposal=proposal,
            evidence=evidence,
            policy_decision=policy_decision,
            approval=approval,
            execution=execution,
            outcome=outcome,
        )

    async def explain_proposal(self, proposal_id: str) -> AuditExplanation:
        """Reconstruct audit data for a proposal, even if not executed."""
        prop_table = await self._proposal_repo.get(proposal_id)
        if not prop_table:
            return AuditExplanation(
                integrity_check={"proposal_found": False},
                human_readable_summary=f"Proposal {proposal_id} not found",
            )

        from operational_semantics.domain.enums import OperationClass, RiskLevel, SystemType
        proposal = ActionProposal(
            id=prop_table.id,
            action_type=prop_table.action_type,
            operation_class=OperationClass(prop_table.operation_class),
            system_type=SystemType(prop_table.system_type),
            target_resource_id=prop_table.target_resource_id,
            payload=prop_table.payload or {},
            payload_hash=prop_table.payload_hash,
            evidence_ids=list(prop_table.evidence_ids or []),
            actor_id=prop_table.actor_id,
            risk_level=RiskLevel(prop_table.risk_level) if prop_table.risk_level else RiskLevel.LOW,
            contains_restricted_data=bool(prop_table.contains_restricted_data),
            proposed_at=prop_table.proposed_at,
        )

        # Get policy decision
        policy_decision = None
        pd_table = await self._policy_decision_repo.get_by_proposal(proposal_id)
        if pd_table:
            from operational_semantics.domain.enums import DecisionType
            policy_decision = PolicyDecision(
                id=pd_table.id,
                proposal_id=pd_table.proposal_id,
                policy_id=pd_table.policy_id,
                policy_version=pd_table.policy_version,
                decision=DecisionType(pd_table.decision),
                reason_codes=list(pd_table.reason_codes or []),
                explanation=pd_table.explanation or "",
                required_approver_role=pd_table.required_approver_role,
                remediation=list(pd_table.remediation or []),
                evaluated_at=pd_table.evaluated_at,
            )

        # Get evidence
        evidence = []
        ev_tables = await self._evidence_repo.get_by_ids(proposal.evidence_ids)
        for ev_table in ev_tables:
            from operational_semantics.domain.enums import EvidenceType
            evidence.append(Evidence(
                id=ev_table.id,
                evidence_type=EvidenceType(ev_table.evidence_type),
                content=ev_table.content,
                source=ev_table.source,
                recorded_at=ev_table.recorded_at,
            ))

        # Get approvals
        approval = None
        app_tables = await self._approval_repo.get_by_proposal(proposal_id)
        if app_tables:
            from operational_semantics.domain.enums import ApprovalStatus
            app_table = app_tables[0]
            approval = Approval(
                id=app_table.id,
                proposal_id=app_table.proposal_id,
                requested_approver_role=app_table.requested_approver_role,
                status=ApprovalStatus(app_table.status),
                proposal_payload_hash=app_table.proposal_payload_hash,
                requested_at=app_table.requested_at,
                decided_at=app_table.decided_at,
                decided_by_actor_id=app_table.decided_by_actor_id,
                expires_at=app_table.expires_at,
            )

        # Get executions
        execution = None
        outcome = None
        exec_tables = await self._execution_repo.get_by_proposal(proposal_id)
        if exec_tables:
            exec_table = exec_tables[0]
            from operational_semantics.domain.enums import ExecutionStatus
            execution = Execution(
                id=exec_table.id,
                proposal_id=exec_table.proposal_id,
                approval_id=exec_table.approval_id,
                policy_decision_id=exec_table.policy_decision_id,
                status=ExecutionStatus(exec_table.status),
                payload_hash_at_execution=exec_table.payload_hash_at_execution,
                executed_at=exec_table.executed_at,
                error_message=exec_table.error_message,
            )
            out_table = await self._outcome_repo.get_by_execution(exec_table.id)
            if out_table:
                from operational_semantics.domain.enums import SystemType
                outcome = Outcome(
                    id=out_table.id,
                    execution_id=out_table.execution_id,
                    system_type=SystemType(out_table.system_type) if out_table.system_type else "unknown",
                    external_reference=out_table.external_reference or "",
                    description=out_table.description or "",
                    before_state=out_table.before_state or {},
                    after_state=out_table.after_state or {},
                    recorded_at=out_table.recorded_at,
                )

        return AuditExplanationBuilder.build(
            proposal=proposal,
            evidence=evidence,
            policy_decision=policy_decision,
            approval=approval,
            execution=execution,
            outcome=outcome,
        )
