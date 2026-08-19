"""Versioned source cards and prompt rendering for target allocation."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
ALLOCATION_KNOWLEDGE_DIR = PLUGIN_ROOT / "knowledge" / "allocation" / "v0.1.0"
PROMPT_TEMPLATE = (
    PLUGIN_ROOT
    / "skills"
    / "design-target-allocation"
    / "references"
    / "target-allocation-prompt.md"
)
CASH_LIQUIDITY_PROMPT_TEMPLATE = (
    PLUGIN_ROOT
    / "skills"
    / "design-target-allocation"
    / "references"
    / "cash-liquidity-policy-prompt.md"
)
PROFILE_INTAKE_PROMPT_TEMPLATE = (
    PLUGIN_ROOT
    / "skills"
    / "financial-profile-intake"
    / "references"
    / "profile-intake-prompt.md"
)
GOAL_CLARIFICATION_PROMPT_TEMPLATE = (
    PLUGIN_ROOT
    / "skills"
    / "financial-goal-clarification"
    / "references"
    / "goal-clarification-prompt.md"
)
PLANNING_SESSION_PROMPT_TEMPLATE = (
    PLUGIN_ROOT
    / "skills"
    / "run-financial-planning"
    / "references"
    / "planning-session-prompt.md"
)
BASE_CARD_IDS = (
    "cfp-board-seven-step",
    "cfa-ips-portfolio-planning",
    "cfa-goals-based-constraints",
    "sec-asset-allocation-diversification",
    "vanguard-investing-success",
    "vanguard-cash-framework",
    "finra-emergency-fund",
    "morningstar-goal-buckets",
)
CHINA_CARD_IDS = (
    "china-deposit-insurance",
    "china-asset-management-guidance",
    "china-commercial-bank-wealth-supervision",
    "china-cash-management-wealth-rules",
    "china-wealth-liquidity-risk-management",
)
CASH_LIQUIDITY_BASE_CARD_IDS = (
    "vanguard-cash-framework",
    "finra-emergency-fund",
)
CASH_LIQUIDITY_CHINA_CARD_IDS = CHINA_CARD_IDS
PROFILE_INTAKE_CARD_IDS = ("cfp-board-seven-step",)
GOAL_CLARIFICATION_CARD_IDS = (
    "cfp-board-seven-step",
    "cfa-goals-based-constraints",
)
PLANNING_SESSION_CARD_IDS = ("cfp-board-seven-step",)


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise TypeError(f"Expected a mapping in {path}")
    return value


def allocation_catalog() -> dict[str, Any]:
    return _load_yaml(ALLOCATION_KNOWLEDGE_DIR / "catalog.yaml")


def allocation_card(card_id: str) -> dict[str, Any]:
    entries = {item["id"]: item for item in allocation_catalog()["cards"]}
    if card_id not in entries:
        raise KeyError(f"Unknown allocation knowledge card: {card_id}")
    return _load_yaml(ALLOCATION_KNOWLEDGE_DIR / entries[card_id]["file"])


def allocation_catalog_as_json() -> str:
    return json.dumps(allocation_catalog(), ensure_ascii=False, indent=2)


def allocation_card_as_json(card_id: str) -> str:
    return json.dumps(allocation_card(card_id), ensure_ascii=False, indent=2)


def allocation_card_ids_for_jurisdiction(jurisdiction: str) -> tuple[str, ...]:
    normalized = jurisdiction.casefold()
    card_ids = list(BASE_CARD_IDS)
    if "china" in normalized or "中国" in jurisdiction:
        card_ids.extend(CHINA_CARD_IDS)
    return tuple(card_ids)


def cash_liquidity_card_ids_for_jurisdiction(jurisdiction: str) -> tuple[str, ...]:
    normalized = jurisdiction.casefold()
    card_ids = list(CASH_LIQUIDITY_BASE_CARD_IDS)
    if "china" in normalized or "中国" in jurisdiction:
        card_ids.extend(CASH_LIQUIDITY_CHINA_CARD_IDS)
    return tuple(card_ids)


def allocation_source_context(card_ids: Iterable[str]) -> str:
    sections: list[str] = []
    for card_id in card_ids:
        card = allocation_card(card_id)
        claims = "\n".join(f"- {item}" for item in card["usable_claims"])
        rules = "\n".join(f"- {item}" for item in card["prompt_rules"])
        limits = "\n".join(f"- {item}" for item in card["limitations"])
        sections.append(
            f"## {card['id']}: {card['title']}\n"
            f"Publisher: {card['publisher']}\n"
            f"Jurisdiction: {card['jurisdiction']}\n"
            f"Canonical URL: {card['source_url']}\n"
            f"Retrieved: {card['retrieved_at']}\n\n"
            f"Usable claims:\n{claims}\n\n"
            f"Prompt rules:\n{rules}\n\n"
            f"Limitations:\n{limits}"
        )
    return "\n\n".join(sections)


def render_target_allocation_prompt(*, planning_context: str, jurisdiction: str) -> str:
    context = planning_context.strip() or (
        "No user-specific planning context was supplied. Collect only the inputs that "
        "can materially change the target structure; do not invent percentages."
    )
    source_context = allocation_source_context(
        allocation_card_ids_for_jurisdiction(jurisdiction)
    )
    return (
        PROMPT_TEMPLATE.read_text(encoding="utf-8")
        .replace("{{jurisdiction}}", jurisdiction)
        .replace("{{source_context}}", source_context)
        .replace("{{planning_context}}", context)
    )


def render_cash_liquidity_policy_prompt(
    *, planning_context: str, product_liquidity_context: str, jurisdiction: str
) -> str:
    context = planning_context.strip() or (
        "No user-specific planning context was supplied. Collect only inputs that can "
        "materially change the cash floor or liquidity layers; do not invent an amount."
    )
    product_context = product_liquidity_context.strip() or (
        "No product-specific liquidity terms were supplied. Do not infer settlement, "
        "limits, minimum holding, guarantee, or regulatory classification from a name."
    )
    source_context = allocation_source_context(
        cash_liquidity_card_ids_for_jurisdiction(jurisdiction)
    )
    return (
        CASH_LIQUIDITY_PROMPT_TEMPLATE.read_text(encoding="utf-8")
        .replace("{{jurisdiction}}", jurisdiction)
        .replace("{{source_context}}", source_context)
        .replace("{{planning_context}}", context)
        .replace("{{product_liquidity_context}}", product_context)
    )


def render_financial_profile_intake_prompt(
    *, profile_context: str, jurisdiction: str, collection_round: str
) -> str:
    context = profile_context.strip() or (
        "No user-specific profile facts were supplied. Start with one to three "
        "high-impact questions and preserve all other fields as unknown."
    )
    round_label = collection_round.strip() or "initial"
    return (
        PROFILE_INTAKE_PROMPT_TEMPLATE.read_text(encoding="utf-8")
        .replace("{{jurisdiction}}", jurisdiction)
        .replace("{{collection_round}}", round_label)
        .replace(
            "{{source_context}}",
            allocation_source_context(PROFILE_INTAKE_CARD_IDS),
        )
        .replace("{{profile_context}}", context)
    )


def render_financial_goal_clarification_prompt(
    *, profile_context: str, goal_context: str, jurisdiction: str
) -> str:
    profile = profile_context.strip() or (
        "No confirmed profile was supplied. Record provisional goals and identify only "
        "the profile facts that materially block clarification."
    )
    goals = goal_context.strip() or (
        "No goal statement was supplied. Ask one to three questions without inventing "
        "an amount, date, priority, or commitment."
    )
    return (
        GOAL_CLARIFICATION_PROMPT_TEMPLATE.read_text(encoding="utf-8")
        .replace("{{jurisdiction}}", jurisdiction)
        .replace(
            "{{source_context}}",
            allocation_source_context(GOAL_CLARIFICATION_CARD_IDS),
        )
        .replace("{{profile_context}}", profile)
        .replace("{{goal_context}}", goals)
    )


def render_financial_planning_session_prompt(
    *,
    session_context: str,
    profile_context: str,
    goal_context: str,
    requested_capability: str,
    jurisdiction: str,
) -> str:
    session = session_context.strip() or (
        "No deterministic route result was supplied. Call "
        "route_financial_planning_stage before choosing a downstream workflow."
    )
    profile = profile_context.strip() or "No profile record was supplied."
    goals = goal_context.strip() or "No goal record was supplied."
    requested = requested_capability.strip() or "auto"
    return (
        PLANNING_SESSION_PROMPT_TEMPLATE.read_text(encoding="utf-8")
        .replace("{{jurisdiction}}", jurisdiction)
        .replace("{{requested_capability}}", requested)
        .replace("{{session_context}}", session)
        .replace("{{profile_context}}", profile)
        .replace("{{goal_context}}", goals)
        .replace(
            "{{source_context}}",
            allocation_source_context(PLANNING_SESSION_CARD_IDS),
        )
    )
