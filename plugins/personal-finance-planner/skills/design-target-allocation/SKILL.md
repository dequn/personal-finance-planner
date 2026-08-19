---
name: design-target-allocation
description: Design, structure, validate, or review an evidence-grounded personal target allocation from goals, time horizons, liquidity floors, risk capacity, risk tolerance, currency needs, and jurisdictional constraints. Use when the user asks what their portfolio structure should be, how cash/fixed income/equity/crypto targets should be separated, whether an existing allocation fits its goals, how to write an investment-policy allocation, or how to confirm and save that allocation. Do not use it to select products, promise returns, infer missing risk limits, auto-save proposals, or execute transactions.
---

# Design Target Allocation

## Purpose

Turn confirmed goals and constraints into an auditable allocation policy. Keep personal facts at runtime; the Plugin contains only public sources and reusable planning rules.

## Required workflow

1. Read `references/target-allocation-prompt.md` completely. Treat it as the canonical prompt contract for this Skill and the Plugin MCP Prompt. For cash-versus-cash-like decisions, also read `references/cash-liquidity-policy-prompt.md`; it is the canonical contract for the specialized MCP Prompt.
2. Read `allocation://catalog` and only the source cards that influence the answer. If MCP Resources are unavailable, read `../../knowledge/allocation/v0.1.0/catalog.yaml` and the selected card files directly.
3. Separate confirmed facts, user estimates, planning assumptions, contradictions, and missing inputs.
4. Freeze one investable-asset denominator. Exclude uncollected receivables, a primary residence, and non-investable assets unless the user explicitly selects another reporting view.
5. Define goal sub-portfolios before percentages: emergency/operations, committed or optional near-term goals, and long-term growth or financial independence.
6. Create mutually exclusive destination sleeves: true cash; deposits, certificates of deposit, and direct sovereign debt; other fixed income; equity; and crypto or other explicit high-risk assets. Classify funds by underlying exposure, not by the fund wrapper.
7. For China-mainland portfolio work involving bank wealth products, distinguish personal or account borrowing, the deterministic-anchor sleeve, and product-internal leverage inside other fixed income. Read `china-asset-management-guidance`, `china-commercial-bank-wealth-supervision`, and `china-wealth-liquidity-risk-management`; require the user's own product-internal-leverage limit and current product evidence instead of treating a regulatory maximum as a personal safe harbor.
8. Add maturity and time-to-usable-cash as a separate overlay. Never mix asset class and maturity into one apparently exhaustive table.
9. Add allocation groups for cross-destination constraints such as total low risk or equity plus crypto. Keep group IDs and member destination references explicit; do not duplicate the assets themselves.
10. State hard amount floors before target percentages. Give target ranges and a central value only when the supplied evidence supports them; otherwise give the missing decision and bounded alternatives.
11. Represent each of the five canonical asset destinations exactly once in a confirmed structure, including a zero range when appropriate. Make every destination range internally ordered and make central percentages sum to 100.
12. Represent maturity and reliable time to usable cash as two independent, exhaustive overlays. Do not let either overlay replace the asset-destination map.
13. Mark a pure cap as `ceiling_only`, and a long-run range with no completion deadline as `directional_range`. Neither mode is an implementation instruction.
14. Resolve the proposed Schema through MCP Resource `planning://schemas/target-allocation-proposal` on server `personal-finance-planner`; if Resource access is unavailable, use the Plugin-root fallback `schemas/target-allocation-proposal.schema.json` (from this Skill directory: `../../schemas/target-allocation-proposal.schema.json`). The filename is `proposal`, never `proposed`.
15. Emit a `target-allocation-proposal.schema.json` object with stable IDs, explicit conflicts, missing inputs, and the sources actually used. Use schema version `0.2.0` for allocation groups or directional ranges. Call `validate_target_allocation` with `target_state=proposed` and correct every deterministic error.
16. When a Schema-required identity field such as reporting currency is unknown, do not invent it merely to emit structured output; return blockers and questions without a proposal. When identity fields are known but denominator value, hard-floor amount, risk limits, or other ratio-setting inputs are missing, emit the minimal proposal with empty unsupported arrays. Do not create `0–100`, `0–0`, or other placeholder ranges, synthetic destinations, or unknown hard floors merely to satisfy references or silence the incomplete-five-destination warning.
17. Compare current versus target as a policy gap. A gap is not a buy, sell, redemption, FX, or rollover instruction.
18. Create a `confirmed` object only after showing the exact denominator, hard floors, all destination and group ranges, overlays, assumptions, conflicts, and confirmation scope and receiving explicit user confirmation. Revalidate with `target_state=confirmed`.
19. Persist a confirmed allocation only when the user separately asks to save it. Use the Workspace Skill and `record_type=allocation`; never persist a proposal automatically.
20. End with monitoring bands, rebalancing triggers, evidence limitations, and the sources actually used.

## Non-negotiable boundaries

- Do not use a universal age-based allocation formula as a personalized answer.
- Do not call daily-open wealth products, money-market funds, bond funds, or short-duration products true cash merely because redemption is operationally quick.
- Separate contractual ordinary redemption from distributor acceleration, and test both normal-state and stress-state time to usable cash.
- During a minimum holding period, count the affected amount as zero toward immediate operational liquidity.
- Do not call bank wealth products deposits, principal guaranteed, true cash, or a deterministic anchor without matching legal and contract evidence.
- Do not treat a fixed-income label or the 140-percent regulatory ceiling as proof of pure-bond exposure, low actual leverage, or suitability. If the user has not approved an internal-leverage policy, keep the limit missing rather than inventing one.
- Do not compare or aggregate trailing returns with different labels or windows.
- Keep willingness to take risk separate from capacity to absorb loss.
- Treat high-risk targets as ceilings or policy ranges unless the user explicitly approves a funded target; being below a cap is not a reason to buy.
- Do not calculate or store target amounts unless the denominator is exact. When amounts are included, require the Validator to reconcile them to the percentages.
- Apply jurisdictional rules only when the user's jurisdiction is known and the source is current enough for the decision.
- Never package personal holdings, goals, credentials, or transaction authority in this Plugin.

## Output order

1. Conclusion and the decision the allocation must solve.
2. Evidence state: facts, assumptions, conflicts, and blockers.
3. Goal sleeves and hard amount floors.
4. Mutually exclusive asset destination map with ranges, central values, and amounts.
5. Independent maturity/liquidity overlay.
6. Current-to-target gaps and no-action, conservative, and optional-enhancement paths.
7. Concentration, currency, cost, tax, liquidity, and product-evidence boundaries.
8. Monitoring and rebalancing rules.
9. Source-card IDs, canonical URLs, retrieval dates, and why each source was used.
10. Proposed or confirmed structured allocation, validation result, and the smallest next confirmation that could materially change it.

## Example triggers

- “我的理财目标结构应该是什么？”
- “审查这个现金、债券、股票和加密资产比例是否适合我的目标。”
- “把购房选择权和长期财务独立拆成目标组合。”
- “基于IPS给出目标区间和再平衡规则，但先不要选产品。”
