"""Enumerations for the operational semantics domain model."""

from enum import Enum


class OperationClass(str, Enum):
    """Classification of an operation's capability level."""

    READ = "read"
    PROPOSE_WRITE = "propose_write"
    EXECUTE_WRITE = "execute_write"


class DecisionType(str, Enum):
    """Result of a policy evaluation."""

    PERMITTED = "permitted"
    APPROVAL_REQUIRED = "approval_required"
    PROHIBITED = "prohibited"


class ApprovalStatus(str, Enum):
    """Lifecycle status of an approval request."""

    PENDING = "pending"
    GRANTED = "granted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"


class ExecutionStatus(str, Enum):
    """Outcome status of an execution attempt."""

    BLOCKED = "blocked"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class RiskLevel(str, Enum):
    """Risk classification for an action."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceType(str, Enum):
    """Categories of evidence that can support a proposal."""

    INCIDENT_RECORD = "incident_record"
    RUNBOOK_EXCERPT = "runbook_excerpt"
    POLICY_DOCUMENT = "policy_document"
    CUSTOMER_CASE = "customer_case"
    MESSAGE_THREAD = "message_thread"


class SystemType(str, Enum):
    """External system types supported by the governed gateway."""

    JIRA = "jira"
    SLACK = "slack"
    CRM = "crm"
