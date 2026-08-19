---
name: plan-financial-independence
description: Estimate, review, or track a personal financial-independence target while identifying how planned or possible major expenses affect investable assets, liquidity, recurring cashflow, and the target-year gap. Use when the user asks how much capital they need, whether a target year is feasible, what annual milestones keep the plan on track, whether an actual checkpoint is green/yellow/red, how spending or withdrawal-rate assumptions change the result, or how pension, housing, vehicles, education, care, business funding, or another large outlay should enter the plan. Do not use it to select products, promise returns, invent an unmentioned expense, estimate a pension from contribution years alone, approve borrowing, or execute transactions.
---

# Plan Financial Independence

## Overview

Turn a financial-independence goal into an auditable range rather than a single magic number. Separate confirmed facts from planning assumptions, use the MCP calculator for arithmetic, and cite the public knowledge cards that justify the assumption range.

## Workflow

1. Establish the calculation date, target year, birth year, current investable assets, and annual spending in today's purchasing power.
2. Reconcile spending components. If rent, non-housing spending, insurance, or debt payments do not add up to the annual total, show the mismatch instead of silently choosing one value.
3. Run a short major-expense scan before presenting the final FI baseline. Ask whether the user has any planned or possible home, vehicle, education, care, business, or another large outlay between the base year and the FI horizon. Do not treat silence as no planned expense. Permit an explicit `none_confirmed` answer or preserve the field as unknown without blocking a preliminary estimate.
4. For each active major expense, collect only what can change the result: amount or range and currency, timing or trigger, commitment (`committed`, `optional`, `exploratory`, or `deferred`), flexibility, funding source, shared-funding conflicts, and any recurring cost or saving after the event. Reuse a confirmed `financial_goals` v0.2 record instead of asking again.
5. Keep the baseline and sensitivities distinct. Include a committed expense only when its amount, timing, and funding treatment are supportable. Keep optional or exploratory expenses in separate scenarios unless the user explicitly approves continuous funding. Use `one_time_goal_reserve_cny` only for an amount that must remain funded at the FI target; do not use it to pretend that a pre-target outlay was timed in the projection.
6. Treat pension or other stable income as zero until there is an official estimate or sufficiently complete benefit calculation. Contribution years alone are not enough.
7. Select a withdrawal-rate range from the versioned knowledge cards. For a horizon longer than 40 years, present 3.0% and 3.3% as planning scenarios and 4.0% only as a historical comparison unless evidence supports otherwise.
8. Use MCP server name exactly `personal-finance-planner`; do not normalize it to Python package form `personal_finance_planner`. Read Resources such as `fi://catalog` from that exact server and call its calculation Tools. If the required deterministic Tool is unavailable, label the calculation gap; do not substitute mental arithmetic for a claimed result.
9. When annual tracking is requested, use `calculate_financial_independence_milestones`. Set the first full cashflow year explicitly. Model portfolio-funded spending before income starts when a full no-income year is in scope. Compare at least one baseline and one stress scenario when timing or return uncertainty is material. The current milestone contract does not accept arbitrary timed outlays, so disclose any pre-target major expense that remains unmodeled.
10. Keep target completion distinct from route status. `current_assets_as_pct_of_capital_target` measures how much of the final FI capital exists today. Green/yellow/red compares assets with the scenario's minimum on-track path after crediting future modeled cashflows. Never say green means the user is already financially independent.
11. When a primary-home purchase is in scope, use `calculate_home_opportunity_scenario`. Model at least timing, price, down payment, mortgage rate and term, transaction and renovation costs, ownership costs, income start, inflation, real return, withdrawal rate, and emergency-fund floor. Add `provident_fund_loan_cny_at_purchase` and its rate only as a conditional tranche after checking user-specific balance, account status, contribution continuity, prior loan use, and the current policy cap.
12. Express the scenario home price in base-year purchasing power unless the user explicitly supplies a future nominal price. Exclude the primary home from investable assets. Compute the target as permanent post-purchase spending capital plus a reserve to repay the remaining mortgage at the target year.
13. When the user needs a home price ceiling or down-payment choice, use `calculate_home_opportunity_boundary_scenarios`. Search explicit purchase years, FI deadlines, monthly housing-cost caps, and down-payment percentages. Maintain the emergency floor throughout the path, not only immediately after purchase.
14. Use `payoff_principal` as the conservative home-scenario decision anchor. Show `discounted_remaining_payments` only as a sensitivity because it assumes the mortgage reserve earns the stated return while the debt remains outstanding.
15. Report the result as a range and sensitivity table. Label current facts, user estimates, system scenarios, missing inputs, and source limits.
16. End with the one or two questions or evidence items that would materially narrow the range.

## Required boundaries

- Express spending and targets in today's CNY when using real returns. Do not mix nominal future CNY with real withdrawal targets.
- A withdrawal rate is a scenario assumption, not a guarantee or a personalized regulated recommendation.
- The calculator is deterministic, but its result is only as reliable as the inputs and assumptions.
- Never infer that the user has no major expense because none was mentioned. Never invent its amount, date, commitment, funding source, or recurring effect.
- Do not count a purchased home, vehicle, education, or other consumption asset as income-producing FI capital. Treat a genuinely income-producing business asset only under an explicit, supportable cashflow assumption.
- Never infer pension amount, retirement eligibility, tax benefit, mortgage affordability, or product suitability from incomplete facts.
- Do not assume a provident-fund loan amount or mortgage-interest tax saving without user-specific evidence. Use a current commercial-rate scenario until eligibility and an actual quote are verified.
- Never package real personal financial data in this Plugin. Read it from the user's workspace or accept it as explicit runtime input.
- Never expose trading, redemption, subscription, borrowing, or FX execution as part of this workflow.

## Output contract

Use this order:

1. Conclusion: the target range and whether it appears reachable under each explicit scenario.
2. Confirmed inputs: values directly supplied by the user or authoritative workspace data, including whether the major-expense scan is confirmed, none confirmed, or still unknown.
3. Major-expense map: type, amount state, timing, commitment, flexibility, funding source, recurring cashflow effect, baseline treatment, and any unmodeled gap.
4. Scenario assumptions: withdrawal rate, real return, contribution start year, stable income, and any target-year one-time reserve.
5. Results: target capital, projected capital, gap or surplus, and target-age range. For a home scenario, also show upfront cash, post-purchase investable assets, emergency-fund preservation, monthly payment, remaining mortgage, and the target-year gap.
6. Annual route when requested: show the baseline checkpoints, the minimum required path, the capital-only progress measure, green/yellow/red definition, and any actual checkpoint assessment. State which future income and pre-income draw assumptions make the status conditional.
7. Sensitivities: at minimum spending and withdrawal rate; add major-expense, return, or contribution-start timing only when relevant. For a home boundary calculation, show the price ceiling, recommended down-payment range, active constraint, and implied FI year for the user's target price.
8. Exclusions and warnings: unresolved or unmodeled major expenses, pension, taxes, fees, health costs, and any unreconciled spending.
9. Sources: card ID, title, URL, publication or data date, and why it was used.
10. Next confirmation: one or two inputs with the largest effect on the decision.

## Source routing

Read `references/calculation-contract.md` before invoking the calculator. On MCP server `personal-finance-planner`, read Resource `fi://catalog` and only the cards relevant to the assumptions used. Never substitute the underscore-form Python package name for the hyphenated MCP server name.

- `bengen-1994`: historical 30-year withdrawal research context.
- `morningstar-2025`: contemporary 30- and 40-year withdrawal-rate research.
- `vanguard-retirement-income`: dynamic spending and sequence-risk principles.
- `china-pension-calculator`: official pension-estimate route.
- `china-retirement-policy`: current China retirement-age policy source.
- `shanghai-mortgage-tax`: Shanghai mortgage-interest deduction rule and its limits.
- `china-lpr-2026-07`: dated five-year-and-over LPR benchmark; not an actual mortgage quote.
- `shanghai-housing-credit-policy-2025`: bank-specific commercial-mortgage pricing boundary.
- `shanghai-housing-policy-2026`: current Shanghai provident-fund ceilings and eligibility limits.
- `china-provident-fund-rate-2025`: dated provident-fund mortgage rate; use only after eligibility confirmation.
- `shanghai-provident-fund-loan-eligibility`: account status, six-month continuity, balance multipliers, and repayment-capacity boundaries.

Do not cite a card that did not influence the result.

## Example trigger

For “I was born in 1991, spend CNY 120,000 per year, and want basic financial independence in 2036,” first ask whether any planned or possible major expense could use investable capital before or near 2036. Preserve an unknown answer, or classify supplied expenses by commitment and timing. Then calculate the age range as 44–45 and produce multiple withdrawal-rate targets. If the user provides employment income without a start year, calculate the potential annual surplus but do not silently project ten years of contributions.
