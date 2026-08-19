# Financial-independence calculation contract

The MCP server name is exactly `personal-finance-planner`. Do not normalize it to the Python package name `personal_finance_planner`. Resource URIs such as `fi://catalog` and all FI/home calculation Tools belong to the hyphenated server name.

The canonical schemas are located at the Plugin root:

- `schemas/financial-independence-input.schema.json`
- `schemas/financial-independence-output.schema.json`
- `schemas/fi-milestones-input.schema.json`
- `schemas/fi-milestones-output.schema.json`
- `schemas/home-opportunity-input.schema.json`
- `schemas/home-opportunity-output.schema.json`
- `schemas/home-opportunity-boundary-input.schema.json`
- `schemas/home-opportunity-boundary-output.schema.json`

All monetary results are CNY in the base year's purchasing power. `real_return_rates_pct` therefore represents nominal return after subtracting inflation, fees, and taxes to the extent the user intends. If those components are not explicitly modeled, label the real return as a scenario rather than a forecast.

The capital target is:

```text
max(annual spending - stable annual income at target, 0)
÷ withdrawal rate
+ one-time reserve
```

The projection applies the selected real return annually and adds the annual surplus at each year-end beginning with `income_start_year`. When after-tax income is supplied but the start year is missing, the calculator reports the potential annual surplus but intentionally excludes future contributions from the projection.

Use a one-time reserve only for a scenario that must still be funded in addition to the income-producing portfolio at the FI target. It is generic and may represent any confirmed major expense, not only housing. Do not use it to imply that a purchase before the target year was deducted at the correct time.

## Major-expense intake boundary

Before presenting a final FI baseline, establish whether there are planned or possible major expenses within or near the FI horizon. Examples include a home, vehicle, education, care, business funding, or another user-defined outlay. Capture amount state, currency, timing or trigger, commitment, flexibility, funding source, shared-funding conflicts, and recurring cashflow changes. Preserve `unknown` when the user has not decided; silence is not evidence of zero.

A committed expense may enter the baseline only when its amount, timing, and funding treatment are supportable. Optional and exploratory expenses remain separate sensitivities unless the user explicitly approves continuous funding. The current generic FI and milestone contracts do not time arbitrary pre-target outlays. If such an outlay matters and no dedicated deterministic calculator exists, report it as an unmodeled gap rather than adding it to the target-year reserve or using mental arithmetic. A primary-home purchase remains a special case because the Plugin has a dedicated scenario calculator for its upfront cost, mortgage, ownership cost, and emergency-fund path.

Important output warnings are part of the result, not cosmetic text. Do not omit them when presenting the calculation.

## Annual-milestone contract

The milestone calculator uses the same real-value FI target. The base-year row is the supplied snapshot. Each later checkpoint compounds the prior balance for one calendar year and then applies that calendar year's modeled cashflow. Therefore a contribution earned during calendar year 2027 appears in the 2028 checkpoint.

Set `cashflow_start_year` to the first full calendar year worth modeling. Before `income_start_year`, the calculator subtracts `annual_portfolio_draw_before_income_cny`; once income is active, it applies after-tax income minus annual spending. Use zero draw only when spending is already covered elsewhere or the partial base year is intentionally omitted.

For each return and income-start combination, report both:

```text
required on-track assets
  = present value of final FI target
  - present value of all remaining scenario cashflows

capital-only threshold
  = present value of final FI target without future employment cashflows
```

The route status compares assets with the required on-track path: green is at least 100%, yellow is from the configured floor (90% by default) to less than 100%, and red is below that floor. This is a planning-health signal, not a claim that FI has already been achieved. Always show `current_assets_as_pct_of_capital_target` separately.

An actual checkpoint requires both its year and investable-asset amount. The returned constant annual contribution is the equal real year-end net contribution needed after the scenario's income-start year, after accounting for modeled pre-income portfolio draws. It is a sensitivity, not an instruction to invest or a guaranteed recovery path.

## Home-opportunity contract

The home price, renovation budget, income, rent, ordinary spending, emergency fund, real return, and FI result are expressed in the base year's purchasing power. The calculator inflates the home price and renovation budget to the purchase year; the mortgage contract and payment remain nominal. This keeps different purchase years comparable while making the nominal loan payment explicit.

The purchase occurs at the beginning of `purchase_year`. Full-year cash flows begin at `cashflow_start_year`; no partial base year is modeled. Equal principal-and-interest repayment is used. A mortgage payment stops after the contractual term.

The target-year requirement is:

```text
(annual non-housing spending + annual ownership cost)
÷ withdrawal rate
+ remaining mortgage principal in target-year real CNY
```

This intentionally excludes the primary home's market value from investable assets. It also avoids capitalizing temporary mortgage payments forever: the result instead reserves enough target-year capital to repay the remaining mortgage. Home appreciation, sale proceeds, and mortgage tax savings are excluded unless a separate, evidence-backed scenario explicitly adds them.

For an evidence-backed combination-loan scenario, `mortgage_annual_rate_pct` applies to the commercial tranche and the optional `provident_fund_loan_cny_at_purchase` plus `provident_fund_annual_rate_pct` define the provident-fund tranche. Both use the same term in the current contract. The caller-supplied provident amount must not exceed the total loan and must never be inferred from balance alone. Report the commercial and provident principals, payments, and remaining balances separately.

Always report whether the emergency-fund floor survives immediately after the down payment, transaction costs, and renovation budget. A mathematically positive portfolio is not enough when it violates that floor.

## Home-boundary contract

The boundary calculator searches a real-CNY home price for each purchase year, FI deadline, monthly housing-cost cap, and down-payment percentage. A price is feasible only when all three conditions hold:

```text
minimum real investable assets throughout the path >= emergency floor
monthly real mortgage plus ownership cost <= housing-cost cap
projected investable assets at the FI deadline >= FI target
```

Round the ceiling down by `price_rounding_increment_cny`, then evaluate the next increment to identify the active constraint. Select the down-payment percentage with the highest feasible price; when ceilings tie, prefer the lower down payment. Treat the result as a scenario boundary, not an approval or instruction to spend to the limit.

`payoff_principal` adds the remaining principal to the FI target and is the conservative anchor. `discounted_remaining_payments` instead discounts remaining contractual payments using the stated reserve return. The latter can produce a higher price ceiling but depends on earning that return and retaining the mortgage, so present it only as sensitivity.
