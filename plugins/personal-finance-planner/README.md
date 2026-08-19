# Personal Finance Planner Plugin

Personal Finance Planner packages a deterministic coordination entry plus reusable progressive profile intake, financial-goal clarification, confirmed Workspace state, financial-independence, target-allocation, and cash-liquidity workflows. Public guidance, canonical Prompt contracts, JSON Schemas, controlled state persistence, routing, validation, and deterministic calculators share one implementation source.

It does not contain personal holdings, goals, account records, credentials, product recommendations, or transaction tools. User-specific data is supplied at runtime or stored only in a user-selected external Workspace after explicit confirmation.

## Included capability

- Skills: `$run-financial-planning`, `$manage-financial-planning-workspace`, `$financial-profile-intake`, `$financial-goal-clarification`, `$plan-financial-independence`, and `$design-target-allocation`
- MCP Prompts: one coordinated session entry plus five specialist Prompts, each rendered from the same canonical contract used by its Skill
- MCP Tools: one deterministic stage router, three read-only profile/goal/allocation validators, three controlled Workspace-state Tools, and four deterministic FI and home-opportunity calculators
- MCP Resources: eleven FI source cards, thirteen professional and regulatory allocation/planning cards, two catalogs, eleven planning-state, Workspace-state, or route Schema Resources, and one versioned workflow registry
- JSON Schemas: session-route, proposed and confirmed profile/goal/target-allocation records, Workspace version/read/write, FI, annual-milestone, home-opportunity, and home-boundary contracts
- Synthetic session, profile, goal, Workspace, FI, home, allocation, and cash-liquidity eval cases with focused tests
- A shared six-persona P0 host-acceptance matrix covering debt, education and care, variable income, cross-jurisdiction currencies, retirement with unknown pension income, and optional primary-home planning
- Two three-turn P0.1 host conversations covering progressive profile intake and optional-versus-committed goal clarification with an explicit funding conflict
- Two P0.2 deterministic-calculator host cases covering FI milestones/progress and home price boundaries

Third-party PDFs are not vendored. The knowledge cards store canonical URLs, retrieval dates, bounded summaries, prompt rules, applicable claims, and limitations so that a host can cite or refresh the source without silently relying on a stale copy. The allocation cards distinguish professional standards, regulator education, asset-manager research, official jurisdictional rules, and practitioner examples.

For China-mainland portfolio design, the source set includes the cross-sector asset-management guidance, commercial-bank wealth supervision measures, and wealth-product liquidity-risk rules. The Prompt separates personal borrowing from product-internal leverage, keeps net-value wealth products outside the deterministic-anchor sleeve, and requires a user-approved product-level limit plus current evidence; it does not turn the regulatory 140-percent maximum into a universal safe threshold.

`$design-target-allocation` contains no universal default portfolio. It requires runtime facts and first separates goal sleeves, mutually exclusive asset destinations, and the maturity overlay. Its cash-liquidity contract further separates true cash, qualified cash-like operational liquidity, and near-cash while distinguishing contractual redemption from channel acceleration. Missing material inputs produce bounded alternatives or questions instead of invented ratios or cash floors.

`$financial-profile-intake` and `$financial-goal-clarification` use progressive disclosure: each round asks no more than three high-impact questions, preserves estimates and unknowns, and emits a `proposed` record. The `confirmed` gate requires explicit user confirmation of a named scope. The validators reject schema violations and sensitive credential or identifier fields.

New financial-goal output uses the jurisdiction-neutral `financial_goals` v0.2 contract. Each goal has a broad `goal_category`, an open stable-slug `goal_subtype`, and an `outcome_type`; a primary-home purchase is therefore one possible `major_purchase` subtype rather than a universal intake stage. FI planning now performs a short major-expense scan across housing, vehicles, education, care, business funding, and user-defined outlays, while keeping optional or exploratory expenses outside the baseline unless the user explicitly changes that policy. Existing v0.1 records remain valid, but v0.1/v0.2 hybrid records are rejected and no Workspace history is migrated automatically.

`$manage-financial-planning-workspace` stores only validator-accepted confirmed profile, goal, or target-allocation records. It requires an explicit absolute Workspace path, named confirmation for initialization and every write, and the exact parent version read before confirmation. One append-only SQLite database is the sole state authority; identical retries are idempotent and stale writes fail closed. Repository v0.1 can be migrated only through explicitly confirmed initialization. It does not discover private directories, dual-write sidecars, delete history, persist holdings or products, or authorize transactions.

`$design-target-allocation` now emits proposed and confirmed structured policy records. Its Validator keeps five canonical asset destinations mutually exclusive, verifies range ordering and 100% central-policy closure, checks exact-denominator amounts, validates stable-ID references and full confirmation scope, and independently closes maturity and reliable-liquidity overlays. `ceiling_only` remains a cap rather than a funding instruction. The structure contains no current holdings and produces no trade authorization.

`$run-financial-planning` is the default coordination entry. Its v0.2 deterministic router selects exactly one next stage, lets users discuss a provisional goal without completing a profile first, and requires confirmed, conflict-free profile and goal scopes before downstream work. In `auto`, it reads only validated neutral goal summaries and maps them through the versioned `planning://workflow-registry/v0.2.0`: retirement/independence, primary-home optionality, and safety/resilience may reach installed specialist workflows, while education, debt, care, other major purchases, and custom subtypes fall back to general goal-based allocation. Equal-priority specialist matches produce only the matched bounded choices; legacy v0.1 goals do not receive an invented FI/home menu. Optional goal-scoped progress can skip an explicitly completed analysis without being persisted. Workspace initialization, read, or save is routed only on explicit request; the coordinator never auto-saves merely because a record is confirmed.

## Local MCP smoke test

From this directory:

```bash
uv run --frozen --project mcp python mcp/server.py
```

The `.mcp.json` adapter uses a contained `./mcp/run-server` launcher with the Plugin root as its explicit working directory. The launcher keeps the installed Plugin code read-only, places the locked `uv` environment and cache in host-provided Plugin data storage when available, and falls back to an isolated temporary directory on hosts that do not provide it.

The reusable host cases live in `evals/host-acceptance-cases.yaml`. The
Project-side adapter first runs deterministic contracts and then starts isolated
read-only Codex processes:

```bash
uv run python scripts/run_plugin_host_acceptance.py --mode contract
uv run python scripts/run_plugin_host_acceptance.py --mode codex
uv run python scripts/run_plugin_multiturn_acceptance.py --mode contract
uv run python scripts/run_plugin_multiturn_acceptance.py --mode codex
uv run python scripts/run_plugin_calculator_acceptance.py --mode contract
uv run python scripts/run_plugin_calculator_acceptance.py --mode codex
```

Codex reports are written below the gitignored `data/reports/` tree. They contain
compact Tool and result evidence, not raw reasoning events or personal financial
data. Claude and Hermes adapters must reuse the same cases when implemented.

## Codex install

Install the public prerelease from its Git tag:

```bash
codex plugin marketplace add dequn/personal-finance-planner --ref v0.9.0-rc.1
codex plugin add personal-finance-planner@personal-finance-planner
```

For local development, replace `dequn/personal-finance-planner` with the
repository path and omit `--ref`. Start a new conversation after each install
or reinstall. The repo Marketplace is declared in
`.agents/plugins/marketplace.json`.

Codex CLI 0.147.0 host acceptance passed on 2026-08-09 for all six Skills with synthetic data: coordinated routing; profile intake and privacy rejection; goal clarification; FI and home-opportunity calculation; target allocation and cash-liquidity classification; and temporary Workspace initialization, confirmed-state persistence, idempotent retry, stale-parent rejection, and read-back. On 2026-08-11 the current build additionally passed the automated six-persona Planning Router v0.2 gate for debt, education and care, variable income, cross-jurisdiction currencies, retirement with unknown pension income, and optional primary-home planning. Every fresh Codex case made exactly one read-only Router call with exact fixture arguments and no state write or transaction action. Claude and Hermes remain unverified.

On 2026-08-12 build `0.8.1+codex.20260812042650` also passed both
three-turn P0.1 Codex conversations: progressive profile intake and neutral goal
clarification with optional home, committed retirement, and a shared-funding
conflict. All 102 deterministic assertions passed, including exact session
resume, cumulative known-key preservation, canonical proposal validation, no
confirmation or persistence, and exact session cleanup. This is in-session
continuity evidence, not durable cross-session state recovery.

On the same date build `0.8.1+codex.20260812074739` passed the two remaining
calculator host cases. FI milestone/progress and home price-boundary results each
made one exact read-only Tool call, matched the canonical deterministic oracle
and output Schema, and performed no state or transaction action. Invalid-input
and exhaustive parameter-space coverage remain deterministic/direct-protocol
rather than host-level evidence.

## Status

The six capability slices are `plugin_ready` after schema, routing, validation, deterministic calculation, Workspace lifecycle, MCP Prompt/Tool/Resource protocol, privacy, source-card, eval, and Skill validation. Codex is verified for the six Skill workflows exercised on the earlier build, Planning Router v0.2, the resumed profile-intake and goal-clarification conversations, and the current build's FI milestone/progress and home price-boundary calculators. `financial_goals` v0.2 now has standalone multi-turn Codex evidence in addition to the neutral classified summaries used by the Router gate. Claude and Hermes remain unverified; direct protocol tests do not silently upgrade another host or an unexercised Tool path.

Build `0.8.1+codex.20260819143344` additionally passed an isolated read-only
Codex smoke for FI intake with unknown major-expense status. It asked a single
neutral question across housing, vehicles, education, care, business funding,
and other outlays, then separated committed baseline treatment from optional
scenario treatment without calculating, persisting, or authorizing a
transaction. Arbitrary timed-outlay calculation remains explicitly deferred.
