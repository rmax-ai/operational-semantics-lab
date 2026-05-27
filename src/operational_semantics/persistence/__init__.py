"""Persistence layer for the operational semantics lab."""

from operational_semantics.persistence.database import (
    DatabaseEngine,
    get_engine,
    get_session,
)
from operational_semantics.persistence.tables import (
    ApprovalTable,
    AuditRecordTable,
    EvidenceTable,
    ExecutionTable,
    OutcomeTable,
    PolicyDecisionTable,
    ProposalTable,
    SaasResourceTable,
)
from operational_semantics.persistence.repositories import (
    ApprovalRepository,
    AuditRepository,
    EvidenceRepository,
    ExecutionRepository,
    OutcomeRepository,
    PolicyDecisionRepository,
    ProposalRepository,
    SaasResourceRepository,
)

__all__ = [
    "DatabaseEngine",
    "get_engine",
    "get_session",
    "ProposalTable",
    "EvidenceTable",
    "PolicyDecisionTable",
    "ApprovalTable",
    "ExecutionTable",
    "OutcomeTable",
    "AuditRecordTable",
    "SaasResourceTable",
    "ProposalRepository",
    "EvidenceRepository",
    "PolicyDecisionRepository",
    "ApprovalRepository",
    "ExecutionRepository",
    "OutcomeRepository",
    "AuditRepository",
    "SaasResourceRepository",
]
