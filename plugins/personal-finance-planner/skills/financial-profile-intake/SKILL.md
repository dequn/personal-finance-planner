---
name: financial-profile-intake
description: Collect, reconcile, and progressively confirm the minimum personal-finance profile needed for planning. Use when a user is starting a financial plan, asks what information to provide, supplies partial income/spending/asset/liability/insurance/family facts, resumes an interrupted intake, or needs contradictions and missing high-impact inputs identified. Do not use it to collect credentials, select products, invent facts, or persist confirmation without explicit user approval.
---

# Financial Profile Intake

## Purpose

Build a portable, privacy-minimized planning profile without turning unknowns into facts or forcing a long questionnaire.

## Workflow

1. Read `references/profile-intake-prompt.md` completely and treat it as the canonical Prompt contract.
2. Read `allocation://v0.1.0/sources/cfp-board-seven-step`. If MCP Resources are unavailable, read `../../knowledge/allocation/v0.1.0/cfp-board-seven-step.yaml`.
3. Classify every supplied field as `user_confirmed`, `user_estimate`, `document_observed`, `calculated`, `unknown`, or `conflict`. Preserve source and observation date when available.
4. Cover only planning-relevant domains: household context, jurisdiction, income, spending, liabilities, insurance and protection, assets at category level, liquidity, pensions or stable income, and operational constraints.
5. Rank missing inputs by whether they can change safety floors, feasibility, risk capacity, goal funding, tax or jurisdiction treatment, or the next calculation. Ask one to three questions per round. Do not repeat fields already confirmed unless new evidence conflicts.
6. Keep values in original currency and keep balance, cost, face value, market value, and available cash distinct. Account-level product intake belongs in a separate holdings workflow.
7. Resolve Schemas through MCP Resources `planning://schemas/financial-profile-proposal` and `planning://schemas/financial-profile-confirmed` on server `personal-finance-planner`. If Resource access is unavailable, use Plugin-root files `schemas/financial-profile-proposal.schema.json` and `schemas/financial-profile-confirmed.schema.json` (from this Skill directory: `../../schemas/...`). The unconfirmed filename is `proposal`, never `proposed`.
8. Produce a `financial_profile` proposal that conforms to `financial-profile-proposal.schema.json`. When the MCP Tool is available, call `validate_financial_profile` before presenting the structured proposal.
9. Treat user acceptance as a separate gate. A confirmed profile must conform to `financial-profile-confirmed.schema.json`, include explicit confirmation and scope, and contain no unresolved conflict among the confirmed facts.

## Privacy and safety boundaries

- Never request or retain account numbers, card numbers, government identity numbers, passwords, passcodes, OTPs, API keys, tokens, cookies, QR codes, or device identifiers.
- Do not infer income, debt, dependents, insurance, tax residency, risk tolerance, or future employment from occupation, age, account balance, or silence.
- Do not require every low-impact field before planning. Preserve `unknown` and state which decisions remain blocked.
- Do not recommend products, allocations, returns, transactions, leverage, or account linking during profile intake.
- Do not write to a user workspace. Return a proposal for explicit host-mediated confirmation and persistence.

## Output order

1. Intake status and the decision this round unlocks.
2. Confirmed facts, estimates, conflicts, and unknowns.
3. One to three highest-impact questions.
4. What can and cannot yet be planned.
5. A schema-valid proposal when useful.
6. Explicit confirmation boundary and source limitations.
