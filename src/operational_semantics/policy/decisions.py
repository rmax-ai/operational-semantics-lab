"""Build PolicyDecision objects from evaluation results."""

from datetime import datetime, timezone

from operational_semantics.domain.enums import DecisionType
from operational_semantics.domain.models import PolicyDecision, PolicyRule


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PolicyDecisionBuilder:
    """Constructs PolicyDecision objects from matched rules."""

    @staticmethod
    def from_rule(
        proposal_id: str,
        rule: PolicyRule,
        policy_id: str = "default",
        policy_version: str = "1.0",
    ) -> PolicyDecision:
        """Build a PolicyDecision from a matched rule."""
        reason_codes: list[str] = [f"{rule.decision.value.upper()}"]
        explanation = rule.decision.value.replace("_", " ").title()

        if rule.approver_role:
            reason_codes.append(f"APPROVER_ROLE:{rule.approver_role}")
            explanation += f" — requires {rule.approver_role} approval"

        return PolicyDecision(
            id=f"pd-{proposal_id}-{_utcnow().timestamp():.0f}",
            proposal_id=proposal_id,
            policy_id=policy_id,
            policy_version=policy_version,
            decision=rule.decision,
            reason_codes=reason_codes,
            explanation=explanation,
            required_approver_role=rule.approver_role,
            remediation=list(rule.remediation),
            evaluated_at=_utcnow(),
        )

    @staticmethod
    def prohibited(
        proposal_id: str,
        reason_codes: list[str] | None = None,
        explanation: str = "",
        remediation: list[str] | None = None,
        policy_id: str = "default",
        policy_version: str = "1.0",
    ) -> PolicyDecision:
        """Build a PROHIBITED decision."""
        return PolicyDecision(
            id=f"pd-{proposal_id}-{_utcnow().timestamp():.0f}",
            proposal_id=proposal_id,
            policy_id=policy_id,
            policy_version=policy_version,
            decision=DecisionType.PROHIBITED,
            reason_codes=reason_codes or ["PROHIBITED"],
            explanation=explanation or "Action is prohibited by policy",
            evaluated_at=_utcnow(),
        )

    @staticmethod
    def permitted(
        proposal_id: str,
        explanation: str = "",
        policy_id: str = "default",
        policy_version: str = "1.0",
    ) -> PolicyDecision:
        """Build a PERMITTED decision."""
        return PolicyDecision(
            id=f"pd-{proposal_id}-{_utcnow().timestamp():.0f}",
            proposal_id=proposal_id,
            policy_id=policy_id,
            policy_version=policy_version,
            decision=DecisionType.PERMITTED,
            reason_codes=["READ_ALLOWED" if "read" in proposal_id.lower() else "WRITE_PROPOSAL_ALLOWED"],
            explanation=explanation or "Action is permitted by policy",
            evaluated_at=_utcnow(),
        )
