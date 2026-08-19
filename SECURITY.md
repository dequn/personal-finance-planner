# Security

## Supported status

The current `0.9.0-rc.1` line is a public prerelease. Security fixes may change
its contracts before a stable release.

## Safety boundary

The Plugin does not expose tools for trading, redemption, subscription, foreign
exchange, leverage, credential collection, or automatic movement of money.
State writes require validated confirmed records, a user-selected external
Workspace, explicit confirmation, and optimistic concurrency checks.

Do not include credentials, account exports, statements, screenshots, personal
Workspace files, or host session logs in an issue or commit. Report a suspected
vulnerability through GitHub private vulnerability reporting when available,
or contact the repository owner privately with the smallest reproducible
synthetic case. Do not open a public issue containing sensitive evidence.
