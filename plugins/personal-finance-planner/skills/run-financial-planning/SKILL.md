---
name: run-financial-planning
description: Route and continue a personal financial-planning session through Workspace state, profile intake, goal clarification, and installed specialist workflows using confirmed neutral goal classifications. Use when a user asks to start, continue, resume, save, review, or update a financial plan without naming a specialist Skill, or when the correct next planning stage is unclear. Do not use it to persist state without an explicit save request, infer goal classifications from prose, select products, invent missing facts, or authorize transactions.
---

# Run Financial Planning

## Purpose

Choose one safe next planning stage while keeping the host runtime lightweight and the specialist Skills authoritative.

## Workflow

1. Read `references/planning-session-prompt.md` completely and treat it as the canonical coordination contract.
2. Identify the user's explicit requested capability, if any. Preserve it instead of silently expanding the task.
3. Classify supplied profile and goal records as `absent`, `proposed`, or `confirmed`. Treat conflicts separately from completeness.
4. For a validated confirmed `financial_goals` v0.2 record, copy only `goal_id`, `goal_category`, `goal_subtype`, `outcome_type`, `priority_rank`, and `commitment` into `goal_summaries`. Do not derive them from goal names or notes. For v0.1, omit the summaries.
5. Pass only declared session progress into `workflow_progress`. Do not mark a workflow complete merely because it was routed or discussed.
6. Call `route_financial_planning_stage` using the exact input contract at MCP Resource `planning://schemas/planning-session-route-input` on server name exactly `personal-finance-planner`. Read `planning://workflow-registry/v0.2.0` when the installed capability mapping is needed. Do not replace deterministic matching with free-form inference.
7. Execute only the routed stage:
   - `financial-profile-intake` for missing, proposed, changed, or conflicting profile facts;
   - `financial-goal-clarification` for missing, proposed, changed, or conflicting goals;
   - `plan-financial-independence` for FI and home-opportunity calculations;
   - `design-target-allocation` for target structure and cash-liquidity policy;
   - `manage-financial-planning-workspace` for an explicit initialize, read, resume, or confirmed-state save request;
   - this Skill for a bounded review or next-workflow choice.
8. Reuse confirmed fields and stable IDs. Do not restart intake, repeat answered questions, or downgrade confirmed facts without new conflicting evidence.
9. Report `matched_goal_ids`, `reason_codes`, and the registry version. If user choice is required, show only `available_next_capabilities` returned by the Tool.
10. Stop after one material stage. Summarize what changed, what remains blocked, and the exact next capability. Let the user continue in a later turn.

## Routing boundaries

- Permit explicit profile intake or provisional goal clarification without requiring the other record first.
- Permit an explicit Workspace-state request without forcing profile or goal intake. The Workspace Skill enforces its own confirmation and concurrency gates.
- Before any registered downstream work, route blocking profile conflicts or an unconfirmed profile to profile intake, then route unresolved or unconfirmed goals to goal clarification.
- For `auto`, let the Tool match actionable confirmed goals through the workflow registry. Do not present FI, home, cash, or any other capability unless the Tool routes it or includes it in `available_next_capabilities`.
- Treat `exploratory` and `deferred` goals as non-actionable for automatic implementation. An explicit scenario request may still route without creating or changing a goal.
- Treat workflow progress as non-authoritative session context. Only an explicit `completed` record can skip a covered goal/capability pair; persistence is outside this coordinator.
- Let the specialist Skill identify missing calculation inputs. A routed stage does not imply that its final answer can already be computed.

## Safety boundaries

- Do not persist profile or goals in the coordinator. Route an explicit save request to the Workspace Skill; never save automatically after confirmation.
- Do not request credentials, account numbers, OTPs, tokens, cookies, QR codes, or device identifiers.
- Do not select products or emit trades, subscriptions, redemptions, FX actions, leverage, or guaranteed outcomes.
- Do not treat route completion, profile confirmation, or goal confirmation as transaction authorization.

## Output order

1. Current stage and reason.
2. Reused confirmed context and visible conflicts.
3. The single routed action or bounded user choice.
4. What this stage can and cannot decide.
5. Next capability, confirmation boundary, and sources used.
