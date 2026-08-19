"""Deterministic stage routing for the financial-planning coordinator."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from personal_finance_planner.planning_workflow_registry import (
    WORKFLOW_REGISTRY,
    WORKFLOW_REGISTRY_VERSION,
)

COORDINATOR_CAPABILITIES = {
    "auto",
    "profile_intake",
    "goal_clarification",
    "workspace_state",
}
RECORD_STATES = {"absent", "proposed", "confirmed"}
CHANGE_SCOPES = {"none", "profile", "goals"}
COMMITMENTS = {"committed", "optional", "exploratory", "deferred"}
ACTIONABLE_COMMITMENTS = {"committed", "optional"}
PROGRESS_STATES = {"in_progress", "completed", "stale", "blocked"}
SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]*$")
PLUGIN_ROOT = Path(__file__).resolve().parents[2]
ROUTE_SCHEMA_FILES = {
    "input": "planning-session-route-input.schema.json",
    "output": "planning-session-route-output.schema.json",
}


def route_schema_as_json(direction: str) -> str:
    """Return a route input or output schema as formatted JSON."""
    try:
        filename = ROUTE_SCHEMA_FILES[direction]
    except KeyError as exc:
        raise ValueError("direction must be input or output") from exc
    payload = json.loads(
        (PLUGIN_ROOT / "schemas" / filename).read_text(encoding="utf-8")
    )
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _result(
    *,
    requested_capability: str,
    next_stage: str,
    next_skill: str,
    next_mcp_prompt: str | None,
    next_tools: list[str],
    reason_codes: list[str],
    blocked_by: list[str] | None = None,
    requires_user_choice: bool = False,
    available_next_capabilities: list[str] | None = None,
    persists_state: bool = False,
    selection_mode: str,
    evaluated_goal_ids: list[str] | None = None,
    matched_goal_ids: list[str] | None = None,
    candidate_workflows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "routing_version": "planning-route-0.2.0",
        "workflow_registry_version": WORKFLOW_REGISTRY_VERSION,
        "requested_capability": requested_capability,
        "next_stage": next_stage,
        "next_skill": next_skill,
        "next_mcp_prompt": next_mcp_prompt,
        "next_tools": next_tools,
        "reason_codes": reason_codes,
        "blocked_by": blocked_by or [],
        "requires_user_choice": requires_user_choice,
        "available_next_capabilities": available_next_capabilities or [],
        "selection_mode": selection_mode,
        "evaluated_goal_ids": evaluated_goal_ids or [],
        "matched_goal_ids": matched_goal_ids or [],
        "candidate_workflows": candidate_workflows or [],
        "safety_boundary": {
            "persists_state": persists_state,
            "authorizes_transactions": False,
        },
    }


def _profile_route(requested_capability: str, reason: str) -> dict[str, Any]:
    return _result(
        requested_capability=requested_capability,
        next_stage="profile_intake",
        next_skill="financial-profile-intake",
        next_mcp_prompt="collect_financial_profile",
        next_tools=["validate_financial_profile"],
        reason_codes=[reason],
        blocked_by=["profile"],
        selection_mode="precondition",
    )


def _goal_route(requested_capability: str, reason: str) -> dict[str, Any]:
    return _result(
        requested_capability=requested_capability,
        next_stage="goal_clarification",
        next_skill="financial-goal-clarification",
        next_mcp_prompt="clarify_financial_goals",
        next_tools=["validate_financial_goals"],
        reason_codes=[reason],
        blocked_by=["goals"],
        selection_mode="precondition",
    )


def _goal_taxonomy() -> tuple[set[str], set[str]]:
    schema = json.loads(
        (PLUGIN_ROOT / "schemas" / "financial-goals-confirmed.schema.json").read_text(
            encoding="utf-8"
        )
    )
    properties = schema["$defs"]["goal"]["properties"]
    return set(properties["goal_category"]["enum"]), set(
        properties["outcome_type"]["enum"]
    )


def _validated_goal_summaries(
    goal_summaries: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    categories, outcomes = _goal_taxonomy()
    required = {
        "goal_id",
        "goal_category",
        "goal_subtype",
        "outcome_type",
        "priority_rank",
        "commitment",
    }
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(goal_summaries or []):
        if not isinstance(raw, dict) or set(raw) != required:
            raise ValueError(
                f"goal_summaries[{index}] must contain exactly {sorted(required)}"
            )
        goal_id = raw["goal_id"]
        subtype = raw["goal_subtype"]
        if not isinstance(goal_id, str) or not SLUG_PATTERN.fullmatch(goal_id):
            raise ValueError(f"Invalid goal_id at goal_summaries[{index}]")
        if goal_id in seen:
            raise ValueError(f"Duplicate goal_id: {goal_id}")
        seen.add(goal_id)
        if (
            not isinstance(raw["goal_category"], str)
            or raw["goal_category"] not in categories
        ):
            raise ValueError(f"Unsupported goal_category: {raw['goal_category']}")
        if not isinstance(subtype, str) or not SLUG_PATTERN.fullmatch(subtype):
            raise ValueError(f"Invalid goal_subtype at goal_summaries[{index}]")
        if (
            not isinstance(raw["outcome_type"], str)
            or raw["outcome_type"] not in outcomes
        ):
            raise ValueError(f"Unsupported outcome_type: {raw['outcome_type']}")
        if not isinstance(raw["priority_rank"], int) or isinstance(
            raw["priority_rank"], bool
        ) or raw["priority_rank"] < 1:
            raise ValueError(f"Invalid priority_rank at goal_summaries[{index}]")
        if (
            not isinstance(raw["commitment"], str)
            or raw["commitment"] not in COMMITMENTS
        ):
            raise ValueError(f"Unsupported commitment: {raw['commitment']}")
        normalized.append(dict(raw))
    return normalized


def _validated_progress(
    workflow_progress: list[dict[str, Any]] | None,
    known_goals: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    required = {"capability", "goal_ids", "status"}
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(workflow_progress or []):
        if not isinstance(raw, dict) or set(raw) != required:
            raise ValueError(
                f"workflow_progress[{index}] must contain exactly {sorted(required)}"
            )
        capability = raw["capability"]
        goal_ids = raw["goal_ids"]
        if capability not in WORKFLOW_REGISTRY:
            raise ValueError(f"Unsupported progress capability: {capability}")
        if not isinstance(goal_ids, list) or not goal_ids:
            raise ValueError(f"workflow_progress[{index}].goal_ids must be non-empty")
        if not all(
            isinstance(goal_id, str) and SLUG_PATTERN.fullmatch(goal_id)
            for goal_id in goal_ids
        ):
            raise ValueError(f"Invalid workflow progress goal ID at index {index}")
        if len(goal_ids) != len(set(goal_ids)):
            raise ValueError(f"Duplicate workflow progress goal ID at index {index}")
        unknown = set(goal_ids) - set(known_goals)
        if unknown:
            raise ValueError(f"Unknown workflow progress goal_id: {sorted(unknown)[0]}")
        if raw["status"] not in PROGRESS_STATES:
            raise ValueError(f"Unsupported workflow progress status: {raw['status']}")
        workflow = WORKFLOW_REGISTRY[capability]
        if workflow["role"] == "specialist":
            mismatched = [
                goal_id
                for goal_id in goal_ids
                if not _matches(known_goals[goal_id], workflow)
            ]
            if mismatched:
                raise ValueError(
                    "Workflow progress goal does not match capability: "
                    f"{capability}/{mismatched[0]}"
                )
        normalized.append(
            {
                "capability": capability,
                "goal_ids": list(goal_ids),
                "status": raw["status"],
            }
        )
    return normalized


def _matches(goal: dict[str, Any], workflow: dict[str, Any]) -> bool:
    match = workflow.get("goal_match")
    if not match:
        return False
    if goal["goal_category"] not in match["goal_categories"]:
        return False
    if match["goal_subtypes"] and goal["goal_subtype"] not in match["goal_subtypes"]:
        return False
    if match["outcome_types"] and goal["outcome_type"] not in match["outcome_types"]:
        return False
    return True


def _candidate(
    capability: str, goal_ids: list[str], match_type: str, reason_codes: list[str]
) -> dict[str, Any]:
    return {
        "capability": capability,
        "goal_ids": sorted(goal_ids),
        "match_type": match_type,
        "reason_codes": reason_codes,
    }


def _is_completed(
    capability: str, goal_ids: list[str], progress: list[dict[str, Any]]
) -> bool:
    completed_goal_ids: set[str] = set()
    for item in progress:
        if item["capability"] == capability and item["status"] == "completed":
            completed_goal_ids.update(item["goal_ids"])
    return set(goal_ids) == completed_goal_ids


def _goal_has_completed_workflow(
    capability: str, goal_id: str, progress: list[dict[str, Any]]
) -> bool:
    return any(
        item["capability"] == capability
        and item["status"] == "completed"
        and goal_id in item["goal_ids"]
        for item in progress
    )


def _workflow_route(
    *,
    requested_capability: str,
    capability: str,
    reason_codes: list[str],
    selection_mode: str,
    evaluated_goal_ids: list[str] | None = None,
    matched_goal_ids: list[str] | None = None,
    candidate_workflows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    workflow = WORKFLOW_REGISTRY[capability]
    return _result(
        requested_capability=requested_capability,
        next_stage=workflow["next_stage"],
        next_skill=workflow["next_skill"],
        next_mcp_prompt=workflow["next_mcp_prompt"],
        next_tools=workflow["next_tools"],
        reason_codes=reason_codes,
        selection_mode=selection_mode,
        evaluated_goal_ids=evaluated_goal_ids,
        matched_goal_ids=matched_goal_ids,
        candidate_workflows=candidate_workflows,
    )


def route_planning_session(
    *,
    requested_capability: str,
    profile_state: str,
    goals_state: str,
    profile_has_blocking_conflicts: bool = False,
    goals_have_unresolved_conflicts: bool = False,
    change_scope: str = "none",
    goal_summaries: list[dict[str, Any]] | None = None,
    workflow_progress: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Select one planning stage without persisting state or authorizing action."""
    supported_capabilities = COORDINATOR_CAPABILITIES | set(WORKFLOW_REGISTRY)
    if requested_capability not in supported_capabilities:
        raise ValueError(f"Unsupported requested_capability: {requested_capability}")
    if profile_state not in RECORD_STATES:
        raise ValueError(f"Unsupported profile_state: {profile_state}")
    if goals_state not in RECORD_STATES:
        raise ValueError(f"Unsupported goals_state: {goals_state}")
    if change_scope not in CHANGE_SCOPES:
        raise ValueError(f"Unsupported change_scope: {change_scope}")

    goals = _validated_goal_summaries(goal_summaries)
    if goals and goals_state != "confirmed":
        raise ValueError("goal_summaries require goals_state=confirmed")
    if workflow_progress and goals_state != "confirmed":
        raise ValueError("workflow_progress requires goals_state=confirmed")
    progress = _validated_progress(
        workflow_progress, {item["goal_id"]: item for item in goals}
    )

    if change_scope == "profile":
        return _profile_route(requested_capability, "profile_change_requested")
    if change_scope == "goals":
        return _goal_route(requested_capability, "goal_change_requested")
    if requested_capability == "profile_intake":
        return _profile_route(requested_capability, "explicit_profile_request")
    if requested_capability == "goal_clarification":
        return _goal_route(requested_capability, "explicit_goal_request")
    if requested_capability == "workspace_state":
        return _result(
            requested_capability=requested_capability,
            next_stage="workspace_state",
            next_skill="manage-financial-planning-workspace",
            next_mcp_prompt="manage_financial_planning_workspace",
            next_tools=[
                "initialize_financial_planning_workspace",
                "read_financial_planning_workspace",
                "persist_confirmed_financial_state",
            ],
            reason_codes=["explicit_workspace_state_request"],
            persists_state=True,
            selection_mode="workspace",
        )

    if requested_capability in WORKFLOW_REGISTRY or requested_capability == "auto":
        if profile_has_blocking_conflicts:
            return _profile_route(requested_capability, "blocking_profile_conflict")
        if profile_state != "confirmed":
            return _profile_route(requested_capability, f"profile_{profile_state}")
        if goals_have_unresolved_conflicts:
            return _goal_route(requested_capability, "unresolved_goal_conflict")
        if goals_state != "confirmed":
            return _goal_route(requested_capability, f"goals_{goals_state}")

    if requested_capability in WORKFLOW_REGISTRY:
        actionable = [
            item for item in goals if item["commitment"] in ACTIONABLE_COMMITMENTS
        ]
        matched = []
        workflow = WORKFLOW_REGISTRY[requested_capability]
        if workflow["role"] == "specialist":
            matched = [item["goal_id"] for item in actionable if _matches(item, workflow)]
        elif requested_capability == "target_allocation":
            matched = [item["goal_id"] for item in actionable]
        candidate = _candidate(
            requested_capability,
            matched,
            "explicit_request",
            ["explicit_registered_workflow_request"],
        )
        return _workflow_route(
            requested_capability=requested_capability,
            capability=requested_capability,
            reason_codes=["requested_workflow_ready"],
            selection_mode="explicit",
            evaluated_goal_ids=[item["goal_id"] for item in actionable],
            matched_goal_ids=matched,
            candidate_workflows=[candidate],
        )

    if not goals:
        candidates = [
            _candidate(
                "target_allocation", [], "legacy_fallback", ["classified_goals_unavailable"]
            ),
            _candidate(
                "planning_review", [], "legacy_fallback", ["classified_goals_unavailable"]
            ),
        ]
        return _result(
            requested_capability=requested_capability,
            next_stage="choose_planning_workflow",
            next_skill="run-financial-planning",
            next_mcp_prompt="run_financial_planning",
            next_tools=[],
            reason_codes=["profile_and_goals_confirmed", "classified_goals_unavailable"],
            requires_user_choice=True,
            available_next_capabilities=["target_allocation", "planning_review"],
            selection_mode="legacy_fallback",
            candidate_workflows=candidates,
        )

    actionable = [item for item in goals if item["commitment"] in ACTIONABLE_COMMITMENTS]
    evaluated_goal_ids = [item["goal_id"] for item in actionable]
    specialist_candidates: list[dict[str, Any]] = []
    for capability, workflow in WORKFLOW_REGISTRY.items():
        if workflow["role"] != "specialist":
            continue
        matching = [item for item in actionable if _matches(item, workflow)]
        incomplete = [
            item
            for item in matching
            if not _goal_has_completed_workflow(
                capability, item["goal_id"], progress
            )
        ]
        if not incomplete:
            continue
        minimum_priority = min(item["priority_rank"] for item in incomplete)
        goal_ids = [
            item["goal_id"]
            for item in incomplete
            if item["priority_rank"] == minimum_priority
        ]
        specialist_candidates.append(
            {
                "priority_rank": minimum_priority,
                "candidate": _candidate(
                    capability,
                    goal_ids,
                    workflow["goal_match"]["match_type"],
                    ["neutral_goal_classification_match"],
                ),
            }
        )

    if specialist_candidates:
        next_priority = min(item["priority_rank"] for item in specialist_candidates)
        candidates = [
            item["candidate"]
            for item in specialist_candidates
            if item["priority_rank"] == next_priority
        ]
        if len(candidates) == 1:
            selected = candidates[0]
            return _workflow_route(
                requested_capability="auto",
                capability=selected["capability"],
                reason_codes=["profile_and_goals_confirmed", "goal_classification_match"],
                selection_mode="goal_match",
                evaluated_goal_ids=evaluated_goal_ids,
                matched_goal_ids=selected["goal_ids"],
                candidate_workflows=candidates,
            )
        return _result(
            requested_capability="auto",
            next_stage="choose_planning_workflow",
            next_skill="run-financial-planning",
            next_mcp_prompt="run_financial_planning",
            next_tools=[],
            reason_codes=["equal_priority_goal_workflow_tie"],
            requires_user_choice=True,
            available_next_capabilities=[item["capability"] for item in candidates],
            selection_mode="goal_tie",
            evaluated_goal_ids=evaluated_goal_ids,
            matched_goal_ids=sorted(
                {goal_id for item in candidates for goal_id in item["goal_ids"]}
            ),
            candidate_workflows=candidates,
        )

    if actionable and not _is_completed("target_allocation", evaluated_goal_ids, progress):
        candidate = _candidate(
            "target_allocation",
            evaluated_goal_ids,
            "generic_allocation",
            ["no_uncompleted_specialist_match"],
        )
        return _workflow_route(
            requested_capability="auto",
            capability="target_allocation",
            reason_codes=["profile_and_goals_confirmed", "generic_goal_allocation_fallback"],
            selection_mode="generic_fallback",
            evaluated_goal_ids=evaluated_goal_ids,
            matched_goal_ids=evaluated_goal_ids,
            candidate_workflows=[candidate],
        )

    reason = "target_allocation_completed" if actionable else "no_actionable_goals"
    candidate = _candidate("planning_review", [], "generic_review", [reason])
    return _workflow_route(
        requested_capability="auto",
        capability="planning_review",
        reason_codes=[reason],
        selection_mode="generic_fallback",
        evaluated_goal_ids=evaluated_goal_ids,
        candidate_workflows=[candidate],
    )
