"""Optional OPA adapter interface.

Implements the same evaluation interface as PolicyEvaluator but delegates
to an OPA (Open Policy Agent) server. Not required for the default runnable system.
"""

from typing import Any

import httpx

from operational_semantics.domain.models import ActionProposal, PolicyDecision
from operational_semantics.policy.decisions import PolicyDecisionBuilder


class OPAAdapter:
    """Policy evaluator that delegates to an OPA server.

    This is an optional adapter. The default system works without OPA.
    """

    def __init__(self, opa_url: str = "http://localhost:8181") -> None:
        self.opa_url = opa_url.rstrip("/")

    def evaluate(self, proposal: ActionProposal) -> PolicyDecision:
        """Evaluate a proposal by querying OPA.

        Falls back to PROHIBITED if OPA is unreachable.
        """
        try:
            input_data = {
                "input": {
                    "proposal_id": proposal.id,
                    "action_type": proposal.action_type,
                    "operation_class": proposal.operation_class.value,
                    "system_type": proposal.system_type.value,
                    "risk_level": proposal.risk_level.value,
                    "contains_restricted_data": proposal.contains_restricted_data,
                    "evidence_count": len(proposal.evidence_ids),
                }
            }
            response = httpx.post(
                f"{self.opa_url}/v1/data/operational_semantics/allow",
                json=input_data,
                timeout=5.0,
            )
            response.raise_for_status()
            result = response.json()

            decision = result.get("result", {})
            if decision.get("allow") is True:
                return PolicyDecisionBuilder.permitted(
                    proposal_id=proposal.id,
                    explanation="Permitted by OPA policy",
                )
            if decision.get("allow") is False and decision.get("require_approval"):
                return PolicyDecisionBuilder.from_rule(
                    proposal_id=proposal.id,
                    rule=decision.get("rule", {}),
                    policy_id="opa",
                )
            return PolicyDecisionBuilder.prohibited(
                proposal_id=proposal.id,
                explanation="Prohibited by OPA policy",
            )

        except (httpx.RequestError, httpx.HTTPStatusError):
            return PolicyDecisionBuilder.prohibited(
                proposal_id=proposal.id,
                reason_codes=["OPA_UNREACHABLE"],
                explanation="OPA server unreachable — action prohibited by default",
            )
