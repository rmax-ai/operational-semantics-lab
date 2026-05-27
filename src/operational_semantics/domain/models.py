"""Pydantic domain models for the operational semantics layer."""

from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, Field

from operational_semantics.domain.enums import (
    ApprovalStatus,
    DecisionType,
    EvidenceType,
    ExecutionStatus,
    OperationClass,
    RiskLevel,
    SystemType,
)
from operational_semantics.domain.hashing import compute_payload_hash


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Core value objects
# ---------------------------------------------------------------------------


class Actor(BaseModel):
    """An actor that can perform operations or approve actions."""

    id: str
    name: str
    role_ids: list[str] = Field(default_factory=list)


class Role(BaseModel):
    """A role defining what operations an actor is authorized to perform."""

    id: str
    name: str
    description: str = ""


class Evidence(BaseModel):
    """A piece of evidence supporting a proposal."""

    id: str
    evidence_type: EvidenceType
    content: str
    source: str
    recorded_at: datetime = Field(default_factory=_utcnow)


class Tool(BaseModel):
    """A tool that can be invoked through the governed gateway."""

    id: str
    name: str
    system_type: SystemType
    operation_class: OperationClass
    description: str = ""


class SaaSResource(BaseModel):
    """A resource in an external SaaS system (synthetic)."""

    id: str
    system_type: SystemType
    resource_type: str
    external_id: str
    state: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------


class PolicyRule(BaseModel):
    """A single policy rule within a YAML-defined policy."""

    operation: str
    action_type: str | None = None
    target_scope: str | None = None
    when: dict[str, Any] = Field(default_factory=dict)
    decision: DecisionType
    approver_role: str | None = None
    remediation: list[str] = Field(default_factory=list)


class Policy(BaseModel):
    """A named policy definition loaded from YAML."""

    id: str
    system: str
    version: str = "1.0"
    rules: list[PolicyRule] = Field(default_factory=list)


class PolicyDecision(BaseModel):
    """The result of evaluating a policy against a proposal."""

    id: str
    proposal_id: str
    policy_id: str
    policy_version: str
    decision: DecisionType
    reason_codes: list[str] = Field(default_factory=list)
    explanation: str = ""
    required_approver_role: str | None = None
    remediation: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Proposals, Approvals, Executions
# ---------------------------------------------------------------------------


class ActionProposal(BaseModel):
    """A proposal representing something an agent wants to do."""

    id: str
    action_type: str
    operation_class: OperationClass
    system_type: SystemType
    target_resource_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    payload_hash: str = ""
    evidence_ids: list[str] = Field(default_factory=list)
    actor_id: str
    risk_level: RiskLevel = RiskLevel.LOW
    proposed_at: datetime = Field(default_factory=_utcnow)
    contains_restricted_data: bool = False

    def model_post_init(self, __context: Any) -> None:
        """Compute payload hash on creation if not set."""
        if not self.payload_hash and self.payload:
            self.payload_hash = compute_payload_hash(self.payload)
        super().model_post_init(__context)


class Approval(BaseModel):
    """An approval (or rejection) of a proposal."""

    id: str
    proposal_id: str
    requested_approver_role: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    proposal_payload_hash: str
    requested_at: datetime = Field(default_factory=_utcnow)
    decided_at: datetime | None = None
    decided_by_actor_id: str | None = None
    expires_at: datetime | None = None

    @property
    def is_valid(self) -> bool:
        """Check if this approval is currently valid for execution."""
        if self.status != ApprovalStatus.GRANTED:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True


class Execution(BaseModel):
    """An attempt to execute an approved proposal."""

    id: str
    proposal_id: str
    approval_id: str | None = None
    policy_decision_id: str
    status: ExecutionStatus
    payload_hash_at_execution: str = ""
    executed_at: datetime = Field(default_factory=_utcnow)
    error_message: str | None = None


class Outcome(BaseModel):
    """The result of a successful execution."""

    id: str
    execution_id: str
    system_type: SystemType
    external_reference: str
    description: str = ""
    before_state: dict[str, Any] = Field(default_factory=dict)
    after_state: dict[str, Any] = Field(default_factory=dict)
    recorded_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


class AuditRecord(BaseModel):
    """A single atomically recorded business event in the provenance ledger."""

    id: str
    event_type: str
    timestamp: datetime = Field(default_factory=_utcnow)
    actor_id: str
    aggregate_id: str
    related_ids: dict[str, list[str]] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
    previous_event_hash: str = ""
    event_hash: str = ""


class AuditExplanation(BaseModel):
    """A structured explanation of why something happened."""

    proposal: ActionProposal | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    validation_result: dict[str, Any] = Field(default_factory=dict)
    policy_decision: PolicyDecision | None = None
    approval: Approval | None = None
    execution: Execution | None = None
    outcome: Outcome | None = None
    integrity_check: dict[str, Any] = Field(default_factory=dict)
    human_readable_summary: str = ""
