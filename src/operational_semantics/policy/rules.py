"""Rule matching engine for deterministic policy evaluation."""

from typing import Any

from operational_semantics.domain.enums import DecisionType
from operational_semantics.domain.models import PolicyRule


def match_rule(
    rules: list[PolicyRule],
    operation: str,
    action_type: str | None = None,
    target_scope: str | None = None,
    when: dict[str, Any] | None = None,
) -> PolicyRule | None:
    """Find the first policy rule matching the given operation and conditions.

    Rules are evaluated in order. The first match wins.
    """
    when = when or {}

    for rule in rules:
        if rule.operation != operation:
            continue

        if rule.action_type and rule.action_type != action_type:
            continue

        if rule.target_scope and rule.target_scope != target_scope:
            continue

        # Evaluate when conditions
        if rule.when:
            all_match = all(
                when.get(key) == value
                for key, value in rule.when.items()
            )
            if not all_match:
                continue

        return rule

    return None


class RuleMatcher:
    """Maintains a set of rules and matches against them."""

    def __init__(self, rules: list[PolicyRule] | None = None) -> None:
        self._rules: list[PolicyRule] = rules or []

    def add_rule(self, rule: PolicyRule) -> None:
        """Add a rule to the matcher."""
        self._rules.append(rule)

    def add_rules(self, rules: list[PolicyRule]) -> None:
        """Add multiple rules."""
        self._rules.extend(rules)

    def match(
        self,
        operation: str,
        action_type: str | None = None,
        target_scope: str | None = None,
        when: dict[str, Any] | None = None,
    ) -> PolicyRule | None:
        """Find the first matching rule."""
        return match_rule(self._rules, operation, action_type, target_scope, when)
