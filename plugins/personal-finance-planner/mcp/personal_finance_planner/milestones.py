"""Deterministic annual milestones for a financial-independence plan."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any


MONEY_QUANTUM = Decimal("0.01")
RATE_QUANTUM = Decimal("0.0001")


def _decimal(value: int | float | str) -> Decimal:
    return Decimal(str(value))


def _money(value: Decimal) -> float:
    return float(value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP))


def _rate(value: Decimal) -> float:
    return float(value.quantize(RATE_QUANTUM, rounding=ROUND_HALF_UP))


def _age_range(year: int, birth_year: int) -> list[int]:
    return [year - birth_year - 1, year - birth_year]


def _status(
    *,
    assets: Decimal,
    required_assets: Decimal,
    yellow_floor_pct: Decimal,
) -> tuple[str, Decimal | None]:
    if required_assets <= 0:
        return "green", None
    ratio_pct = assets / required_assets * Decimal("100")
    if ratio_pct >= Decimal("100"):
        return "green", ratio_pct
    if ratio_pct >= yellow_floor_pct:
        return "yellow", ratio_pct
    return "red", ratio_pct


def _calendar_year_cashflow(
    *,
    calendar_year: int,
    cashflow_start_year: int,
    income_start_year: int | None,
    annual_net_contribution_if_income_active: Decimal,
    annual_portfolio_draw_before_income: Decimal,
) -> Decimal:
    if calendar_year < cashflow_start_year:
        return Decimal("0")
    if income_start_year is not None and calendar_year >= income_start_year:
        return annual_net_contribution_if_income_active
    return -annual_portfolio_draw_before_income


def _future_cashflow_value(
    *,
    checkpoint_year: int,
    target_year: int,
    annual_rate: Decimal,
    cashflow_start_year: int,
    income_start_year: int | None,
    annual_net_contribution_if_income_active: Decimal,
    annual_portfolio_draw_before_income: Decimal,
) -> Decimal:
    future_value = Decimal("0")
    for calendar_year in range(checkpoint_year, target_year):
        cashflow = _calendar_year_cashflow(
            calendar_year=calendar_year,
            cashflow_start_year=cashflow_start_year,
            income_start_year=income_start_year,
            annual_net_contribution_if_income_active=(
                annual_net_contribution_if_income_active
            ),
            annual_portfolio_draw_before_income=annual_portfolio_draw_before_income,
        )
        growth_periods = target_year - calendar_year - 1
        future_value += cashflow * ((Decimal("1") + annual_rate) ** growth_periods)
    return future_value


def _required_on_track_assets(
    *,
    checkpoint_year: int,
    target_year: int,
    capital_target: Decimal,
    annual_rate: Decimal,
    cashflow_start_year: int,
    income_start_year: int | None,
    annual_net_contribution_if_income_active: Decimal,
    annual_portfolio_draw_before_income: Decimal,
) -> Decimal:
    future_cashflows = _future_cashflow_value(
        checkpoint_year=checkpoint_year,
        target_year=target_year,
        annual_rate=annual_rate,
        cashflow_start_year=cashflow_start_year,
        income_start_year=income_start_year,
        annual_net_contribution_if_income_active=(
            annual_net_contribution_if_income_active
        ),
        annual_portfolio_draw_before_income=annual_portfolio_draw_before_income,
    )
    growth_periods = target_year - checkpoint_year
    discounted_need = (capital_target - future_cashflows) / (
        (Decimal("1") + annual_rate) ** growth_periods
    )
    return max(discounted_need, Decimal("0"))


def _required_constant_annual_contribution(
    *,
    checkpoint_assets: Decimal,
    checkpoint_year: int,
    target_year: int,
    capital_target: Decimal,
    annual_rate: Decimal,
    cashflow_start_year: int,
    income_start_year: int | None,
    annual_portfolio_draw_before_income: Decimal,
) -> Decimal | None:
    remaining_years = target_year - checkpoint_year
    if checkpoint_year == target_year:
        if checkpoint_assets >= capital_target:
            return Decimal("0")
        return None

    asset_future_value = checkpoint_assets * (
        (Decimal("1") + annual_rate) ** remaining_years
    )
    pre_income_future_value = Decimal("0")
    pre_income_end_year = (
        target_year if income_start_year is None else income_start_year
    )
    for calendar_year in range(
        max(checkpoint_year, cashflow_start_year),
        min(pre_income_end_year, target_year),
    ):
        growth_periods = target_year - calendar_year - 1
        pre_income_future_value -= annual_portfolio_draw_before_income * (
            (Decimal("1") + annual_rate) ** growth_periods
        )

    remaining_need = max(
        capital_target - asset_future_value - pre_income_future_value,
        Decimal("0"),
    )
    if income_start_year is None:
        return Decimal("0") if remaining_need == 0 else None

    contribution_years = range(
        max(checkpoint_year, cashflow_start_year, income_start_year),
        target_year,
    )
    contribution_factor = sum(
        (
            (Decimal("1") + annual_rate)
            ** (target_year - calendar_year - 1)
        )
        for calendar_year in contribution_years
    )
    if contribution_factor == 0:
        return Decimal("0") if remaining_need == 0 else None
    return remaining_need / contribution_factor


def calculate_fi_milestones(
    *,
    birth_year: int,
    base_year: int,
    target_year: int,
    annual_spending_cny_in_base_year_purchasing_power: int | float | str,
    current_investable_assets_cny: int | float | str,
    withdrawal_rate_pct: int | float | str,
    real_return_rates_pct: list[int | float | str],
    annual_after_tax_income_cny_in_base_year_purchasing_power: (
        int | float | str | None
    ) = None,
    income_start_year_scenarios: list[int] | None = None,
    cashflow_start_year: int | None = None,
    annual_portfolio_draw_before_income_cny: int | float | str = 0,
    annual_stable_income_at_target_cny: int | float | str = 0,
    one_time_goal_reserve_cny: int | float | str = 0,
    yellow_status_floor_pct: int | float | str = 90,
    actual_checkpoint_year: int | None = None,
    actual_investable_assets_cny: int | float | str | None = None,
) -> dict[str, Any]:
    """Build annual forward and minimum-required paths for FI scenarios."""
    if target_year <= base_year:
        raise ValueError("target_year must be greater than base_year")
    if birth_year > base_year:
        raise ValueError("birth_year must not be after base_year")
    if not real_return_rates_pct:
        raise ValueError("real_return_rates_pct must not be empty")

    spending = _decimal(annual_spending_cny_in_base_year_purchasing_power)
    current_assets = _decimal(current_investable_assets_cny)
    withdrawal_rate = _decimal(withdrawal_rate_pct)
    real_returns = [_decimal(value) for value in real_return_rates_pct]
    stable_income = _decimal(annual_stable_income_at_target_cny)
    reserve = _decimal(one_time_goal_reserve_cny)
    pre_income_draw = _decimal(annual_portfolio_draw_before_income_cny)
    yellow_floor = _decimal(yellow_status_floor_pct)
    income = (
        _decimal(annual_after_tax_income_cny_in_base_year_purchasing_power)
        if annual_after_tax_income_cny_in_base_year_purchasing_power is not None
        else None
    )

    if spending < 0 or current_assets < 0 or stable_income < 0 or reserve < 0:
        raise ValueError("spending, assets, stable income, and reserve must be non-negative")
    if pre_income_draw < 0:
        raise ValueError("annual_portfolio_draw_before_income_cny must be non-negative")
    if not Decimal("0") < withdrawal_rate < Decimal("100"):
        raise ValueError("withdrawal_rate_pct must be greater than 0 and less than 100")
    if any(value <= Decimal("-100") for value in real_returns):
        raise ValueError("real return rates must be greater than -100")
    if income is not None and income < 0:
        raise ValueError("annual after-tax income must be non-negative")
    if not Decimal("0") <= yellow_floor < Decimal("100"):
        raise ValueError("yellow_status_floor_pct must be within [0, 100)")

    effective_cashflow_start = (
        base_year if cashflow_start_year is None else cashflow_start_year
    )
    if not base_year <= effective_cashflow_start < target_year:
        raise ValueError("cashflow_start_year must be within [base_year, target_year)")

    if (actual_checkpoint_year is None) != (actual_investable_assets_cny is None):
        raise ValueError(
            "actual_checkpoint_year and actual_investable_assets_cny must be supplied together"
        )
    actual_assets = (
        _decimal(actual_investable_assets_cny)
        if actual_investable_assets_cny is not None
        else None
    )
    if actual_checkpoint_year is not None and not (
        base_year <= actual_checkpoint_year <= target_year
    ):
        raise ValueError("actual_checkpoint_year must be within [base_year, target_year]")
    if actual_assets is not None and actual_assets < 0:
        raise ValueError("actual_investable_assets_cny must be non-negative")

    warnings: list[str] = []
    if income is None:
        normalized_income_starts: list[int | None] = [None]
        if income_start_year_scenarios:
            warnings.append(
                "Income start scenarios were supplied without after-tax income; no employment contribution is modeled."
            )
    elif not income_start_year_scenarios:
        normalized_income_starts = [None]
        warnings.append(
            "After-tax income was supplied without income-start scenarios; no employment contribution is modeled."
        )
    else:
        if len(set(income_start_year_scenarios)) != len(income_start_year_scenarios):
            raise ValueError("income_start_year_scenarios must not contain duplicates")
        if any(
            not base_year <= year < target_year
            for year in income_start_year_scenarios
        ):
            raise ValueError(
                "income start years must be within [base_year, target_year)"
            )
        normalized_income_starts = list(income_start_year_scenarios)

    if len(set(real_returns)) != len(real_returns):
        raise ValueError("real_return_rates_pct must not contain duplicates")
    if pre_income_draw == 0:
        warnings.append(
            "No portfolio-funded spending draw is modeled before income starts; set it explicitly when a full no-income year should reduce assets."
        )
    if stable_income == 0:
        warnings.append(
            "No pension or other stable income is credited at the target."
        )

    required_portfolio_income = max(spending - stable_income, Decimal("0"))
    capital_target = (
        required_portfolio_income / (withdrawal_rate / Decimal("100"))
    ) + reserve
    annual_net_contribution = (
        income - spending if income is not None else Decimal("0")
    )

    scenarios: list[dict[str, Any]] = []
    scenario_number = 0
    for income_start_year in normalized_income_starts:
        for real_return in real_returns:
            scenario_number += 1
            annual_rate = real_return / Decimal("100")
            balance = current_assets
            projected_by_year: dict[int, Decimal] = {base_year: balance}
            income_active_years = 0
            portfolio_draw_years = 0

            for calendar_year in range(base_year, target_year):
                balance *= Decimal("1") + annual_rate
                cashflow = _calendar_year_cashflow(
                    calendar_year=calendar_year,
                    cashflow_start_year=effective_cashflow_start,
                    income_start_year=income_start_year,
                    annual_net_contribution_if_income_active=annual_net_contribution,
                    annual_portfolio_draw_before_income=pre_income_draw,
                )
                balance += cashflow
                if (
                    calendar_year >= effective_cashflow_start
                    and income_start_year is not None
                    and calendar_year >= income_start_year
                ):
                    income_active_years += 1
                elif calendar_year >= effective_cashflow_start and pre_income_draw > 0:
                    portfolio_draw_years += 1
                projected_by_year[calendar_year + 1] = balance

            milestones: list[dict[str, Any]] = []
            for checkpoint_year in range(base_year, target_year + 1):
                projected_assets = projected_by_year[checkpoint_year]
                required_assets = _required_on_track_assets(
                    checkpoint_year=checkpoint_year,
                    target_year=target_year,
                    capital_target=capital_target,
                    annual_rate=annual_rate,
                    cashflow_start_year=effective_cashflow_start,
                    income_start_year=income_start_year,
                    annual_net_contribution_if_income_active=annual_net_contribution,
                    annual_portfolio_draw_before_income=pre_income_draw,
                )
                projected_status, projected_ratio = _status(
                    assets=projected_assets,
                    required_assets=required_assets,
                    yellow_floor_pct=yellow_floor,
                )
                capital_only_threshold = capital_target / (
                    (Decimal("1") + annual_rate)
                    ** (target_year - checkpoint_year)
                )
                minimum_contribution = _required_constant_annual_contribution(
                    checkpoint_assets=projected_assets,
                    checkpoint_year=checkpoint_year,
                    target_year=target_year,
                    capital_target=capital_target,
                    annual_rate=annual_rate,
                    cashflow_start_year=effective_cashflow_start,
                    income_start_year=income_start_year,
                    annual_portfolio_draw_before_income=pre_income_draw,
                )
                milestones.append(
                    {
                        "year": checkpoint_year,
                        "age_range": _age_range(checkpoint_year, birth_year),
                        "projected_investable_assets_cny": _money(projected_assets),
                        "required_on_track_assets_cny": _money(required_assets),
                        "yellow_status_floor_assets_cny": _money(
                            required_assets * yellow_floor / Decimal("100")
                        ),
                        "projected_status": projected_status,
                        "projected_assets_as_pct_of_required": (
                            _rate(projected_ratio)
                            if projected_ratio is not None
                            else None
                        ),
                        "capital_only_threshold_cny": _money(capital_only_threshold),
                        "projected_capital_only_progress_pct": (
                            _rate(
                                projected_assets
                                / capital_only_threshold
                                * Decimal("100")
                            )
                            if capital_only_threshold > 0
                            else None
                        ),
                        "required_constant_annual_net_contribution_after_income_start_from_checkpoint_cny": (
                            _money(minimum_contribution)
                            if minimum_contribution is not None
                            else None
                        ),
                    }
                )

            actual_assessment: dict[str, Any] | None = None
            if actual_checkpoint_year is not None and actual_assets is not None:
                required_assets = _required_on_track_assets(
                    checkpoint_year=actual_checkpoint_year,
                    target_year=target_year,
                    capital_target=capital_target,
                    annual_rate=annual_rate,
                    cashflow_start_year=effective_cashflow_start,
                    income_start_year=income_start_year,
                    annual_net_contribution_if_income_active=annual_net_contribution,
                    annual_portfolio_draw_before_income=pre_income_draw,
                )
                actual_status, actual_ratio = _status(
                    assets=actual_assets,
                    required_assets=required_assets,
                    yellow_floor_pct=yellow_floor,
                )
                required_contribution = _required_constant_annual_contribution(
                    checkpoint_assets=actual_assets,
                    checkpoint_year=actual_checkpoint_year,
                    target_year=target_year,
                    capital_target=capital_target,
                    annual_rate=annual_rate,
                    cashflow_start_year=effective_cashflow_start,
                    income_start_year=income_start_year,
                    annual_portfolio_draw_before_income=pre_income_draw,
                )
                actual_assessment = {
                    "year": actual_checkpoint_year,
                    "actual_investable_assets_cny": _money(actual_assets),
                    "required_on_track_assets_cny": _money(required_assets),
                    "gap_to_required_path_cny": _money(
                        max(required_assets - actual_assets, Decimal("0"))
                    ),
                    "surplus_to_required_path_cny": _money(
                        max(actual_assets - required_assets, Decimal("0"))
                    ),
                    "status": actual_status,
                    "actual_assets_as_pct_of_required": (
                        _rate(actual_ratio) if actual_ratio is not None else None
                    ),
                    "required_constant_annual_net_contribution_after_income_start_from_actual_cny": (
                        _money(required_contribution)
                        if required_contribution is not None
                        else None
                    ),
                }

            projected_target = projected_by_year[target_year]
            target_status, target_ratio = _status(
                assets=projected_target,
                required_assets=capital_target,
                yellow_floor_pct=yellow_floor,
            )
            scenarios.append(
                {
                    "scenario_id": f"scenario_{scenario_number:02d}",
                    "real_return_rate_pct": _rate(real_return),
                    "income_start_year": income_start_year,
                    "cashflow_start_year": effective_cashflow_start,
                    "annual_net_contribution_if_income_active_cny": _money(
                        annual_net_contribution
                    ),
                    "annual_portfolio_draw_before_income_cny": _money(
                        pre_income_draw
                    ),
                    "income_active_years": income_active_years,
                    "portfolio_draw_years_before_income": portfolio_draw_years,
                    "projected_investable_assets_at_target_cny": _money(
                        projected_target
                    ),
                    "target_gap_cny": _money(
                        max(capital_target - projected_target, Decimal("0"))
                    ),
                    "target_surplus_cny": _money(
                        max(projected_target - capital_target, Decimal("0"))
                    ),
                    "target_status": target_status,
                    "projected_assets_as_pct_of_target": (
                        _rate(target_ratio) if target_ratio is not None else None
                    ),
                    "actual_checkpoint_assessment": actual_assessment,
                    "milestones": milestones,
                }
            )

    return {
        "calculation_version": "fi-milestones-0.1.0",
        "currency": "CNY",
        "value_basis": f"real_{base_year}_purchasing_power",
        "checkpoint_timing": (
            "base-year snapshot; each later checkpoint includes the prior calendar year's return and modeled year-end cashflow"
        ),
        "base_year": base_year,
        "target_year": target_year,
        "target_age_range": _age_range(target_year, birth_year),
        "current_investable_assets_cny": _money(current_assets),
        "annual_spending_cny": _money(spending),
        "withdrawal_rate_pct": _rate(withdrawal_rate),
        "annual_stable_income_at_target_cny": _money(stable_income),
        "one_time_goal_reserve_cny": _money(reserve),
        "capital_target_cny": _money(capital_target),
        "current_assets_as_pct_of_capital_target": (
            _rate(current_assets / capital_target * Decimal("100"))
            if capital_target > 0
            else None
        ),
        "status_thresholds": {
            "green": "assets are at least 100% of the scenario's required on-track path",
            "yellow": (
                f"assets are at least {_rate(yellow_floor)}% but less than 100% of the required path"
            ),
            "red": (
                f"assets are below {_rate(yellow_floor)}% of the required path"
            ),
            "yellow_status_floor_pct": _rate(yellow_floor),
        },
        "scenarios": scenarios,
        "warnings": warnings
        + [
            "Green means on track only if the scenario's future income, cashflow, and real-return assumptions hold; it does not mean financial independence has already been reached.",
            "Withdrawal rates and real returns are planning scenarios, not guarantees.",
        ],
        "formula_notes": [
            "capital target = max(spending - stable income, 0) / withdrawal rate + one-time reserve",
            "each annual checkpoint compounds the prior balance and then applies that calendar year's modeled net cashflow",
            "required on-track assets discount the final target after crediting all remaining scenario cashflows",
            "capital-only threshold discounts the target without crediting future employment contributions",
        ],
        "provenance_card_ids": [
            "bengen-1994",
            "morningstar-2025",
            "vanguard-retirement-income",
        ],
    }
