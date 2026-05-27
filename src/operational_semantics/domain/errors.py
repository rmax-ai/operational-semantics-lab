"""Domain errors for the operational semantics layer."""


class DomainError(Exception):
    """Base error for domain-level violations."""

    def __init__(self, message: str, code: str | None = None) -> None:
        self.code = code or "DOMAIN_ERROR"
        super().__init__(message)


class ValidationError(DomainError):
    """A proposal or entity failed semantic or structural validation."""

    def __init__(self, message: str, details: list[str] | None = None) -> None:
        self.details = details or []
        super().__init__(message, code="VALIDATION_ERROR")


class PolicyError(DomainError):
    """A policy evaluation prevented or restricted an action."""

    def __init__(
        self,
        message: str,
        reason_codes: list[str] | None = None,
        remediation: list[str] | None = None,
    ) -> None:
        self.reason_codes = reason_codes or []
        self.remediation = remediation or []
        super().__init__(message, code="POLICY_ERROR")


class ApprovalError(DomainError):
    """An approval-related operation failed."""

    def __init__(self, message: str, reason: str | None = None) -> None:
        self.reason = reason
        super().__init__(message, code="APPROVAL_ERROR")


class ExecutionError(DomainError):
    """An execution attempt failed or was blocked."""

    def __init__(self, message: str, reason: str | None = None) -> None:
        self.reason = reason
        super().__init__(message, code="EXECUTION_ERROR")
