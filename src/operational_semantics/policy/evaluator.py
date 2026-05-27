"""Deterministic YAML-based policy evaluator.

Loads policy definitions from YAML files and evaluates proposals against them.
"""

from pathlib import Path
from typing import Any

import yaml

from operational_semantics.domain.enums import OperationClass
from operational_semantics.domain.models import ActionProposal, Policy, PolicyDecision, PolicyRule
from operational_semantics.policy.decisions import PolicyDecisionBuilder
from operational_semantics.policy.rules import match_rule


class PolicyEvaluator:
    """Evaluates proposals against YAML-defined policies."""

    def __init__(self, policy_dir: str | Path | None = None) -> None:
        self._policies: dict[str, Policy] = {}
        if policy_dir:
            self.load_directory(Path(policy_dir))

    def load_directory(self, policy_dir: Path) -> None:
        """Load all YAML policy files from a directory."""
        if not policy_dir.exists():
            return
        for f in sorted(policy_dir.glob("*.yaml")):
            self.load_file(f)

    def load_file(self, path: Path) -> None:
        """Load a single YAML policy file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        if not data or "system" not in data:
            return

        rules = []
        for r in data.get("rules", []):
            rules.append(PolicyRule(**r))

        policy = Policy(
            id=data.get("id", f"policy-{data['system']}"),
            system=data["system"],
            version=data.get("version", "1.0"),
            rules=rules,
        )
        self._policies[policy.system] = policy

    def get_policy(self, system: str) -> Policy | None:
        """Get a policy by system name."""
        return self._policies.get(system)

    def evaluate(
        self,
        proposal: ActionProposal,
    ) -> PolicyDecision:
        """Evaluate a proposal against the relevant policy.

        Returns a PolicyDecision with deterministically computed result.
        """
        policy = self._policies.get(proposal.system_type.value)
        if policy is None:
            return PolicyDecisionBuilder.prohibited(
                proposal_id=proposal.id,
                reason_codes=["NO_POLICY_FOUND"],
                explanation=f"No policy configured for system: {proposal.system_type.value}",
            )

        operation = proposal.operation_class.value
        action_type = proposal.action_type
        when: dict[str, Any] = {
            "contains_restricted_data": proposal.contains_restricted_data,
        }

        # Determine target scope (specific to system type)
        target_scope = None
        if proposal.system_type.value == "slack":
            target_scope = proposal.payload.get("target_scope")
        elif proposal.system_type.value == "crm":
            when["target_status"] = proposal.payload.get("target_status")
            when["minimum_evidence_count"] = len(proposal.evidence_ids)

        rule = match_rule(
            policy.rules,
            operation=operation,
            action_type=action_type,
            target_scope=target_scope,
            when=when,
        )

        if rule is None:
            # Default: if read, permit; if write, require approval
            if proposal.operation_class == OperationClass.READ:
                return PolicyDecisionBuilder.permitted(
                    proposal_id=proposal.id,
                    explanation=f"Read operation permitted by default for {policy.system}",
                )
            return PolicyDecisionBuilder.prohibited(
                proposal_id=proposal.id,
                reason_codes=["NO_MATCHING_RULE"],
                explanation=f"No matching rule for {operation}/{action_type} in {policy.system}",
            )

        return PolicyDecisionBuilder.from_rule(
            proposal_id=proposal.id,
            rule=rule,
            policy_id=policy.id,
            policy_version=policy.version,
        )
