"""SQLAlchemy table models for persistence."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from operational_semantics.persistence.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProposalTable(Base):
    """Persistent storage for action proposals."""

    __tablename__ = "proposals"

    id = Column(String, primary_key=True)
    action_type = Column(String, nullable=False)
    operation_class = Column(String, nullable=False)
    system_type = Column(String, nullable=False)
    target_resource_id = Column(String, nullable=False)
    payload = Column(JSON, default=dict)
    payload_hash = Column(String, nullable=False)
    evidence_ids = Column(JSON, default=list)
    actor_id = Column(String, nullable=False)
    risk_level = Column(String, default="low")
    contains_restricted_data = Column(Integer, default=0)
    proposed_at = Column(DateTime, default=_utcnow)

    policy_decisions = relationship("PolicyDecisionTable", back_populates="proposal", lazy="selectin")


class EvidenceTable(Base):
    """Persistent storage for evidence items."""

    __tablename__ = "evidence"

    id = Column(String, primary_key=True)
    evidence_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String, nullable=False)
    recorded_at = Column(DateTime, default=_utcnow)


class PolicyDecisionTable(Base):
    """Persistent storage for policy decisions."""

    __tablename__ = "policy_decisions"

    id = Column(String, primary_key=True)
    proposal_id = Column(String, ForeignKey("proposals.id"), nullable=False)
    policy_id = Column(String, nullable=False)
    policy_version = Column(String, nullable=False)
    decision = Column(String, nullable=False)
    reason_codes = Column(JSON, default=list)
    explanation = Column(Text, default="")
    required_approver_role = Column(String, nullable=True)
    remediation = Column(JSON, default=list)
    evaluated_at = Column(DateTime, default=_utcnow)

    proposal = relationship("ProposalTable", back_populates="policy_decisions", lazy="selectin")


class ApprovalTable(Base):
    """Persistent storage for approval records."""

    __tablename__ = "approvals"

    id = Column(String, primary_key=True)
    proposal_id = Column(String, ForeignKey("proposals.id"), nullable=False)
    requested_approver_role = Column(String, nullable=False)
    status = Column(String, default="pending")
    proposal_payload_hash = Column(String, nullable=False)
    requested_at = Column(DateTime, default=_utcnow)
    decided_at = Column(DateTime, nullable=True)
    decided_by_actor_id = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)


class ExecutionTable(Base):
    """Persistent storage for execution attempts."""

    __tablename__ = "executions"

    id = Column(String, primary_key=True)
    proposal_id = Column(String, ForeignKey("proposals.id"), nullable=False)
    approval_id = Column(String, ForeignKey("approvals.id"), nullable=True)
    policy_decision_id = Column(String, ForeignKey("policy_decisions.id"), nullable=False)
    status = Column(String, nullable=False)
    payload_hash_at_execution = Column(String, default="")
    executed_at = Column(DateTime, default=_utcnow)
    error_message = Column(Text, nullable=True)


class OutcomeTable(Base):
    """Persistent storage for execution outcomes."""

    __tablename__ = "outcomes"

    id = Column(String, primary_key=True)
    execution_id = Column(String, ForeignKey("executions.id"), nullable=False)
    system_type = Column(String, nullable=False)
    external_reference = Column(String, default="")
    description = Column(Text, default="")
    before_state = Column(JSON, default=dict)
    after_state = Column(JSON, default=dict)
    recorded_at = Column(DateTime, default=_utcnow)


class AuditRecordTable(Base):
    """Append-only ledger of business events."""

    __tablename__ = "audit_records"

    id = Column(String, primary_key=True)
    event_type = Column(String, nullable=False)
    timestamp = Column(DateTime, default=_utcnow)
    actor_id = Column(String, nullable=False)
    aggregate_id = Column(String, nullable=False)
    related_ids = Column(JSON, default=dict)
    payload = Column(JSON, default=dict)
    previous_event_hash = Column(String, default="")
    event_hash = Column(String, nullable=False)


class SaasResourceTable(Base):
    """Persistent storage for synthetic SaaS resources."""

    __tablename__ = "saas_resources"

    id = Column(String, primary_key=True)
    system_type = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    external_id = Column(String, nullable=False)
    state = Column(JSON, default=dict)
