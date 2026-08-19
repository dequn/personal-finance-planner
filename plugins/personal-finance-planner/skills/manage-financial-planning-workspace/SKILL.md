---
name: manage-financial-planning-workspace
description: Initialize, inspect, resume, and explicitly persist confirmed financial profile, goal, or target-allocation state in a user-selected external Workspace. Use when a user asks to save confirmed planning information, continue from a prior session, inspect planning-state versions, migrate a supported repository version, or resolve a stale-write conflict. Do not use it to save proposals, collect credentials, discover private files automatically, delete history, package personal data into the Plugin, or authorize financial transactions.
---

# Manage Financial Planning Workspace

## Purpose

Maintain one portable, auditable planning-state repository outside the Plugin while preventing silent writes and stale-session overwrites.

## Workflow

1. Read `references/workspace-state-prompt.md` completely and treat it as the canonical state-lifecycle contract.
2. Require an explicit absolute Workspace path. Never discover, guess, or scan for a user's financial directory.
3. Inspect the Workspace before any state operation. If it is uninitialized, explain the exact hidden store that initialization will create and request explicit confirmation.
4. Read current profile and goal versions before proposing a write. Preserve the returned `version_id` as `expected_parent_version_id`.
5. Resolve confirmed Schemas through MCP Resources on server `personal-finance-planner`: profile=`planning://schemas/financial-profile-confirmed`, goals=`planning://schemas/financial-goals-confirmed`, allocation=`planning://schemas/target-allocation-confirmed`. If Resource access is unavailable, use the matching Plugin-root file under `schemas/` (from this Skill directory: `../../schemas/`). Use filenames ending in `-proposal.schema.json` for unconfirmed records and `-confirmed.schema.json` for confirmed records; never guess `-proposed.schema.json`.
6. Validate the payload against the matching confirmed profile, goal, or target-allocation Schema. Reject proposed state, invalid allocation arithmetic or references, unresolved conflicts, missing confirmation scope, and sensitive credential or identifier fields.
7. Show the record type, confirmation scope, current parent version, and stable-ID change summary before requesting write confirmation.
8. Call `persist_confirmed_financial_state` only after the user explicitly confirms that named write. Pass the exact parent version read in this session.
9. After persistence, read the Workspace again and verify that the new version is current. Report the immutable version ID and remaining unknowns.

## Repository contract

- Use one SQLite database at `.personal-finance-planner/planning-state.sqlite3` under the user-selected Workspace.
- Treat the database as the sole writable planning-state authority. Do not dual-write YAML, JSON, or Markdown copies.
- Append immutable profile, goal, and target-allocation versions. Do not update or delete prior versions.
- Use optimistic concurrency. A missing or stale expected parent must fail closed when a current version exists.
- Treat a repeated identical write as idempotent, not as a second version.
- Restore an older state only by explicitly confirming it as a new version; never move history pointers silently.

## Safety boundaries

- Initialization and persistence are local data writes, not financial transactions. Require explicit confirmation for each.
- Do not store account numbers, card numbers, government identity numbers, passwords, passcodes, OTPs, API keys, tokens, cookies, QR codes, or device identifiers.
- Do not persist holdings, product facts, transaction proposals, general policy, or decision journals. Target allocation is allowed only through its dedicated confirmed Schema and Validator.
- Do not delete the database, versions, or the user Workspace.
- Do not imply that confirmed planning state authorizes a trade, redemption, subscription, FX action, loan, or leverage.

## Output order

1. Workspace initialization and current-version status.
2. Requested read or write operation.
3. Validation and stable-ID change summary.
4. Explicit confirmation or concurrency boundary.
5. Resulting immutable version ID and verification.
6. Remaining unknowns, next planning capability, and transaction boundary.
