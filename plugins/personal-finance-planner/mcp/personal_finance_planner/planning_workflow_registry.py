"""Versioned workflow registry for neutral goal-driven planning routes."""

from __future__ import annotations

import json
from typing import Any

WORKFLOW_REGISTRY_VERSION = "planning-workflows-0.2.0"

WORKFLOW_REGISTRY: dict[str, dict[str, Any]] = {
    "financial_independence": {
        "next_stage": "financial_independence",
        "next_skill": "plan-financial-independence",
        "next_mcp_prompt": None,
        "next_tools": [
            "calculate_financial_independence",
            "calculate_financial_independence_milestones",
        ],
        "role": "specialist",
        "goal_match": {
            "goal_categories": ["retirement_and_independence"],
            "goal_subtypes": [],
            "outcome_types": [],
            "match_type": "exact_category",
        },
    },
    "home_opportunity": {
        "next_stage": "home_opportunity",
        "next_skill": "plan-financial-independence",
        "next_mcp_prompt": None,
        "next_tools": [
            "calculate_home_opportunity_scenario",
            "calculate_home_opportunity_boundary_scenarios",
        ],
        "role": "specialist",
        "goal_match": {
            "goal_categories": ["major_purchase"],
            "goal_subtypes": ["primary_home"],
            "outcome_types": [],
            "match_type": "category_and_subtype",
        },
    },
    "cash_liquidity": {
        "next_stage": "cash_liquidity",
        "next_skill": "design-target-allocation",
        "next_mcp_prompt": "design_cash_liquidity_policy",
        "next_tools": [],
        "role": "specialist",
        "goal_match": {
            "goal_categories": ["safety_and_resilience"],
            "goal_subtypes": [],
            "outcome_types": [],
            "match_type": "exact_category",
        },
    },
    "target_allocation": {
        "next_stage": "target_allocation",
        "next_skill": "design-target-allocation",
        "next_mcp_prompt": "design_target_allocation",
        "next_tools": ["validate_target_allocation"],
        "role": "generic_fallback",
        "goal_match": None,
    },
    "planning_review": {
        "next_stage": "planning_review",
        "next_skill": "run-financial-planning",
        "next_mcp_prompt": "run_financial_planning",
        "next_tools": [],
        "role": "review_fallback",
        "goal_match": None,
    },
}


def workflow_registry() -> dict[str, Any]:
    """Return the public, read-only registry payload."""
    return {
        "registry_version": WORKFLOW_REGISTRY_VERSION,
        "classification_contract": "financial_goals-0.2.0",
        "workflows": WORKFLOW_REGISTRY,
        "safety_boundary": {
            "persists_state": False,
            "authorizes_transactions": False,
        },
    }


def workflow_registry_as_json() -> str:
    """Return the registry as stable formatted JSON."""
    return json.dumps(workflow_registry(), ensure_ascii=False, indent=2)
