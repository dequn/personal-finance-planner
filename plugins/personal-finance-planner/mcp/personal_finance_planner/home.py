"""Deterministic home-opportunity scenarios linked to financial independence."""

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


def _inflation_factor(inflation_rate: Decimal, years: int) -> Decimal:
    return (Decimal("1") + inflation_rate) ** years


def _monthly_payment(
    principal: Decimal, annual_rate: Decimal, term_months: int
) -> Decimal:
    if principal == 0:
        return Decimal("0")
    monthly_rate = annual_rate / Decimal("12")
    if monthly_rate == 0:
        return principal / Decimal(term_months)
    factor = (Decimal("1") + monthly_rate) ** term_months
    return principal * monthly_rate * factor / (factor - Decimal("1"))


def _remaining_principal(
    principal: Decimal,
    annual_rate: Decimal,
    term_months: int,
    paid_months: int,
) -> Decimal:
    if paid_months >= term_months or principal == 0:
        return Decimal("0")
    monthly_rate = annual_rate / Decimal("12")
    if monthly_rate == 0:
        return principal * Decimal(term_months - paid_months) / Decimal(term_months)
    payment = _monthly_payment(principal, annual_rate, term_months)
    factor = (Decimal("1") + monthly_rate) ** paid_months
    return principal * factor - payment * (factor - Decimal("1")) / monthly_rate


def _remaining_payment_present_value(
    principal: Decimal,
    annual_rate: Decimal,
    term_months: int,
    paid_months: int,
    annual_discount_rate: Decimal,
) -> Decimal:
    remaining_months = max(term_months - paid_months, 0)
    if remaining_months == 0 or principal == 0:
        return Decimal("0")
    payment = _monthly_payment(principal, annual_rate, term_months)
    monthly_discount_rate = annual_discount_rate / Decimal("12")
    if monthly_discount_rate == 0:
        return payment * Decimal(remaining_months)
    factor = (Decimal("1") + monthly_discount_rate) ** (-remaining_months)
    return payment * (Decimal("1") - factor) / monthly_discount_rate


def calculate_home_opportunity(
    *,
    base_year: int,
    target_year: int,
    purchase_year: int,
    current_investable_assets_cny: int | float | str,
    home_price_cny_in_base_year_purchasing_power: int | float | str,
    down_payment_pct: int | float | str,
    mortgage_annual_rate_pct: int | float | str,
    mortgage_term_years: int,
    transaction_cost_pct: int | float | str,
    renovation_and_furnishing_cny_in_base_year_purchasing_power: int | float | str,
    annual_ownership_cost_pct_of_home_price: int | float | str,
    annual_non_housing_spending_cny_in_base_year_purchasing_power: int | float | str,
    annual_rent_cny_in_base_year_purchasing_power: int | float | str,
    annual_after_tax_income_cny_in_base_year_purchasing_power: int | float | str,
    income_start_year: int,
    cashflow_start_year: int,
    annual_real_return_pct: int | float | str,
    annual_inflation_pct: int | float | str,
    fi_withdrawal_rate_pct: int | float | str,
    minimum_emergency_fund_cny_in_base_year_purchasing_power: int | float | str,
    provident_fund_loan_cny_at_purchase: int | float | str = 0,
    provident_fund_annual_rate_pct: int | float | str = 2.6,
    mortgage_reserve_mode: str = "payoff_principal",
    mortgage_reserve_annual_real_return_pct: int | float | str | None = None,
) -> dict[str, Any]:
    """Project a purchase and its effect on the target-year FI requirement."""
    if target_year <= base_year:
        raise ValueError("target_year must be greater than base_year")
    if not base_year <= purchase_year < target_year:
        raise ValueError("purchase_year must be within [base_year, target_year)")
    if not base_year <= income_start_year < target_year:
        raise ValueError("income_start_year must be within [base_year, target_year)")
    if not base_year <= cashflow_start_year < target_year:
        raise ValueError("cashflow_start_year must be within [base_year, target_year)")
    if mortgage_term_years <= 0:
        raise ValueError("mortgage_term_years must be positive")

    current_assets = _decimal(current_investable_assets_cny)
    home_price_real = _decimal(home_price_cny_in_base_year_purchasing_power)
    down_payment_rate = _decimal(down_payment_pct) / Decimal("100")
    mortgage_rate_pct = _decimal(mortgage_annual_rate_pct)
    mortgage_rate = mortgage_rate_pct / Decimal("100")
    provident_loan_nominal = _decimal(provident_fund_loan_cny_at_purchase)
    provident_rate_pct = _decimal(provident_fund_annual_rate_pct)
    provident_rate = provident_rate_pct / Decimal("100")
    transaction_rate = _decimal(transaction_cost_pct) / Decimal("100")
    renovation_real = _decimal(
        renovation_and_furnishing_cny_in_base_year_purchasing_power
    )
    ownership_rate = _decimal(annual_ownership_cost_pct_of_home_price) / Decimal(
        "100"
    )
    non_housing_real = _decimal(
        annual_non_housing_spending_cny_in_base_year_purchasing_power
    )
    rent_real = _decimal(annual_rent_cny_in_base_year_purchasing_power)
    income_real = _decimal(
        annual_after_tax_income_cny_in_base_year_purchasing_power
    )
    real_return = _decimal(annual_real_return_pct) / Decimal("100")
    inflation = _decimal(annual_inflation_pct) / Decimal("100")
    withdrawal_rate = _decimal(fi_withdrawal_rate_pct) / Decimal("100")
    emergency_real = _decimal(
        minimum_emergency_fund_cny_in_base_year_purchasing_power
    )
    reserve_real_return = (
        real_return
        if mortgage_reserve_annual_real_return_pct is None
        else _decimal(mortgage_reserve_annual_real_return_pct) / Decimal("100")
    )

    nonnegative_values = (
        current_assets,
        home_price_real,
        renovation_real,
        non_housing_real,
        rent_real,
        income_real,
        emergency_real,
        provident_loan_nominal,
    )
    if any(value < 0 for value in nonnegative_values):
        raise ValueError("monetary inputs must be non-negative")
    if not Decimal("0") <= down_payment_rate <= Decimal("1"):
        raise ValueError("down_payment_pct must be within [0, 100]")
    if mortgage_rate < 0:
        raise ValueError("mortgage_annual_rate_pct must be non-negative")
    if provident_rate < 0:
        raise ValueError("provident_fund_annual_rate_pct must be non-negative")
    if not Decimal("0") <= transaction_rate < Decimal("1"):
        raise ValueError("transaction_cost_pct must be within [0, 100)")
    if not Decimal("0") <= ownership_rate < Decimal("1"):
        raise ValueError(
            "annual_ownership_cost_pct_of_home_price must be within [0, 100)"
        )
    if real_return <= Decimal("-1") or inflation <= Decimal("-1"):
        raise ValueError("return and inflation rates must be greater than -100")
    if reserve_real_return <= Decimal("-1"):
        raise ValueError(
            "mortgage_reserve_annual_real_return_pct must be greater than -100"
        )
    if not Decimal("0") < withdrawal_rate < Decimal("1"):
        raise ValueError("fi_withdrawal_rate_pct must be within (0, 100)")
    if mortgage_reserve_mode not in {
        "payoff_principal",
        "discounted_remaining_payments",
    }:
        raise ValueError(
            "mortgage_reserve_mode must be payoff_principal or discounted_remaining_payments"
        )

    nominal_return = (Decimal("1") + real_return) * (
        Decimal("1") + inflation
    ) - Decimal("1")
    purchase_inflation_factor = _inflation_factor(
        inflation, purchase_year - base_year
    )
    target_inflation_factor = _inflation_factor(inflation, target_year - base_year)

    home_price_nominal = home_price_real * purchase_inflation_factor
    down_payment_nominal = home_price_nominal * down_payment_rate
    loan_principal_nominal = home_price_nominal - down_payment_nominal
    if provident_loan_nominal > loan_principal_nominal:
        if provident_loan_nominal - loan_principal_nominal <= MONEY_QUANTUM:
            provident_loan_nominal = loan_principal_nominal
        else:
            raise ValueError(
                "provident_fund_loan_cny_at_purchase cannot exceed total loan principal"
            )
    commercial_loan_nominal = loan_principal_nominal - provident_loan_nominal
    transaction_cost_nominal = home_price_nominal * transaction_rate
    renovation_nominal = renovation_real * purchase_inflation_factor
    upfront_cash_nominal = (
        down_payment_nominal + transaction_cost_nominal + renovation_nominal
    )

    term_months = mortgage_term_years * 12
    commercial_monthly_payment_nominal = _monthly_payment(
        commercial_loan_nominal, mortgage_rate, term_months
    )
    provident_monthly_payment_nominal = _monthly_payment(
        provident_loan_nominal, provident_rate, term_months
    )
    monthly_payment_nominal = (
        commercial_monthly_payment_nominal + provident_monthly_payment_nominal
    )
    annual_payment_nominal = monthly_payment_nominal * Decimal("12")
    paid_months_at_target = min(
        max(target_year - purchase_year, 0) * 12, term_months
    )
    commercial_remaining_principal_nominal = _remaining_principal(
        commercial_loan_nominal,
        mortgage_rate,
        term_months,
        paid_months_at_target,
    )
    provident_remaining_principal_nominal = _remaining_principal(
        provident_loan_nominal,
        provident_rate,
        term_months,
        paid_months_at_target,
    )
    remaining_principal_nominal = (
        commercial_remaining_principal_nominal
        + provident_remaining_principal_nominal
    )
    remaining_principal_real_at_target = (
        remaining_principal_nominal / target_inflation_factor
    )
    reserve_nominal_return = (Decimal("1") + reserve_real_return) * (
        Decimal("1") + inflation
    ) - Decimal("1")
    discounted_commercial_payments_nominal = _remaining_payment_present_value(
        commercial_loan_nominal,
        mortgage_rate,
        term_months,
        paid_months_at_target,
        reserve_nominal_return,
    )
    discounted_provident_payments_nominal = _remaining_payment_present_value(
        provident_loan_nominal,
        provident_rate,
        term_months,
        paid_months_at_target,
        reserve_nominal_return,
    )
    discounted_remaining_payments_real_at_target = (
        discounted_commercial_payments_nominal
        + discounted_provident_payments_nominal
    ) / target_inflation_factor
    mortgage_funding_reserve_real = (
        remaining_principal_real_at_target
        if mortgage_reserve_mode == "payoff_principal"
        else discounted_remaining_payments_real_at_target
    )

    annual_ownership_cost_real = home_price_real * ownership_rate
    permanent_annual_spending_real = non_housing_real + annual_ownership_cost_real
    permanent_spending_capital_real = permanent_annual_spending_real / withdrawal_rate
    total_fi_target_real = (
        permanent_spending_capital_real + mortgage_funding_reserve_real
    )

    balance_nominal = current_assets
    post_upfront_assets_real: Decimal | None = None
    minimum_assets_real = current_assets
    yearly_cashflows: list[dict[str, Any]] = []
    purchased = False

    for year in range(base_year, target_year):
        year_factor = _inflation_factor(inflation, year - base_year)
        if year == purchase_year:
            balance_nominal -= upfront_cash_nominal
            purchased = True
            post_upfront_assets_real = balance_nominal / year_factor
            minimum_assets_real = min(minimum_assets_real, post_upfront_assets_real)

        balance_nominal *= Decimal("1") + nominal_return

        income_nominal = Decimal("0")
        spending_nominal = Decimal("0")
        mortgage_payment_nominal = Decimal("0")
        if year >= cashflow_start_year:
            if year >= income_start_year:
                income_nominal = income_real * year_factor
            if purchased:
                if year - purchase_year < mortgage_term_years:
                    mortgage_payment_nominal = annual_payment_nominal
                spending_nominal = (
                    permanent_annual_spending_real * year_factor
                    + mortgage_payment_nominal
                )
            else:
                spending_nominal = (non_housing_real + rent_real) * year_factor
            balance_nominal += income_nominal - spending_nominal

        end_factor = _inflation_factor(inflation, year + 1 - base_year)
        end_balance_real = balance_nominal / end_factor
        minimum_assets_real = min(minimum_assets_real, end_balance_real)
        yearly_cashflows.append(
            {
                "year": year,
                "home_owned": purchased,
                "income_nominal_cny": _money(income_nominal),
                "spending_nominal_cny": _money(spending_nominal),
                "mortgage_payment_nominal_cny": _money(
                    mortgage_payment_nominal
                ),
                "end_investable_assets_real_cny": _money(end_balance_real),
            }
        )

    projected_assets_real = balance_nominal / target_inflation_factor
    gap_real = max(total_fi_target_real - projected_assets_real, Decimal("0"))
    surplus_real = max(projected_assets_real - total_fi_target_real, Decimal("0"))
    emergency_preserved_after_purchase = (
        post_upfront_assets_real is not None
        and post_upfront_assets_real >= emergency_real
    )

    warnings = [
        "The primary home is excluded from investable assets and the FI denominator.",
        "Home price, renovation, income, rent, and ordinary spending are modeled in base-year purchasing power; actual housing prices and income may not track inflation.",
        "The calculation begins annual cash flows at cashflow_start_year and does not model a partial base year.",
    ]
    if mortgage_reserve_mode == "payoff_principal":
        warnings.append(
            "The target includes a payoff reserve equal to remaining mortgage principal rather than capitalizing mortgage payments forever."
        )
    else:
        warnings.append(
            "The target funds remaining scheduled mortgage payments at the caller-supplied reserve return; this assumes the reserve earns that return and is not equivalent to debt-free status."
        )
    if provident_loan_nominal > 0:
        warnings.append(
            "The provident-fund tranche is a caller-supplied conditional scenario; official eligibility, approval, and the current rate must be reverified at purchase."
        )
        warnings.append(
            "Mortgage-interest tax savings are excluded until user-specific evidence is available."
        )
    else:
        warnings.append(
            "Mortgage-interest tax savings and provident-fund loan eligibility are excluded until user-specific evidence is available."
        )
    if not emergency_preserved_after_purchase:
        warnings.append(
            "The minimum emergency fund is not preserved immediately after upfront purchase costs."
        )
    if minimum_assets_real < 0:
        warnings.append("Investable assets become negative in the modeled path.")

    return {
        "calculation_version": "home-0.3.0",
        "currency": "CNY",
        "value_basis": f"real_{base_year}_purchasing_power_except_contractual_nominal_mortgage",
        "base_year": base_year,
        "target_year": target_year,
        "purchase_year": purchase_year,
        "assumptions": {
            "annual_real_return_pct": _rate(real_return * Decimal("100")),
            "annual_inflation_pct": _rate(inflation * Decimal("100")),
            "nominal_portfolio_return_pct": _rate(nominal_return * Decimal("100")),
            "income_start_year": income_start_year,
            "cashflow_start_year": cashflow_start_year,
            "fi_withdrawal_rate_pct": _rate(withdrawal_rate * Decimal("100")),
            "mortgage_reserve_mode": mortgage_reserve_mode,
            "mortgage_reserve_annual_real_return_pct": _rate(
                reserve_real_return * Decimal("100")
            ),
        },
        "purchase": {
            "home_price_real_cny": _money(home_price_real),
            "home_price_nominal_at_purchase_cny": _money(home_price_nominal),
            "down_payment_pct": _rate(down_payment_rate * Decimal("100")),
            "down_payment_nominal_cny": _money(down_payment_nominal),
            "transaction_cost_nominal_cny": _money(transaction_cost_nominal),
            "renovation_and_furnishing_nominal_cny": _money(renovation_nominal),
            "upfront_cash_nominal_cny": _money(upfront_cash_nominal),
            "post_upfront_investable_assets_real_cny": (
                _money(post_upfront_assets_real)
                if post_upfront_assets_real is not None
                else None
            ),
            "emergency_fund_preserved_after_purchase": emergency_preserved_after_purchase,
        },
        "mortgage": {
            "mortgage_type": (
                "combination" if provident_loan_nominal > 0 else "commercial_only"
            ),
            "loan_principal_nominal_cny": _money(loan_principal_nominal),
            "commercial_loan_principal_nominal_cny": _money(
                commercial_loan_nominal
            ),
            "annual_rate_pct": _rate(mortgage_rate_pct),
            "commercial_monthly_payment_nominal_cny": _money(
                commercial_monthly_payment_nominal
            ),
            "provident_fund_loan_principal_nominal_cny": _money(
                provident_loan_nominal
            ),
            "provident_fund_annual_rate_pct": _rate(provident_rate_pct),
            "provident_fund_monthly_payment_nominal_cny": _money(
                provident_monthly_payment_nominal
            ),
            "term_years": mortgage_term_years,
            "monthly_payment_nominal_cny": _money(monthly_payment_nominal),
            "annual_payment_nominal_cny": _money(annual_payment_nominal),
            "paid_months_at_target": paid_months_at_target,
            "remaining_principal_nominal_at_target_cny": _money(
                remaining_principal_nominal
            ),
            "commercial_remaining_principal_nominal_at_target_cny": _money(
                commercial_remaining_principal_nominal
            ),
            "provident_fund_remaining_principal_nominal_at_target_cny": _money(
                provident_remaining_principal_nominal
            ),
            "remaining_principal_real_at_target_cny": _money(
                remaining_principal_real_at_target
            ),
            "discounted_remaining_payments_real_at_target_cny": _money(
                discounted_remaining_payments_real_at_target
            ),
        },
        "target_year_result": {
            "permanent_annual_spending_real_cny": _money(
                permanent_annual_spending_real
            ),
            "permanent_spending_capital_real_cny": _money(
                permanent_spending_capital_real
            ),
            "mortgage_payoff_reserve_real_cny": _money(
                remaining_principal_real_at_target
            ),
            "mortgage_funding_reserve_real_cny": _money(
                mortgage_funding_reserve_real
            ),
            "mortgage_reserve_mode": mortgage_reserve_mode,
            "total_fi_target_real_cny": _money(total_fi_target_real),
            "projected_investable_assets_real_cny": _money(projected_assets_real),
            "gap_real_cny": _money(gap_real),
            "surplus_real_cny": _money(surplus_real),
            "fi_target_met": projected_assets_real >= total_fi_target_real,
        },
        "minimum_investable_assets_real_cny": _money(minimum_assets_real),
        "yearly_cashflows": yearly_cashflows,
        "warnings": warnings,
        "provenance_card_ids": [
            "china-lpr-2026-07",
            "shanghai-housing-credit-policy-2025",
            "shanghai-housing-policy-2026",
            "china-provident-fund-rate-2025",
            "shanghai-provident-fund-loan-eligibility",
            "shanghai-mortgage-tax",
        ],
    }
