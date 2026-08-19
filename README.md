# Personal Finance Planning Core

Goal-based intake, financial-independence scenarios, allocation policy,
liquidity guidance, and confirmed planning state for agent hosts.

This repository is the canonical source for the `personal-finance-planner`
Plugin. The narrower product name is intentional: it provides a reusable
planning core, not a complete wealth adviser, product marketplace, portfolio
manager, or trading agent.

## Current scope

- progressive financial-profile intake;
- neutral goal clarification and conflict detection;
- deterministic planning-stage routing;
- financial-independence, milestone, and optional home-scenario calculators;
- target-allocation and cash-liquidity policy validation;
- explicitly confirmed external Workspace state;
- versioned professional and China-mainland public guidance;
- synthetic evaluations and no transaction execution tools.

Product selection, live account ingestion, tax or insurance advice, automatic
rebalancing, and financial transactions are outside the current scope.

## Repository layout

The Codex Marketplace manifest is `.agents/plugins/marketplace.json`. The
installable package remains at `plugins/personal-finance-planner/` so its
technical ID and MCP server name stay backward compatible.

## Local validation

```bash
python3 /path/to/plugin-creator/scripts/validate_plugin.py \
  plugins/personal-finance-planner

uv run --project plugins/personal-finance-planner/mcp \
  python -m unittest discover -s tests
```

The repository is currently a private release candidate. A Git repository or
version tag is not evidence of public Marketplace publication.

See `PRIVACY.md`, `SECURITY.md`, and the package README before distributing a
build.
