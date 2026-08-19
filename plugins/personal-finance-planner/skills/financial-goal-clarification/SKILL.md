---
name: financial-goal-clarification
description: Clarify, prioritize, conflict-check, and explicitly confirm financial goals before allocation or product selection. Use when a user describes retirement, financial independence, housing, education, family support, emergency reserves, major purchases, or other goals with incomplete amounts, dates, currencies, priorities, commitment levels, or flexibility; also use when an existing goal changes or conflicts with another goal. Do not use it to invent target amounts, silently convert optional goals into liabilities, select products, or persist changes without explicit approval.
---

# Financial Goal Clarification

## Purpose

Turn informal wishes into auditable goal records while preserving uncertainty, flexibility, and conflicts.

## Workflow

1. Read `references/goal-clarification-prompt.md` completely and treat it as the canonical Prompt contract.
2. Read `allocation://v0.1.0/sources/cfp-board-seven-step` and `allocation://v0.1.0/sources/cfa-goals-based-constraints`. If MCP Resources are unavailable, read the matching files under `../../knowledge/allocation/v0.1.0/`.
3. Start from confirmed profile facts when supplied. Do not make profile intake a prerequisite for recording a provisional goal.
4. Run a lightweight goal-family scan across safety and resilience, retirement or independence, major purchases, education, family support, health and care, debt, business or career, legacy or giving, lifestyle, and other user-defined needs. Do not turn the scan into a mandatory questionnaire; create detailed records only for active, possible, exploratory, or deferred goals.
5. Give each goal a stable ID. For a new v0.2 proposal, classify it with broad `goal_category`, open stable-slug `goal_subtype`, and financial `outcome_type`; never encode a country, Skill, MCP Tool, or calculator name in those fields. Preserve an existing v0.1 record until an explicit migration or newly confirmed version is requested.
6. Collect only decision-relevant fields: name, priority rank, `committed` versus `optional` versus `exploratory` versus `deferred`, amount status and currency, timing, minimum acceptable outcome, flexibility, funding status, dependencies, and evidence state.
7. Separate a hard goal from an opportunity scenario. Do not reserve funds continuously for an optional goal unless the user explicitly approves that policy.
8. Detect shared-funding, timing, liquidity, currency, and feasibility conflicts. Show the trade-off before asking the user to choose. A calculation gap remains `to_be_calculated`, not a guessed amount.
9. Ask one to three questions that can change priority, feasibility, required liquidity, or allocation. Do not reopen already confirmed decisions without new conflicting evidence.
10. Resolve Schemas through MCP Resources `planning://schemas/financial-goals-proposal` and `planning://schemas/financial-goals-confirmed` on server `personal-finance-planner`. If Resource access is unavailable, use Plugin-root files `schemas/financial-goals-proposal.schema.json` and `schemas/financial-goals-confirmed.schema.json` (from this Skill directory: `../../schemas/...`). The unconfirmed filename is `proposal`, never `proposed`.
11. Produce a `financial_goals` proposal conforming to `financial-goals-proposal.schema.json`, using `schema_version: 0.2.0` for newly structured output. When available, call `validate_financial_goals` before presenting it.
12. Confirm only after the user explicitly accepts named goals or changes. A confirmed record must conform to `financial-goals-confirmed.schema.json`; unresolved conflicts must remain visible and cannot be silently marked resolved.

## Safety boundaries

- Do not choose a target amount, target date, inflation rate, return assumption, or withdrawal rate merely because a common default exists.
- Do not infer a detailed subtype from age, account balances, jurisdiction, or silence. `goal_subtype` is open vocabulary, not a claim that a matching scenario calculator exists.
- Do not merge emergency liquidity with a home, education, or retirement reserve unless the user explicitly approves the overlap.
- Do not count an uncollected receivable, primary residence, or volatile asset as guaranteed goal funding without an explicit eligibility rule.
- Do not output product recommendations, trades, redemptions, FX actions, or guaranteed outcomes.
- Do not write confirmed state. Return a validated proposal and an explicit confirmation request for the host.

## Output order

1. Goal map and the current decision.
2. Confirmed, proposed, optional, deferred, and unknown goals.
3. Category, subtype, outcome type, priority, amount, timing, currency, flexibility, and funding evidence.
4. Conflicts and bounded alternatives.
5. One to three highest-impact questions.
6. A schema-valid proposal when useful.
7. Explicit confirmation scope and next planning step.
