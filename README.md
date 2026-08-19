# Personal Finance Planner

English | [简体中文](README.zh-CN.md)

Personal Finance Planner is a privacy-first Plugin for agent hosts such
as Codex, Claude, and Hermes. It turns a financial profile, goals, and
constraints into structured planning state, deterministic calculations, and
reviewable allocation guidance.

Its scope is intentionally bounded. This is a reusable planning Plugin, not a
wealth adviser, product marketplace, portfolio manager, brokerage connector,
or trading agent.

## Privacy first: personal data stays local

**All personal financial data persisted by this Plugin stays in a local
Workspace explicitly selected by the user.** The Plugin has no telemetry or
remote personal-data store, does not discover private folders, and does not
package local Workspace data into releases.

When asset information is needed, provide only the planning facts required to
describe the asset position, for example:

- asset category and approximate amount or range;
- currency, liquidity, maturity, and observation date;
- planning goal, time horizon, risk constraint, and confirmed status;
- source or provenance needed to distinguish confirmed facts from estimates.

Never provide or store:

- passwords, passcodes, one-time verification codes, or security answers;
- full bank, brokerage, card, or payment account numbers;
- API keys, access tokens, cookies, private keys, or recovery phrases;
- government identification numbers or unnecessary identity documents;
- raw statements, screenshots, or exports containing personal identifiers.

Use masked institution labels and partial identifiers only when they are truly
needed to distinguish two assets. The Plugin does not need login credentials
or account access to build a financial plan.

> **Host boundary:** local persistence does not automatically mean that every
> conversation is processed locally. If this Plugin runs through a cloud-hosted
> model, text sent to that host may be processed under the host and model
> provider's privacy policy. Do not paste secrets into prompts. End-to-end local
> processing requires a local agent runtime and local model in addition to this
> local Workspace.

See [PRIVACY.md](PRIVACY.md) and [SECURITY.md](SECURITY.md) for the release and
security boundaries.

## What it provides

- progressive financial-profile intake;
- neutral goal clarification and conflict detection;
- deterministic planning-stage routing;
- financial-independence, milestone, and optional home-scenario calculators;
- target-allocation and cash-liquidity policy validation;
- explicitly confirmed local Workspace state;
- versioned professional and China-mainland public guidance;
- synthetic evaluations and no transaction-execution tools.

Product selection, live account ingestion, tax or insurance advice, automatic
rebalancing, and financial transactions are outside the current scope.

## Data and safety model

```text
User-provided planning facts
          |
          v
Agent host + Plugin Skills
          |
          v
Deterministic MCP validation/calculation
          |
          v
User confirmation -> local Workspace
```

- Prompts and Skills may propose or clarify information.
- Deterministic tools validate calculations and structured state.
- Confirmed state is written only after explicit user confirmation.
- The Plugin exposes no tools for trading, redemption, subscription, foreign
  exchange, leverage, credential collection, or automatic money movement.

## Repository layout

```text
.agents/plugins/marketplace.json        # local Marketplace metadata
plugins/personal-finance-planner/       # installable Plugin package
  skills/                               # reusable planning workflows
  mcp/                                  # deterministic tools and resources
  schemas/                              # structured contracts
  knowledge/                            # versioned public knowledge cards
  evals/                                # synthetic evaluation cases
tests/                                  # repository smoke tests
```

The user-facing name is **Personal Finance Planner**. The technical
Plugin ID and MCP server ID remain `personal-finance-planner` for compatibility.

## Local validation

```bash
python3 /path/to/plugin-creator/scripts/validate_plugin.py \
  plugins/personal-finance-planner

uv run --project plugins/personal-finance-planner/mcp \
  python -m unittest discover -s tests
```

Every release candidate must also pass fixture classification, prohibited-data,
symlink, secret, package-boundary, and staged-diff privacy checks.

## Install in Codex

Add this repository as a Git Marketplace at the release tag, then install the
Plugin:

```bash
codex plugin marketplace add dequn/personal-finance-planner --ref v0.9.0-rc.1
codex plugin add personal-finance-planner@personal-finance-planner
```

Start a new Codex conversation after installation. The repository is a
Git-hosted Codex Marketplace; it is not listed in an OpenAI-operated central
Plugin directory.

## Release status

`v0.9.0-rc.1` is the first public prerelease. Codex installation is verified;
Claude and Hermes packaging is present but has not yet passed host acceptance.
Review the privacy and security documents before distributing or deploying a
build.

This Plugin supports planning and education. It does not provide individualized
regulated financial advice and does not authorize any transaction.

Licensed under the [Apache License 2.0](LICENSE).
