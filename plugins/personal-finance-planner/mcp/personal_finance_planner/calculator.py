"""Deterministic, real-value financial-independence calculations."""

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


def _project_balance(
    *,
    current_assets: Decimal,
    real_return_pct: Decimal,
    base_year: int,
    target_year: int,
    annual_contribution: Decimal,
    contribution_start_year: int | None,
) -> Decimal:
    balance = current_assets
    annual_rate = real_return_pct / Decimal("100")
    for year in range(base_year, target_year):
        balance *= Decimal("1") + annual_rate
        if contribution_start_year is not None and year >= contribution_start_year:
            balance += annual_contribution
    return balance


def calculate_fi(
    *,
    birth_year: int,
    base_year: int,
    target_year: int,
    annual_spending_scenarios_cny: list[int | float | str],
    current_investable_assets_cny: int | float | str,
    withdrawal_rates_pct: list[int | float | str],
    real_return_rates_pct: list[int | float | str],
    annual_after_tax_income_cny: int | float | str | None = None,
    income_start_year: int | None = None,
    annual_stable_income_at_target_cny: int | float | str = 0,
    one_time_goal_reserve_cny: int | float | str = 0,
    current_year_annual_rent_cny: int | float | str | None = None,
    current_year_annual_non_housing_spending_cny: int | float | str | None = None,
) -> dict[str, Any]:
    """Return an auditable FI target and projection sensitivity matrix."""
    if target_year <= base_year:
        raise ValueError("target_year must be greater than base_year")
    if birth_year > base_year:
        raise ValueError("birth_year must not be after base_year")
    if not annual_spending_scenarios_cny:
        raise ValueError("annual_spending_scenarios_cny must not be empty")
    if not withdrawal_rates_pct:
        raise ValueError("withdrawal_rates_pct must not be empty")
    if not real_return_rates_pct:
        raise ValueError("real_return_rates_pct must not be empty")
    if income_start_year is not None and not base_year <= income_start_year < target_year:
        raise ValueError("income_start_year must be within [base_year, target_year)")

    spending_values = [_decimal(value) for value in annual_spending_scenarios_cny]
    withdrawal_rates = [_decimal(value) for value in withdrawal_rates_pct]
    real_returns = [_decimal(value) for value in real_return_rates_pct]
    current_assets = _decimal(current_investable_assets_cny)
    stable_income = _decimal(annual_stable_income_at_target_cny)
    reserve = _decimal(one_time_goal_reserve_cny)
    income = (
        _decimal(annual_after_tax_income_cny)
        if annual_after_tax_income_cny is not None
        else None
    )

    if any(value < 0 for value in spending_values):
        raise ValueError("annual spending must be non-negative")
    if any(value <= 0 or value >= 100 for value in withdrawal_rates):
        raise ValueError("withdrawal rates must be greater than 0 and less than 100")
    if any(value <= Decimal("-100") for value in real_returns):
        raise ValueError("real return rates must be greater than -100")
    if current_assets < 0 or stable_income < 0 or reserve < 0:
        raise ValueError("asset, stable-income, and reserve inputs must be non-negative")
    if income is not None and income < 0:
        raise ValueError("annual_after_tax_income_cny must be non-negative")

    warnings: list[str] = []
    component_total: Decimal | None = None
    if (
        current_year_annual_rent_cny is not None
        and current_year_annual_non_housing_spending_cny is not None
    ):
        component_total = _decimal(current_year_annual_rent_cny) + _decimal(
            current_year_annual_non_housing_spending_cny
        )
        if component_total != spending_values[0]:
            warnings.append(
                "The rent and non-housing components do not equal the first annual spending scenario."
            )

    if income is not None and income_start_year is None:
        warnings.append(
            "After-tax income was supplied without an income_start_year; future contributions are excluded from projections."
        )
    if income is None and income_start_year is not None:
        warnings.append(
            "income_start_year was supplied without after-tax income; future contributions are excluded from projections."
        )
    if reserve == 0:
        warnings.append(
            "No one-time goal reserve is included; model an optional home purchase as a separate scenario."
        )
    if stable_income == 0:
        warnings.append(
            "No pension or other stable income is credited at the target; add it only after a supportable estimate exists."
        )

    target_rows: list[dict[str, Any]] = []
    projection_rows: list[dict[str, Any]] = []
    for spending in spending_values:
        required_portfolio_income = max(spending - stable_income, Decimal("0"))
        annual_surplus = (
            max(income - spending, Decimal("0")) if income is not None else Decimal("0")
        )

        for withdrawal_rate in withdrawal_rates:
            capital_target = (
                required_portfolio_income / (withdrawal_rate / Decimal("100"))
            ) + reserve
            target_rows.append(
                {
                    "annual_spending_cny": _money(spending),
                    "withdrawal_rate_pct": _rate(withdrawal_rate),
                    "stable_income_at_target_cny": _money(stable_income),
                    "one_time_goal_reserve_cny": _money(reserve),
                    "capital_target_cny": _money(capital_target),
                    "current_gap_cny": _money(max(capital_target - current_assets, Decimal("0"))),
                    "current_surplus_cny": _money(max(current_assets - capital_target, Decimal("0"))),
                }
            )

        contribution_start = income_start_year if income is not None else None
        contribution = annual_surplus if contribution_start is not None else Decimal("0")
        for real_return in real_returns:
            projected = _project_balance(
                current_assets=current_assets,
                real_return_pct=real_return,
                base_year=base_year,
                target_year=target_year,
                annual_contribution=contribution,
                contribution_start_year=contribution_start,
            )
            projection_rows.append(
                {
                    "annual_spending_cny": _money(spending),
                    "real_return_rate_pct": _rate(real_return),
                    "annual_surplus_if_income_active_cny": _money(annual_surplus),
                    "income_start_year": contribution_start,
                    "contribution_years": (
                        target_year - contribution_start
                        if contribution_start is not None
                        else 0
                    ),
                    "projected_investable_assets_cny": _money(projected),
                }
            )

    return {
        "calculation_version": "0.1.0",
        "currency": "CNY",
        "value_basis": f"real_{base_year}_purchasing_power",
        "base_year": base_year,
        "target_year": target_year,
        "years_to_target": target_year - base_year,
        "target_age_range": [target_year - birth_year - 1, target_year - birth_year],
        "current_investable_assets_cny": _money(current_assets),
        "spending_reconciliation": {
            "first_scenario_cny": _money(spending_values[0]),
            "component_total_cny": (
                _money(component_total) if component_total is not None else None
            ),
            "components_match": (
                component_total == spending_values[0]
                if component_total is not None
                else None
            ),
        },
        "capital_targets": target_rows,
        "projections": projection_rows,
        "warnings": warnings,
        "formula_notes": [
            "capital target = max(spending - stable income, 0) / withdrawal rate + one-time reserve",
            "projection compounds current assets annually in real terms and adds any modeled surplus at each year-end",
            "withdrawal rates and real returns are scenarios, not guarantees",
        ],
        "provenance_card_ids": [
            "bengen-1994",
            "morningstar-2025",
            "vanguard-retirement-income",
        ],
    }
