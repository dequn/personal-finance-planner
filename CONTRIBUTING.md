# Contributing

Personal Finance Planner accepts reusable, contract-stable financial-planning
capabilities that preserve its privacy and safety boundaries.

## Data and privacy

- Use synthetic fixtures only.
- Do not submit identities, holdings, balances, transactions, account numbers,
  statements, screenshots, credentials, Workspace databases, or host traces.
- Keep examples jurisdiction-neutral unless a capability explicitly belongs to
  a versioned regional knowledge pack.
- Do not add tools that trade, redeem, subscribe, convert currency, borrow, use
  leverage, collect credentials, or move money.

If a vulnerability report needs sensitive evidence, follow
[SECURITY.md](SECURITY.md) and do not open a public issue.

## Development checks

From the repository root, run:

```bash
uv run --project plugins/personal-finance-planner/mcp \
  python -m unittest discover -s tests
sha256sum -c release/manifest.sha256
git diff --check
```

Changes to Skills, MCP interfaces, schemas, knowledge, or persistence contracts
must include focused synthetic contract coverage. A host is marked verified only
after a real host smoke test; passing direct protocol tests is not cross-host
evidence.

By submitting a contribution, you agree that it is licensed under the Apache
License 2.0.
