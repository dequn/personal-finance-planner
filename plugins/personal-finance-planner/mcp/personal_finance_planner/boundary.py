"""Deterministic home-price ceilings under liquidity, housing-cost, and FI constraints."""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Any

from .home import calculate_home_opportunity


def calculate_home_opportunity_boundaries(
    *,
    base_year: int,
    purchase_years: list[int],
    fi_target_years: list[int],
    monthly_housing_cost_caps_cny_in_base_year_purchasing_power: list[float],
    down_payment_pcts: list[float],
    current_investable_assets_cny: float,
    commercial_mortgage_annual_rate_pct: float,
    mortgage_term_years: int,
    transaction_cost_pct: float,
    renovation_and_furnishing_cny_in_base_year_purchasing_power: float,
    annual_ownership_cost_pct_of_home_price: float,
    annual_non_housing_spending_cny_in_base_year_purchasing_power: float,
    annual_rent_cny_in_base_year_purchasing_power: float,
    annual_after_tax_income_cny_in_base_year_purchasing_power: float,
    income_start_year: int,
    cashflow_start_year: int,
    annual_real_return_pct: float,
    annual_inflation_pct: float,
    fi_withdrawal_rate_pct: float,
    minimum_emergency_fund_cny_in_base_year_purchasing_power: float,
    provident_fund_loan_cap_cny_at_purchase: float = 0,
    provident_fund_annual_rate_pct: float = 2.6,
    mortgage_reserve_mode: str = "payoff_principal",
    mortgage_reserve_annual_real_return_pct: float | None = None,
    price_search_upper_bound_cny_in_base_year_purchasing_power: float = 10000000,
    price_rounding_increment_cny: int = 10000,
) -> dict[str, Any]:
    """Find maximum real home prices that satisfy every supplied constraint."""
    if not purchase_years or not fi_target_years or not down_payment_pcts:
        raise ValueError("purchase years, FI target years, and down payments are required")
    if len(fi_target_years) != len(
        monthly_housing_cost_caps_cny_in_base_year_purchasing_power
    ):
        raise ValueError("each FI target year must have one monthly housing-cost cap")
    if any(year <= base_year for year in purchase_years):
        raise ValueError("purchase_years must be greater than base_year")
    latest_purchase = max(purchase_years)
    if any(target_year <= latest_purchase for target_year in fi_target_years):
        raise ValueError("every FI target year must be after every purchase year")
    if any(not 0 <= pct <= 100 for pct in down_payment_pcts):
        raise ValueError("down_payment_pcts must be within [0, 100]")
    if any(cap <= 0 for cap in monthly_housing_cost_caps_cny_in_base_year_purchasing_power):
        raise ValueError("monthly housing-cost caps must be positive")
    if price_search_upper_bound_cny_in_base_year_purchasing_power <= 0:
        raise ValueError("price search upper bound must be positive")
    if price_rounding_increment_cny <= 0:
        raise ValueError("price_rounding_increment_cny must be positive")
    if provident_fund_loan_cap_cny_at_purchase < 0:
        raise ValueError("provident_fund_loan_cap_cny_at_purchase must be non-negative")

    inflation = annual_inflation_pct / 100
    ownership_rate = annual_ownership_cost_pct_of_home_price / 100
    emergency_floor = minimum_emergency_fund_cny_in_base_year_purchasing_power

    def evaluate(
        *,
        price_real: float,
        purchase_year: int,
        target_year: int,
        down_payment_pct: float,
        monthly_cap_real: float,
    ) -> tuple[dict[str, Any], list[str], float]:
        purchase_factor_decimal = (Decimal("1") + Decimal(str(inflation))) ** (
            purchase_year - base_year
        )
        total_loan_nominal = (
            Decimal(str(price_real))
            * purchase_factor_decimal
            * (Decimal("1") - Decimal(str(down_payment_pct)) / Decimal("100"))
        )
        provident_loan = min(
            Decimal(str(provident_fund_loan_cap_cny_at_purchase)),
            max(total_loan_nominal, Decimal("0")),
        )
        result = calculate_home_opportunity(
            base_year=base_year,
            target_year=target_year,
            purchase_year=purchase_year,
            current_investable_assets_cny=current_investable_assets_cny,
            home_price_cny_in_base_year_purchasing_power=price_real,
            down_payment_pct=down_payment_pct,
            mortgage_annual_rate_pct=commercial_mortgage_annual_rate_pct,
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
            provident_fund_loan_cny_at_purchase=str(provident_loan),
            provident_fund_annual_rate_pct=provident_fund_annual_rate_pct,
            mortgage_reserve_mode=mortgage_reserve_mode,
            mortgage_reserve_annual_real_return_pct=(
                mortgage_reserve_annual_real_return_pct
            ),
        )
        purchase_factor = float(purchase_factor_decimal)
        monthly_housing_cost_real = (
            result["mortgage"]["monthly_payment_nominal_cny"] / purchase_factor
            + price_real * ownership_rate / 12
        )
        reasons: list[str] = []
        if result["minimum_investable_assets_real_cny"] < emergency_floor:
            reasons.append("emergency_floor")
        if not result["target_year_result"]["fi_target_met"]:
            reasons.append("fi_target")
        if monthly_housing_cost_real > monthly_cap_real:
            reasons.append("monthly_housing_cost")
        return result, reasons, monthly_housing_cost_real

    tiers: list[dict[str, Any]] = []
    for target_year, monthly_cap in zip(
        fi_target_years,
        monthly_housing_cost_caps_cny_in_base_year_purchasing_power,
        strict=True,
    ):
        purchase_results: list[dict[str, Any]] = []
        for purchase_year in purchase_years:
            down_payment_results: list[dict[str, Any]] = []
            for down_payment_pct in down_payment_pcts:
                low = 0.0
                high = price_search_upper_bound_cny_in_base_year_purchasing_power
                _, zero_reasons, _ = evaluate(
                    price_real=0,
                    purchase_year=purchase_year,
                    target_year=target_year,
                    down_payment_pct=down_payment_pct,
                    monthly_cap_real=monthly_cap,
                )
                if zero_reasons:
                    ceiling = 0.0
                else:
                    for _ in range(60):
                        midpoint = (low + high) / 2
                        _, reasons, _ = evaluate(
                            price_real=midpoint,
                            purchase_year=purchase_year,
                            target_year=target_year,
                            down_payment_pct=down_payment_pct,
                            monthly_cap_real=monthly_cap,
                        )
                        if reasons:
                            high = midpoint
                        else:
                            low = midpoint
                    ceiling = math.floor(low / price_rounding_increment_cny) * (
                        price_rounding_increment_cny
                    )

                result, reasons, monthly_housing_cost_real = evaluate(
                    price_real=ceiling,
                    purchase_year=purchase_year,
                    target_year=target_year,
                    down_payment_pct=down_payment_pct,
                    monthly_cap_real=monthly_cap,
                )
                next_price = min(
                    ceiling + price_rounding_increment_cny,
                    price_search_upper_bound_cny_in_base_year_purchasing_power,
                )
                _, next_reasons, _ = evaluate(
                    price_real=next_price,
                    purchase_year=purchase_year,
                    target_year=target_year,
                    down_payment_pct=down_payment_pct,
                    monthly_cap_real=monthly_cap,
                )
                if not next_reasons:
                    next_reasons = ["search_upper_bound"]
                down_payment_results.append(
                    {
                        "down_payment_pct": down_payment_pct,
                        "maximum_home_price_real_cny": ceiling,
                        "monthly_housing_cost_real_cny_at_ceiling": round(
                            monthly_housing_cost_real, 2
                        ),
                        "minimum_investable_assets_real_cny": result[
                            "minimum_investable_assets_real_cny"
                        ],
                        "fi_surplus_real_cny": result["target_year_result"][
                            "surplus_real_cny"
                        ],
                        "constraints_at_ceiling": reasons,
                        "binding_constraints_at_next_increment": next_reasons,
                    }
                )
            recommended = max(
                down_payment_results,
                key=lambda item: (
                    item["maximum_home_price_real_cny"],
                    -item["down_payment_pct"],
                ),
            )
            purchase_results.append(
                {
                    "purchase_year": purchase_year,
                    "recommended_down_payment_pct": recommended[
                        "down_payment_pct"
                    ],
                    "maximum_home_price_real_cny": recommended[
                        "maximum_home_price_real_cny"
                    ],
                    "binding_constraints_at_next_increment": recommended[
                        "binding_constraints_at_next_increment"
                    ],
                    "down_payment_results": down_payment_results,
                }
            )
        tiers.append(
            {
                "fi_target_year": target_year,
                "monthly_housing_cost_cap_real_cny": monthly_cap,
                "purchase_results": purchase_results,
            }
        )

    return {
        "calculation_version": "home-boundary-0.1.0",
        "currency": "CNY",
        "value_basis": f"real_{base_year}_purchasing_power",
        "base_year": base_year,
        "mortgage_reserve_mode": mortgage_reserve_mode,
        "price_rounding_increment_cny": price_rounding_increment_cny,
        "tiers": tiers,
        "warnings": [
            "A price ceiling is a deterministic scenario boundary, not a mortgage approval or recommendation to spend up to the limit.",
            "The primary home is excluded from investable assets.",
            "The conditional provident-fund tranche must be reverified at purchase.",
            "The next price increment identifies the active modeled constraint; real property costs may introduce additional constraints.",
        ],
    }
