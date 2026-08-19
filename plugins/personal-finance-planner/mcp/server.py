"""MCP entry point for Personal Finance Planning Core."""

from __future__ import annotations

import json
from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from mcp_types import ToolAnnotations
from personal_finance_planner.allocation_knowledge import (
    allocation_card_as_json,
    allocation_catalog_as_json,
    render_cash_liquidity_policy_prompt,
    render_financial_goal_clarification_prompt,
    render_financial_planning_session_prompt,
    render_financial_profile_intake_prompt,
    render_target_allocation_prompt,
)
from personal_finance_planner.boundary import calculate_home_opportunity_boundaries
from personal_finance_planner.calculator import calculate_fi
from personal_finance_planner.home import calculate_home_opportunity
from personal_finance_planner.knowledge import card_as_json, catalog_as_json
from personal_finance_planner.milestones import calculate_fi_milestones
from personal_finance_planner.planning_router import (
    route_planning_session,
    route_schema_as_json,
)
from personal_finance_planner.planning_workflow_registry import (
    workflow_registry_as_json,
)
from personal_finance_planner.planning_state import (
    schema_as_json,
)
from personal_finance_planner.planning_state import (
    validate_financial_goals as validate_financial_goals_payload,
)
from personal_finance_planner.planning_state import (
    validate_financial_profile as validate_financial_profile_payload,
)
from personal_finance_planner.planning_state import (
    validate_target_allocation as validate_target_allocation_payload,
)
from personal_finance_planner.workspace_repository import (
    initialize_planning_workspace,
    persist_confirmed_state,
    read_planning_workspace,
    render_workspace_state_prompt,
    workspace_schema_as_json,
)
from pydantic import Field

mcp = MCPServer(
    "Personal Finance Planning Core",
    instructions=(
        "Provides versioned public financial-planning guidance and deterministic, "
        "read-only calculations plus source-grounded profile-intake, goal-clarification, "
        "target-allocation, and cash-liquidity prompts. A narrowly controlled local "
        "Workspace repository can persist only explicitly confirmed profile, goal, or "
        "target-allocation "
        "versions after named user confirmation. It does "
        "not contain personal data, recommend products, estimate unsupported pension "
        "benefits, or execute transactions."
    ),
)


@mcp.resource("fi://catalog", mime_type="application/json")
def financial_independence_catalog() -> str:
    """List the versioned public sources available for FI planning."""
    return catalog_as_json()


@mcp.resource("fi://v0.1.0/sources/bengen-1994", mime_type="application/json")
def bengen_1994() -> str:
    """Historical withdrawal-rate research card."""
    return card_as_json("bengen-1994")


@mcp.resource("fi://v0.1.0/sources/morningstar-2025", mime_type="application/json")
def morningstar_2025() -> str:
    """Morningstar 2025 retirement-income research card."""
    return card_as_json("morningstar-2025")


@mcp.resource(
    "fi://v0.1.0/sources/vanguard-retirement-income",
    mime_type="application/json",
)
def vanguard_retirement_income() -> str:
    """Vanguard dynamic-spending and sequence-risk principles card."""
    return card_as_json("vanguard-retirement-income")


@mcp.resource(
    "fi://v0.1.0/sources/china-pension-calculator",
    mime_type="application/json",
)
def china_pension_calculator() -> str:
    """Official China pension-calculator route card."""
    return card_as_json("china-pension-calculator")


@mcp.resource(
    "fi://v0.1.0/sources/china-retirement-policy",
    mime_type="application/json",
)
def china_retirement_policy() -> str:
    """Official China gradual delayed-retirement policy card."""
    return card_as_json("china-retirement-policy")


@mcp.resource(
    "fi://v0.1.0/sources/shanghai-mortgage-tax",
    mime_type="application/json",
)
def shanghai_mortgage_tax() -> str:
    """Official Shanghai mortgage-interest tax FAQ card."""
    return card_as_json("shanghai-mortgage-tax")


@mcp.resource(
    "fi://v0.1.0/sources/china-lpr-2026-07",
    mime_type="application/json",
)
def china_lpr_2026_07() -> str:
    """Official five-year-and-over LPR benchmark card."""
    return card_as_json("china-lpr-2026-07")


@mcp.resource(
    "fi://v0.1.0/sources/shanghai-housing-credit-policy-2025",
    mime_type="application/json",
)
def shanghai_housing_credit_policy_2025() -> str:
    """Official Shanghai commercial-mortgage pricing policy card."""
    return card_as_json("shanghai-housing-credit-policy-2025")


@mcp.resource(
    "fi://v0.1.0/sources/shanghai-housing-policy-2026",
    mime_type="application/json",
)
def shanghai_housing_policy_2026() -> str:
    """Official Shanghai 2026 housing and provident-fund policy card."""
    return card_as_json("shanghai-housing-policy-2026")


@mcp.resource(
    "fi://v0.1.0/sources/china-provident-fund-rate-2025",
    mime_type="application/json",
)
def china_provident_fund_rate_2025() -> str:
    """Official provident-fund mortgage-rate policy card."""
    return card_as_json("china-provident-fund-rate-2025")


@mcp.resource(
    "fi://v0.1.0/sources/shanghai-provident-fund-loan-eligibility",
    mime_type="application/json",
)
def shanghai_provident_fund_loan_eligibility() -> str:
    """Official Shanghai provident-fund eligibility and amount rules card."""
    return card_as_json("shanghai-provident-fund-loan-eligibility")


@mcp.resource("allocation://catalog", mime_type="application/json")
def target_allocation_catalog() -> str:
    """List professional sources used by the target-allocation prompt."""
    return allocation_catalog_as_json()


@mcp.resource(
    "allocation://v0.1.0/sources/cfp-board-seven-step",
    mime_type="application/json",
)
def allocation_cfp_board_seven_step() -> str:
    """CFP Board seven-step financial-planning process card."""
    return allocation_card_as_json("cfp-board-seven-step")


@mcp.resource(
    "allocation://v0.1.0/sources/cfa-ips-portfolio-planning",
    mime_type="application/json",
)
def allocation_cfa_ips_portfolio_planning() -> str:
    """CFA Institute IPS and portfolio-planning card."""
    return allocation_card_as_json("cfa-ips-portfolio-planning")


@mcp.resource(
    "allocation://v0.1.0/sources/cfa-goals-based-constraints",
    mime_type="application/json",
)
def allocation_cfa_goals_based_constraints() -> str:
    """CFA Institute goals-based and real-world-constraints card."""
    return allocation_card_as_json("cfa-goals-based-constraints")


@mcp.resource(
    "allocation://v0.1.0/sources/sec-asset-allocation-diversification",
    mime_type="application/json",
)
def allocation_sec_asset_allocation_diversification() -> str:
    """SEC Investor.gov asset-allocation and diversification card."""
    return allocation_card_as_json("sec-asset-allocation-diversification")


@mcp.resource(
    "allocation://v0.1.0/sources/vanguard-investing-success",
    mime_type="application/json",
)
def allocation_vanguard_investing_success() -> str:
    """Vanguard goals, balance, cost, and discipline card."""
    return allocation_card_as_json("vanguard-investing-success")


@mcp.resource(
    "allocation://v0.1.0/sources/vanguard-cash-framework",
    mime_type="application/json",
)
def allocation_vanguard_cash_framework() -> str:
    """Vanguard goal-based cash-allocation framework card."""
    return allocation_card_as_json("vanguard-cash-framework")


@mcp.resource(
    "allocation://v0.1.0/sources/finra-emergency-fund",
    mime_type="application/json",
)
def allocation_finra_emergency_fund() -> str:
    """FINRA emergency-fund planning and accessibility card."""
    return allocation_card_as_json("finra-emergency-fund")


@mcp.resource(
    "allocation://v0.1.0/sources/china-deposit-insurance",
    mime_type="application/json",
)
def allocation_china_deposit_insurance() -> str:
    """Official China mainland deposit-insurance rule card."""
    return allocation_card_as_json("china-deposit-insurance")


@mcp.resource(
    "allocation://v0.1.0/sources/china-asset-management-guidance",
    mime_type="application/json",
)
def allocation_china_asset_management_guidance() -> str:
    """Official cross-sector China mainland asset-management guidance card."""
    return allocation_card_as_json("china-asset-management-guidance")


@mcp.resource(
    "allocation://v0.1.0/sources/china-commercial-bank-wealth-supervision",
    mime_type="application/json",
)
def allocation_china_commercial_bank_wealth_supervision() -> str:
    """Official commercial-bank wealth supervision rule card."""
    return allocation_card_as_json("china-commercial-bank-wealth-supervision")


@mcp.resource(
    "allocation://v0.1.0/sources/china-cash-management-wealth-rules",
    mime_type="application/json",
)
def allocation_china_cash_management_wealth_rules() -> str:
    """Official China mainland cash-management wealth-product rule card."""
    return allocation_card_as_json("china-cash-management-wealth-rules")


@mcp.resource(
    "allocation://v0.1.0/sources/china-wealth-liquidity-risk-management",
    mime_type="application/json",
)
def allocation_china_wealth_liquidity_risk_management() -> str:
    """Official wealth-product liquidity-risk management rule card."""
    return allocation_card_as_json("china-wealth-liquidity-risk-management")


@mcp.resource(
    "allocation://v0.1.0/sources/morningstar-goal-buckets",
    mime_type="application/json",
)
def allocation_morningstar_goal_buckets() -> str:
    """Morningstar time-segmented goal-bucket practitioner card."""
    return allocation_card_as_json("morningstar-goal-buckets")


@mcp.resource(
    "planning://schemas/financial-profile-proposal",
    mime_type="application/schema+json",
)
def financial_profile_proposal_schema() -> str:
    """Schema for unconfirmed, progressively collected profile facts."""
    return schema_as_json("profile", "proposed")


@mcp.resource(
    "planning://schemas/financial-profile-confirmed",
    mime_type="application/schema+json",
)
def financial_profile_confirmed_schema() -> str:
    """Schema requiring an explicit confirmation scope for profile facts."""
    return schema_as_json("profile", "confirmed")


@mcp.resource(
    "planning://schemas/financial-goals-proposal",
    mime_type="application/schema+json",
)
def financial_goals_proposal_schema() -> str:
    """Schema for proposed goals, uncertainty, and visible conflicts."""
    return schema_as_json("goals", "proposed")


@mcp.resource(
    "planning://schemas/financial-goals-confirmed",
    mime_type="application/schema+json",
)
def financial_goals_confirmed_schema() -> str:
    """Schema requiring explicit confirmation of named financial goals."""
    return schema_as_json("goals", "confirmed")


@mcp.resource(
    "planning://schemas/target-allocation-proposal",
    mime_type="application/schema+json",
)
def target_allocation_proposal_schema() -> str:
    """Schema for a structured, unconfirmed target-allocation policy."""
    return schema_as_json("allocation", "proposed")


@mcp.resource(
    "planning://schemas/target-allocation-confirmed",
    mime_type="application/schema+json",
)
def target_allocation_confirmed_schema() -> str:
    """Schema for an explicitly confirmed target-allocation policy."""
    return schema_as_json("allocation", "confirmed")


@mcp.resource(
    "planning://schemas/planning-session-route-input",
    mime_type="application/schema+json",
)
def planning_session_route_input_schema() -> str:
    """Schema for deterministic financial-planning route inputs."""
    return route_schema_as_json("input")


@mcp.resource(
    "planning://schemas/planning-session-route-output",
    mime_type="application/schema+json",
)
def planning_session_route_output_schema() -> str:
    """Schema for one-stage financial-planning route decisions."""
    return route_schema_as_json("output")


@mcp.resource(
    "planning://workflow-registry/v0.2.0",
    mime_type="application/json",
)
def planning_workflow_registry() -> str:
    """Versioned neutral-goal to installed-workflow mapping."""
    return workflow_registry_as_json()


@mcp.resource(
    "planning://schemas/workspace-state-version",
    mime_type="application/schema+json",
)
def workspace_state_version_schema() -> str:
    """Schema for one immutable confirmed Workspace-state version."""
    return workspace_schema_as_json("version")


@mcp.resource(
    "planning://schemas/workspace-state-read-output",
    mime_type="application/schema+json",
)
def workspace_state_read_output_schema() -> str:
    """Portable schema for Workspace repository inspection results."""
    return workspace_schema_as_json("read")


@mcp.resource(
    "planning://schemas/workspace-state-write-output",
    mime_type="application/schema+json",
)
def workspace_state_write_output_schema() -> str:
    """Portable schema for initialization and confirmed-write results."""
    return workspace_schema_as_json("write")


@mcp.prompt(title="Run financial planning")
def run_financial_planning(
    session_context: str = "",
    profile_context: str = "",
    goal_context: str = "",
    requested_capability: str = "auto",
    jurisdiction: str = "unspecified",
) -> str:
    """Create a coordinated one-stage planning prompt from a route result."""
    return render_financial_planning_session_prompt(
        session_context=session_context,
        profile_context=profile_context,
        goal_context=goal_context,
        requested_capability=requested_capability,
        jurisdiction=jurisdiction,
    )


@mcp.prompt(title="Manage financial planning Workspace")
def manage_financial_planning_workspace(
    workspace_context: str = "",
    operation_context: str = "",
) -> str:
    """Create a safe inspect, initialize, read, or confirmed-write prompt."""
    return render_workspace_state_prompt(
        workspace_context=workspace_context,
        operation_context=operation_context,
    )


@mcp.prompt(title="Collect financial profile")
def collect_financial_profile(
    profile_context: str = "",
    jurisdiction: str = "unspecified",
    collection_round: str = "initial",
) -> str:
    """Create a source-grounded progressive intake prompt from runtime context."""
    return render_financial_profile_intake_prompt(
        profile_context=profile_context,
        jurisdiction=jurisdiction,
        collection_round=collection_round,
    )


@mcp.prompt(title="Clarify financial goals")
def clarify_financial_goals(
    goal_context: str = "",
    profile_context: str = "",
    jurisdiction: str = "unspecified",
) -> str:
    """Create a source-grounded goal clarification and confirmation prompt."""
    return render_financial_goal_clarification_prompt(
        profile_context=profile_context,
        goal_context=goal_context,
        jurisdiction=jurisdiction,
    )


@mcp.prompt(title="Design target allocation")
def design_target_allocation(
    planning_context: str = "",
    jurisdiction: str = "unspecified",
) -> str:
    """Create a sourced allocation prompt from runtime context and jurisdiction."""
    return render_target_allocation_prompt(
        planning_context=planning_context,
        jurisdiction=jurisdiction,
    )


@mcp.prompt(title="Design cash and liquidity policy")
def design_cash_liquidity_policy(
    planning_context: str = "",
    product_liquidity_context: str = "",
    jurisdiction: str = "unspecified",
) -> str:
    """Create a sourced policy prompt that separates cash from cash-like products."""
    return render_cash_liquidity_policy_prompt(
        planning_context=planning_context,
        product_liquidity_context=product_liquidity_context,
        jurisdiction=jurisdiction,
    )


@mcp.tool(
    title="Validate financial profile",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def validate_financial_profile(
    payload_json: Annotated[
        str,
        Field(description="Proposed or confirmed financial-profile JSON object."),
    ],
    target_state: Annotated[
        str,
        Field(description="Validation gate: proposed or confirmed."),
    ] = "proposed",
) -> str:
    """Validate a profile proposal or confirmation without storing it."""
    result = validate_financial_profile_payload(payload_json, target_state)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(
    title="Validate financial goals",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def validate_financial_goals(
    payload_json: Annotated[
        str,
        Field(description="Proposed or confirmed financial-goals JSON object."),
    ],
    target_state: Annotated[
        str,
        Field(description="Validation gate: proposed or confirmed."),
    ] = "proposed",
) -> str:
    """Validate goal records and conflicts without resolving or storing them."""
    result = validate_financial_goals_payload(payload_json, target_state)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(title="Validate target allocation")
def validate_target_allocation(
    payload_json: Annotated[
        str,
        Field(description="Proposed or confirmed target-allocation JSON object."),
    ],
    target_state: Annotated[
        Literal["proposed", "confirmed"],
        Field(description="Validation gate: proposed or confirmed."),
    ] = "proposed",
) -> str:
    """Validate allocation structure, percentages, references, and confirmation."""
    result = validate_target_allocation_payload(payload_json, target_state)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(
    title="Route financial planning stage",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def route_financial_planning_stage(
    requested_capability: Annotated[
        str,
        Field(
            description=(
                "auto, a reserved coordinator capability, or a capability slug in "
                "planning://workflow-registry/v0.2.0."
            )
        ),
    ] = "auto",
    profile_state: Annotated[
        Literal["absent", "proposed", "confirmed"],
        Field(description="Profile state: absent, proposed, or confirmed."),
    ] = "absent",
    goals_state: Annotated[
        Literal["absent", "proposed", "confirmed"],
        Field(description="Goals state: absent, proposed, or confirmed."),
    ] = "absent",
    profile_has_blocking_conflicts: Annotated[
        bool, Field(description="Whether profile conflicts block downstream planning.")
    ] = False,
    goals_have_unresolved_conflicts: Annotated[
        bool, Field(description="Whether goal conflicts remain unresolved.")
    ] = False,
    change_scope: Annotated[
        Literal["none", "profile", "goals"],
        Field(description="Explicit changed record: none, profile, or goals."),
    ] = "none",
    goal_summaries: Annotated[
        list[dict[str, Any]] | None,
        Field(
            description=(
                "Confirmed financial_goals v0.2 routing summaries; use the exact "
                "planning-session route input Schema."
            )
        ),
    ] = None,
    workflow_progress: Annotated[
        list[dict[str, Any]] | None,
        Field(
            description=(
                "Optional non-authoritative goal-scoped workflow progress; only "
                "completed entries skip an exact candidate."
            )
        ),
    ] = None,
) -> str:
    """Select one next planning stage without persistence or transactions."""
    result = route_planning_session(
        requested_capability=requested_capability,
        profile_state=profile_state,
        goals_state=goals_state,
        profile_has_blocking_conflicts=profile_has_blocking_conflicts,
        goals_have_unresolved_conflicts=goals_have_unresolved_conflicts,
        change_scope=change_scope,
        goal_summaries=goal_summaries,
        workflow_progress=workflow_progress,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(title="Initialize financial planning Workspace")
def initialize_financial_planning_workspace(
    workspace_path: Annotated[
        str,
        Field(
            description="Explicit absolute path to an existing user-selected Workspace."
        ),
    ],
    explicit_user_confirmation: Annotated[
        bool,
        Field(description="True only after the user confirms this initialization."),
    ] = False,
) -> str:
    """Create the sole local SQLite state authority after explicit confirmation."""
    result = initialize_planning_workspace(
        workspace_path=workspace_path,
        explicit_user_confirmation=explicit_user_confirmation,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(title="Read financial planning Workspace")
def read_financial_planning_workspace(
    workspace_path: Annotated[
        str,
        Field(
            description="Explicit absolute path to an existing user-selected Workspace."
        ),
    ],
    history_limit: Annotated[
        int,
        Field(
            description="Number of newest immutable versions to return, from 0 to 100."
        ),
    ] = 20,
) -> str:
    """Read current confirmed records and immutable history without writing."""
    result = read_planning_workspace(
        workspace_path=workspace_path,
        history_limit=history_limit,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(title="Persist confirmed financial state")
def persist_confirmed_financial_state(
    workspace_path: Annotated[
        str,
        Field(description="Explicit absolute path to an initialized Workspace."),
    ],
    record_type: Annotated[
        Literal["profile", "goals", "allocation"],
        Field(description="Confirmed record stream: profile, goals, or allocation."),
    ],
    payload_json: Annotated[
        str,
        Field(
            description="Confirmed profile, goals, or target-allocation JSON that passes its validator."
        ),
    ],
    expected_parent_version_id: Annotated[
        str | None,
        Field(
            description="Exact current version read before confirmation, or null initially."
        ),
    ] = None,
    explicit_user_confirmation: Annotated[
        bool,
        Field(description="True only after the user confirms this exact named write."),
    ] = False,
) -> str:
    """Append an immutable confirmed version with optimistic concurrency."""
    result = persist_confirmed_state(
        workspace_path=workspace_path,
        record_type=record_type,
        payload_json=payload_json,
        expected_parent_version_id=expected_parent_version_id,
        explicit_user_confirmation=explicit_user_confirmation,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(title="Calculate financial independence")
def calculate_financial_independence(
    birth_year: Annotated[int, Field(description="Calendar year of birth.")],
    base_year: Annotated[
        int, Field(description="Purchasing-power and calculation base year.")
    ],
    target_year: Annotated[int, Field(description="Target calendar year.")],
    annual_spending_scenarios_cny: Annotated[
        list[float],
        Field(description="Annual real-CNY spending scenarios; first is baseline."),
    ],
    current_investable_assets_cny: Annotated[
        float,
        Field(
            description="Current investable financial assets, excluding a primary home."
        ),
    ],
    withdrawal_rates_pct: Annotated[
        list[float],
        Field(description="Scenario withdrawal rates in percent, not guarantees."),
    ],
    real_return_rates_pct: Annotated[
        list[float], Field(description="Annual real-return scenarios in percent.")
    ],
    annual_after_tax_income_cny: Annotated[
        float | None, Field(description="Optional annual after-tax employment income.")
    ] = None,
    income_start_year: Annotated[
        int | None,
        Field(description="Optional first year in which the income is active."),
    ] = None,
    annual_stable_income_at_target_cny: Annotated[
        float,
        Field(
            description="Supportable pension or other stable income at target; default zero."
        ),
    ] = 0,
    one_time_goal_reserve_cny: Annotated[
        float,
        Field(description="Optional reserve funded in addition to the FI portfolio."),
    ] = 0,
    current_year_annual_rent_cny: Annotated[
        float | None,
        Field(
            description="Optional annual rent used only for spending reconciliation."
        ),
    ] = None,
    current_year_annual_non_housing_spending_cny: Annotated[
        float | None,
        Field(
            description="Optional annual non-housing spending used only for reconciliation."
        ),
    ] = None,
) -> str:
    """Calculate FI targets and real-value projection scenarios without recommendations."""
    result = calculate_fi(
        birth_year=birth_year,
        base_year=base_year,
        target_year=target_year,
        annual_spending_scenarios_cny=annual_spending_scenarios_cny,
        current_investable_assets_cny=current_investable_assets_cny,
        withdrawal_rates_pct=withdrawal_rates_pct,
        real_return_rates_pct=real_return_rates_pct,
        annual_after_tax_income_cny=annual_after_tax_income_cny,
        income_start_year=income_start_year,
        annual_stable_income_at_target_cny=annual_stable_income_at_target_cny,
        one_time_goal_reserve_cny=one_time_goal_reserve_cny,
        current_year_annual_rent_cny=current_year_annual_rent_cny,
        current_year_annual_non_housing_spending_cny=current_year_annual_non_housing_spending_cny,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(
    title="Calculate financial independence milestones",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def calculate_financial_independence_milestones(
    birth_year: Annotated[int, Field(description="Calendar year of birth.")],
    base_year: Annotated[
        int, Field(description="Purchasing-power and calculation base year.")
    ],
    target_year: Annotated[int, Field(description="Target calendar year.")],
    annual_spending_cny_in_base_year_purchasing_power: Annotated[
        float, Field(description="Annual spending expressed in base-year real CNY.")
    ],
    current_investable_assets_cny: Annotated[
        float,
        Field(
            description="Current investable financial assets; primary home excluded."
        ),
    ],
    withdrawal_rate_pct: Annotated[
        float,
        Field(description="Withdrawal-rate scenario in percent, not a guarantee."),
    ],
    real_return_rates_pct: Annotated[
        list[float], Field(description="Annual real-return scenarios in percent.")
    ],
    annual_after_tax_income_cny_in_base_year_purchasing_power: Annotated[
        float | None, Field(description="Optional annual after-tax income in real CNY.")
    ] = None,
    income_start_year_scenarios: Annotated[
        list[int] | None,
        Field(description="Optional first-income years to compare."),
    ] = None,
    cashflow_start_year: Annotated[
        int | None,
        Field(description="First full calendar year whose cashflow is modeled."),
    ] = None,
    annual_portfolio_draw_before_income_cny: Annotated[
        float,
        Field(
            description="Annual real-CNY spending funded from the portfolio before income starts."
        ),
    ] = 0,
    annual_stable_income_at_target_cny: Annotated[
        float,
        Field(description="Supportable annual pension or stable income at target."),
    ] = 0,
    one_time_goal_reserve_cny: Annotated[
        float,
        Field(description="Optional reserve funded in addition to the FI portfolio."),
    ] = 0,
    yellow_status_floor_pct: Annotated[
        float,
        Field(
            description="Lower percentage of the required path classified as yellow."
        ),
    ] = 90,
    actual_checkpoint_year: Annotated[
        int | None,
        Field(description="Optional year for an actual progress assessment."),
    ] = None,
    actual_investable_assets_cny: Annotated[
        float | None,
        Field(description="Optional actual investable assets at the checkpoint year."),
    ] = None,
) -> str:
    """Build annual forward, minimum-required, and actual-progress FI paths."""
    result = calculate_fi_milestones(
        birth_year=birth_year,
        base_year=base_year,
        target_year=target_year,
        annual_spending_cny_in_base_year_purchasing_power=(
            annual_spending_cny_in_base_year_purchasing_power
        ),
        current_investable_assets_cny=current_investable_assets_cny,
        withdrawal_rate_pct=withdrawal_rate_pct,
        real_return_rates_pct=real_return_rates_pct,
        annual_after_tax_income_cny_in_base_year_purchasing_power=(
            annual_after_tax_income_cny_in_base_year_purchasing_power
        ),
        income_start_year_scenarios=income_start_year_scenarios,
        cashflow_start_year=cashflow_start_year,
        annual_portfolio_draw_before_income_cny=(
            annual_portfolio_draw_before_income_cny
        ),
        annual_stable_income_at_target_cny=annual_stable_income_at_target_cny,
        one_time_goal_reserve_cny=one_time_goal_reserve_cny,
        yellow_status_floor_pct=yellow_status_floor_pct,
        actual_checkpoint_year=actual_checkpoint_year,
        actual_investable_assets_cny=actual_investable_assets_cny,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(title="Calculate home opportunity scenario")
def calculate_home_opportunity_scenario(
    base_year: Annotated[int, Field(description="Purchasing-power base year.")],
    target_year: Annotated[
        int, Field(description="Financial-independence target year.")
    ],
    purchase_year: Annotated[
        int, Field(description="Beginning-of-year purchase date.")
    ],
    current_investable_assets_cny: Annotated[
        float,
        Field(description="Current investable assets; primary-home value is excluded."),
    ],
    home_price_cny_in_base_year_purchasing_power: Annotated[
        float, Field(description="Home price expressed in base-year purchasing power.")
    ],
    down_payment_pct: Annotated[float, Field(description="Down payment percentage.")],
    mortgage_annual_rate_pct: Annotated[
        float, Field(description="Contractual nominal annual mortgage rate.")
    ],
    mortgage_term_years: Annotated[int, Field(description="Mortgage term in years.")],
    transaction_cost_pct: Annotated[
        float, Field(description="One-time transaction-cost percentage of home price.")
    ],
    renovation_and_furnishing_cny_in_base_year_purchasing_power: Annotated[
        float,
        Field(description="One-time renovation and furnishing budget in real CNY."),
    ],
    annual_ownership_cost_pct_of_home_price: Annotated[
        float,
        Field(
            description="Annual property, maintenance, and reserve cost as home-price percent."
        ),
    ],
    annual_non_housing_spending_cny_in_base_year_purchasing_power: Annotated[
        float, Field(description="Annual non-housing spending in real CNY.")
    ],
    annual_rent_cny_in_base_year_purchasing_power: Annotated[
        float, Field(description="Annual rent before purchase in real CNY.")
    ],
    annual_after_tax_income_cny_in_base_year_purchasing_power: Annotated[
        float, Field(description="Annual after-tax income in real CNY once active.")
    ],
    income_start_year: Annotated[
        int, Field(description="First year modeled income is active.")
    ],
    cashflow_start_year: Annotated[
        int,
        Field(
            description="First full year modeled for income and spending cash flows."
        ),
    ],
    annual_real_return_pct: Annotated[
        float, Field(description="Annual real portfolio-return scenario.")
    ],
    annual_inflation_pct: Annotated[
        float,
        Field(
            description="Annual inflation scenario used for nominal mortgage conversion."
        ),
    ],
    fi_withdrawal_rate_pct: Annotated[
        float, Field(description="FI withdrawal-rate scenario, not a guarantee.")
    ],
    minimum_emergency_fund_cny_in_base_year_purchasing_power: Annotated[
        float,
        Field(description="Minimum emergency fund that must survive the purchase."),
    ],
    provident_fund_loan_cny_at_purchase: Annotated[
        float,
        Field(
            description="User-specific eligible provident-fund tranche; zero unless verified."
        ),
    ] = 0,
    provident_fund_annual_rate_pct: Annotated[
        float,
        Field(description="Provident-fund annual rate for the verified tranche."),
    ] = 2.6,
    mortgage_reserve_mode: Annotated[
        str,
        Field(description="payoff_principal or discounted_remaining_payments."),
    ] = "payoff_principal",
    mortgage_reserve_annual_real_return_pct: Annotated[
        float | None,
        Field(
            description="Real return for a continuing-mortgage reserve; defaults to portfolio scenario."
        ),
    ] = None,
) -> str:
    """Calculate the effect of a home purchase on investable assets and FI."""
    result = calculate_home_opportunity(
        base_year=base_year,
        target_year=target_year,
        purchase_year=purchase_year,
        current_investable_assets_cny=current_investable_assets_cny,
        home_price_cny_in_base_year_purchasing_power=home_price_cny_in_base_year_purchasing_power,
        down_payment_pct=down_payment_pct,
        mortgage_annual_rate_pct=mortgage_annual_rate_pct,
        mortgage_term_years=mortgage_term_years,
        transaction_cost_pct=transaction_cost_pct,
        renovation_and_furnishing_cny_in_base_year_purchasing_power=renovation_and_furnishing_cny_in_base_year_purchasing_power,
        annual_ownership_cost_pct_of_home_price=annual_ownership_cost_pct_of_home_price,
        annual_non_housing_spending_cny_in_base_year_purchasing_power=annual_non_housing_spending_cny_in_base_year_purchasing_power,
        annual_rent_cny_in_base_year_purchasing_power=annual_rent_cny_in_base_year_purchasing_power,
        annual_after_tax_income_cny_in_base_year_purchasing_power=annual_after_tax_income_cny_in_base_year_purchasing_power,
        income_start_year=income_start_year,
        cashflow_start_year=cashflow_start_year,
        annual_real_return_pct=annual_real_return_pct,
        annual_inflation_pct=annual_inflation_pct,
        fi_withdrawal_rate_pct=fi_withdrawal_rate_pct,
        minimum_emergency_fund_cny_in_base_year_purchasing_power=minimum_emergency_fund_cny_in_base_year_purchasing_power,
        provident_fund_loan_cny_at_purchase=provident_fund_loan_cny_at_purchase,
        provident_fund_annual_rate_pct=provident_fund_annual_rate_pct,
        mortgage_reserve_mode=mortgage_reserve_mode,
        mortgage_reserve_annual_real_return_pct=mortgage_reserve_annual_real_return_pct,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(
    title="Calculate home opportunity boundaries",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def calculate_home_opportunity_boundary_scenarios(
    base_year: Annotated[int, Field(description="Purchasing-power base year.")],
    purchase_years: Annotated[
        list[int], Field(description="Candidate beginning-of-year purchase dates.")
    ],
    fi_target_years: Annotated[
        list[int], Field(description="Candidate financial-independence target years.")
    ],
    monthly_housing_cost_caps_cny_in_base_year_purchasing_power: Annotated[
        list[float],
        Field(description="Monthly real housing-cost cap aligned to each FI year."),
    ],
    down_payment_pcts: Annotated[
        list[float], Field(description="Down-payment percentages to compare.")
    ],
    current_investable_assets_cny: Annotated[
        float, Field(description="Current investable assets; primary home excluded.")
    ],
    commercial_mortgage_annual_rate_pct: Annotated[
        float, Field(description="Commercial-tranche nominal annual rate.")
    ],
    mortgage_term_years: Annotated[int, Field(description="Mortgage term in years.")],
    transaction_cost_pct: Annotated[
        float, Field(description="One-time transaction costs as home-price percent.")
    ],
    renovation_and_furnishing_cny_in_base_year_purchasing_power: Annotated[
        float,
        Field(description="One-time renovation and furnishing budget in real CNY."),
    ],
    annual_ownership_cost_pct_of_home_price: Annotated[
        float, Field(description="Annual ownership costs as home-price percent.")
    ],
    annual_non_housing_spending_cny_in_base_year_purchasing_power: Annotated[
        float, Field(description="Annual real non-housing spending.")
    ],
    annual_rent_cny_in_base_year_purchasing_power: Annotated[
        float, Field(description="Annual real rent before purchase.")
    ],
    annual_after_tax_income_cny_in_base_year_purchasing_power: Annotated[
        float, Field(description="Annual real after-tax income once active.")
    ],
    income_start_year: Annotated[
        int, Field(description="First year income is active.")
    ],
    cashflow_start_year: Annotated[
        int, Field(description="First full year of modeled cash flows.")
    ],
    annual_real_return_pct: Annotated[
        float, Field(description="Annual real portfolio-return scenario.")
    ],
    annual_inflation_pct: Annotated[
        float, Field(description="Annual inflation scenario.")
    ],
    fi_withdrawal_rate_pct: Annotated[
        float, Field(description="FI withdrawal-rate scenario.")
    ],
    minimum_emergency_fund_cny_in_base_year_purchasing_power: Annotated[
        float, Field(description="Emergency floor maintained throughout the path.")
    ],
    provident_fund_loan_cap_cny_at_purchase: Annotated[
        float, Field(description="Conditional provident-fund tranche cap.")
    ] = 0,
    provident_fund_annual_rate_pct: Annotated[
        float, Field(description="Conditional provident-fund nominal annual rate.")
    ] = 2.6,
    mortgage_reserve_mode: Annotated[
        str,
        Field(description="payoff_principal or discounted_remaining_payments."),
    ] = "payoff_principal",
    mortgage_reserve_annual_real_return_pct: Annotated[
        float | None,
        Field(description="Real return used to fund continuing mortgage payments."),
    ] = None,
    price_search_upper_bound_cny_in_base_year_purchasing_power: Annotated[
        float, Field(description="Maximum real price searched by the solver.")
    ] = 10000000,
    price_rounding_increment_cny: Annotated[
        int, Field(description="Price ceiling rounding and next-constraint increment.")
    ] = 10000,
) -> str:
    """Find price ceilings and down-payment choices under explicit constraints."""
    result = calculate_home_opportunity_boundaries(
        base_year=base_year,
        purchase_years=purchase_years,
        fi_target_years=fi_target_years,
        monthly_housing_cost_caps_cny_in_base_year_purchasing_power=(
            monthly_housing_cost_caps_cny_in_base_year_purchasing_power
        ),
        down_payment_pcts=down_payment_pcts,
        current_investable_assets_cny=current_investable_assets_cny,
        commercial_mortgage_annual_rate_pct=(commercial_mortgage_annual_rate_pct),
        mortgage_term_years=mortgage_term_years,
        transaction_cost_pct=transaction_cost_pct,
        renovation_and_furnishing_cny_in_base_year_purchasing_power=(
            renovation_and_furnishing_cny_in_base_year_purchasing_power
        ),
        annual_ownership_cost_pct_of_home_price=(
            annual_ownership_cost_pct_of_home_price
        ),
        annual_non_housing_spending_cny_in_base_year_purchasing_power=(
            annual_non_housing_spending_cny_in_base_year_purchasing_power
        ),
        annual_rent_cny_in_base_year_purchasing_power=(
            annual_rent_cny_in_base_year_purchasing_power
        ),
        annual_after_tax_income_cny_in_base_year_purchasing_power=(
            annual_after_tax_income_cny_in_base_year_purchasing_power
        ),
        income_start_year=income_start_year,
        cashflow_start_year=cashflow_start_year,
        annual_real_return_pct=annual_real_return_pct,
        annual_inflation_pct=annual_inflation_pct,
        fi_withdrawal_rate_pct=fi_withdrawal_rate_pct,
        minimum_emergency_fund_cny_in_base_year_purchasing_power=(
            minimum_emergency_fund_cny_in_base_year_purchasing_power
        ),
        provident_fund_loan_cap_cny_at_purchase=(
            provident_fund_loan_cap_cny_at_purchase
        ),
        provident_fund_annual_rate_pct=provident_fund_annual_rate_pct,
        mortgage_reserve_mode=mortgage_reserve_mode,
        mortgage_reserve_annual_real_return_pct=(
            mortgage_reserve_annual_real_return_pct
        ),
        price_search_upper_bound_cny_in_base_year_purchasing_power=(
            price_search_upper_bound_cny_in_base_year_purchasing_power
        ),
        price_rounding_increment_cny=price_rounding_increment_cny,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
