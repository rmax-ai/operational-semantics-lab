"""Deterministic YAML-based policy evaluator and rule engine."""

from operational_semantics.policy.evaluator import PolicyEvaluator
from operational_semantics.policy.rules import RuleMatcher, match_rule
from operational_semantics.policy.decisions import PolicyDecisionBuilder
from operational_semantics.policy.opa_adapter import OPAAdapter

__all__ = [
    "PolicyEvaluator",
    "RuleMatcher",
    "match_rule",
    "PolicyDecisionBuilder",
    "OPAAdapter",
]
