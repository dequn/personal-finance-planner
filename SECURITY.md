# Security

## Supported status

The current `0.9.0-rc.1` line is a private release candidate. Security fixes may
change its contracts before a stable release.

## Safety boundary

The Plugin does not expose tools for trading, redemption, subscription, foreign
exchange, leverage, credential collection, or automatic movement of money.
State writes require validated confirmed records, a user-selected external
Workspace, explicit confirmation, and optimistic concurrency checks.

Do not include credentials, account exports, statements, screenshots, personal
Workspace files, or host session logs in an issue or commit. Report a suspected
vulnerability privately to the repository owner with the smallest reproducible
synthetic case.
