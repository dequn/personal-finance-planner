"""Explicit-confirmation SQLite repository for confirmed planning state."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from personal_finance_planner.planning_state import (
    validate_financial_goals,
    validate_financial_profile,
    validate_target_allocation,
)

REPOSITORY_VERSION = "planning-workspace-0.2.0"
LEGACY_REPOSITORY_VERSION = "planning-workspace-0.1.0"
STORE_DIR_NAME = ".personal-finance-planner"
DATABASE_NAME = "planning-state.sqlite3"
STORE_RELATIVE_PATH = f"{STORE_DIR_NAME}/{DATABASE_NAME}"
PLUGIN_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_SCHEMA_FILES = {
    "version": "workspace-state-version.schema.json",
    "read": "workspace-state-read-output.schema.json",
    "write": "workspace-state-write-output.schema.json",
}
WORKSPACE_PROMPT_TEMPLATE = (
    PLUGIN_ROOT
    / "skills"
    / "manage-financial-planning-workspace"
    / "references"
    / "workspace-state-prompt.md"
)


def workspace_schema_as_json(schema_name: str) -> str:
    """Return a public Workspace repository schema as formatted JSON."""
    try:
        filename = WORKSPACE_SCHEMA_FILES[schema_name]
    except KeyError as exc:
        raise ValueError("schema_name must be version, read, or write") from exc
    payload = json.loads(
        (PLUGIN_ROOT / "schemas" / filename).read_text(encoding="utf-8")
    )
    if schema_name in {"read", "write"}:
        version_schema = json.loads(
            (PLUGIN_ROOT / "schemas" / WORKSPACE_SCHEMA_FILES["version"]).read_text(
                encoding="utf-8"
            )
        )
        version_definition = {
            key: value
            for key, value in version_schema.items()
            if key not in {"$schema", "$id", "title"}
        }

        def replace_version_reference(value: Any) -> Any:
            if isinstance(value, dict):
                return {
                    key: (
                        "#/$defs/version"
                        if key == "$ref"
                        and item == "workspace-state-version.schema.json"
                        else replace_version_reference(item)
                    )
                    for key, item in value.items()
                }
            if isinstance(value, list):
                return [replace_version_reference(item) for item in value]
            return value

        payload = replace_version_reference(payload)
        payload["$defs"] = {"version": version_definition}
    return json.dumps(payload, ensure_ascii=False, indent=2)


def render_workspace_state_prompt(
    *, workspace_context: str, operation_context: str
) -> str:
    """Render the same Workspace lifecycle contract used by the Skill."""
    workspace = workspace_context.strip() or (
        "No explicit Workspace path or repository inspection result was supplied."
    )
    operation = operation_context.strip() or (
        "No state operation was selected. Inspect before proposing initialization or a write."
    )
    return (
        WORKSPACE_PROMPT_TEMPLATE.read_text(encoding="utf-8")
        .replace("{{workspace_context}}", workspace)
        .replace("{{operation_context}}", operation)
    )


def _resolve_workspace_root(workspace_path: str) -> Path:
    raw = Path(workspace_path)
    if not raw.is_absolute():
        raise ValueError("workspace_path must be an explicit absolute path")
    if raw.is_symlink():
        raise ValueError("workspace_path itself cannot be a symbolic link")
    try:
        root = raw.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ValueError("workspace_path must already exist") from exc
    if not root.is_dir():
        raise ValueError("workspace_path must be a directory")
    if root == Path(root.anchor):
        raise ValueError(
            "filesystem root cannot be used as a financial-planning Workspace"
        )
    return root


def _store_paths(root: Path) -> tuple[Path, Path]:
    store_dir = root / STORE_DIR_NAME
    database_path = store_dir / DATABASE_NAME
    if store_dir.exists() and store_dir.is_symlink():
        raise ValueError("Workspace state directory cannot be a symbolic link")
    if database_path.exists() and database_path.is_symlink():
        raise ValueError("Workspace state database cannot be a symbolic link")
    return store_dir, database_path


def _connect(database_path: Path, *, read_only: bool = False) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    if read_only:
        connection.execute("PRAGMA query_only = ON")
    return connection


def _initialize_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS repository_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS state_versions (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            version_id TEXT NOT NULL UNIQUE,
            record_type TEXT NOT NULL CHECK (record_type IN ('profile', 'goals', 'allocation')),
            parent_version_id TEXT,
            committed_at TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            confirmation_scope_json TEXT NOT NULL,
            change_summary_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            FOREIGN KEY (parent_version_id) REFERENCES state_versions(version_id)
        );

        CREATE INDEX IF NOT EXISTS idx_state_versions_record_sequence
        ON state_versions(record_type, sequence DESC);
        """
    )
    connection.execute(
        "INSERT OR IGNORE INTO repository_metadata(key, value) VALUES (?, ?)",
        ("repository_version", REPOSITORY_VERSION),
    )


def _repository_version(database_path: Path) -> str | None:
    if not database_path.is_file():
        return None
    try:
        with closing(_connect(database_path, read_only=True)) as connection:
            row = connection.execute(
                "SELECT value FROM repository_metadata WHERE key = ?",
                ("repository_version",),
            ).fetchone()
            versions_table = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'state_versions'"
            ).fetchone()
    except sqlite3.Error as exc:
        raise ValueError(
            "Workspace state database is unreadable or incompatible"
        ) from exc
    if not row or not versions_table:
        raise ValueError("Workspace state database is unreadable or incompatible")
    version = row["value"]
    if version not in {LEGACY_REPOSITORY_VERSION, REPOSITORY_VERSION}:
        raise ValueError(f"Unsupported Workspace repository version: {version}")
    return version


def _migrate_legacy_repository(connection: sqlite3.Connection) -> None:
    """Upgrade the v0.1 profile/goals table to the allocation-aware contract."""
    connection.execute("BEGIN IMMEDIATE")
    connection.execute("ALTER TABLE state_versions RENAME TO state_versions_v01")
    connection.execute(
        """
        CREATE TABLE state_versions (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            version_id TEXT NOT NULL UNIQUE,
            record_type TEXT NOT NULL CHECK (record_type IN ('profile', 'goals', 'allocation')),
            parent_version_id TEXT,
            committed_at TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            confirmation_scope_json TEXT NOT NULL,
            change_summary_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            FOREIGN KEY (parent_version_id) REFERENCES state_versions(version_id)
        )
        """
    )
    connection.execute(
        """
        INSERT INTO state_versions(
            sequence,
            version_id,
            record_type,
            parent_version_id,
            committed_at,
            payload_sha256,
            confirmation_scope_json,
            change_summary_json,
            payload_json
        )
        SELECT
            sequence,
            version_id,
            record_type,
            parent_version_id,
            committed_at,
            payload_sha256,
            confirmation_scope_json,
            change_summary_json,
            payload_json
        FROM state_versions_v01
        ORDER BY sequence
        """
    )
    connection.execute("DROP TABLE state_versions_v01")
    connection.execute(
        """
        CREATE INDEX idx_state_versions_record_sequence
        ON state_versions(record_type, sequence DESC)
        """
    )
    connection.execute(
        "UPDATE repository_metadata SET value = ? WHERE key = ?",
        (REPOSITORY_VERSION, "repository_version"),
    )
    connection.commit()


def _write_result(
    *,
    operation: str,
    status: str,
    persisted: bool = False,
    current_version_id: str | None = None,
    version: dict[str, Any] | None = None,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "repository_version": REPOSITORY_VERSION,
        "operation": operation,
        "status": status,
        "persisted": persisted,
        "store_relative_path": STORE_RELATIVE_PATH,
        "current_version_id": current_version_id,
        "version": version,
        "errors": errors or [],
        "warnings": warnings or [],
    }


def initialize_planning_workspace(
    *, workspace_path: str, explicit_user_confirmation: bool
) -> dict[str, Any]:
    """Initialize an empty local repository only after explicit confirmation."""
    if not explicit_user_confirmation:
        return _write_result(
            operation="initialize",
            status="rejected",
            errors=["explicit_user_confirmation must be true before initialization"],
        )

    root = _resolve_workspace_root(workspace_path)
    store_dir, database_path = _store_paths(root)
    repository_version = _repository_version(database_path)
    if repository_version == REPOSITORY_VERSION:
        return _write_result(operation="initialize", status="already_initialized")
    if repository_version == LEGACY_REPOSITORY_VERSION:
        with closing(_connect(database_path)) as connection:
            _migrate_legacy_repository(connection)
        os.chmod(database_path, 0o600)
        return _write_result(operation="initialize", status="migrated")

    store_dir.mkdir(mode=0o700, exist_ok=True)
    os.chmod(store_dir, 0o700)
    with closing(_connect(database_path)) as connection:
        connection.execute("BEGIN IMMEDIATE")
        _initialize_schema(connection)
        connection.commit()
    os.chmod(database_path, 0o600)
    return _write_result(operation="initialize", status="initialized")


def _row_to_version(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "sequence": row["sequence"],
        "version_id": row["version_id"],
        "record_type": row["record_type"],
        "parent_version_id": row["parent_version_id"],
        "committed_at": row["committed_at"],
        "payload_sha256": row["payload_sha256"],
        "confirmation_scope": json.loads(row["confirmation_scope_json"]),
        "change_summary": json.loads(row["change_summary_json"]),
        "payload": json.loads(row["payload_json"]),
    }


def _current_row(
    connection: sqlite3.Connection, record_type: str
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT * FROM state_versions
        WHERE record_type = ?
        ORDER BY sequence DESC
        LIMIT 1
        """,
        (record_type,),
    ).fetchone()


def read_planning_workspace(
    *, workspace_path: str, history_limit: int = 20
) -> dict[str, Any]:
    """Read current confirmed records and immutable version history."""
    if history_limit < 0 or history_limit > 100:
        raise ValueError("history_limit must be between 0 and 100")
    root = _resolve_workspace_root(workspace_path)
    _, database_path = _store_paths(root)
    repository_version = _repository_version(database_path)
    if repository_version == LEGACY_REPOSITORY_VERSION:
        raise ValueError(
            "Workspace repository requires explicit initialization confirmation to migrate"
        )
    if repository_version != REPOSITORY_VERSION:
        return {
            "repository_version": REPOSITORY_VERSION,
            "initialized": False,
            "store_relative_path": STORE_RELATIVE_PATH,
            "current": {"profile": None, "goals": None, "allocation": None},
            "history": [],
        }

    with closing(_connect(database_path, read_only=True)) as connection:
        profile_row = _current_row(connection, "profile")
        goals_row = _current_row(connection, "goals")
        allocation_row = _current_row(connection, "allocation")
        history_rows = connection.execute(
            "SELECT * FROM state_versions ORDER BY sequence DESC LIMIT ?",
            (history_limit,),
        ).fetchall()
    return {
        "repository_version": REPOSITORY_VERSION,
        "initialized": True,
        "store_relative_path": STORE_RELATIVE_PATH,
        "current": {
            "profile": _row_to_version(profile_row) if profile_row else None,
            "goals": _row_to_version(goals_row) if goals_row else None,
            "allocation": _row_to_version(allocation_row) if allocation_row else None,
        },
        "history": [_row_to_version(row) for row in history_rows],
    }


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _stable_items(payload: dict[str, Any], record_type: str) -> dict[str, Any]:
    if record_type == "profile":
        collections = (("facts", "field_id"),)
    elif record_type == "goals":
        collections = (("goals", "goal_id"),)
    else:
        collections = (
            ("goal_sleeves", "goal_sleeve_id"),
            ("hard_floors", "floor_id"),
            ("asset_destinations", "destination_id"),
            ("maturity_overlay", "maturity_bucket_id"),
            ("liquidity_overlay", "liquidity_bucket_id"),
        )
    stable_items: dict[str, Any] = {}
    for collection_name, id_name in collections:
        stable_items.update(
            {
                item[id_name]: item
                for item in payload.get(collection_name, [])
                if isinstance(item, dict) and isinstance(item.get(id_name), str)
            }
        )
    return stable_items


def _change_summary(
    previous_payload: dict[str, Any] | None,
    payload: dict[str, Any],
    record_type: str,
) -> dict[str, list[str]]:
    previous = _stable_items(previous_payload or {}, record_type)
    current = _stable_items(payload, record_type)
    shared = set(previous) & set(current)
    return {
        "added_ids": sorted(set(current) - set(previous)),
        "changed_ids": sorted(
            item_id
            for item_id in shared
            if _canonical_json(previous[item_id]) != _canonical_json(current[item_id])
        ),
        "removed_ids": sorted(set(previous) - set(current)),
    }


def _validated_payload(
    payload_json: str, record_type: str
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    validators = {
        "profile": validate_financial_profile,
        "goals": validate_financial_goals,
        "allocation": validate_target_allocation,
    }
    validator = validators[record_type]
    validation = validator(payload_json, "confirmed")
    if not validation["valid"]:
        return None, validation
    return json.loads(payload_json), validation


def persist_confirmed_state(
    *,
    workspace_path: str,
    record_type: str,
    payload_json: str,
    expected_parent_version_id: str | None,
    explicit_user_confirmation: bool,
) -> dict[str, Any]:
    """Append one confirmed planning-state version with optimistic concurrency."""
    if record_type not in {"profile", "goals", "allocation"}:
        raise ValueError("record_type must be profile, goals, or allocation")
    if not explicit_user_confirmation:
        return _write_result(
            operation="persist",
            status="rejected",
            errors=["explicit_user_confirmation must be true for this named write"],
        )

    payload, validation = _validated_payload(payload_json, record_type)
    if payload is None:
        return _write_result(
            operation="persist",
            status="rejected",
            errors=validation["errors"],
            warnings=validation["warnings"],
        )

    root = _resolve_workspace_root(workspace_path)
    _, database_path = _store_paths(root)
    repository_version = _repository_version(database_path)
    if repository_version == LEGACY_REPOSITORY_VERSION:
        return _write_result(
            operation="persist",
            status="rejected",
            errors=[
                "Workspace repository requires explicit initialization confirmation to migrate"
            ],
        )
    if repository_version != REPOSITORY_VERSION:
        return _write_result(
            operation="persist",
            status="rejected",
            errors=["Workspace repository is not initialized"],
        )

    canonical_payload = _canonical_json(payload)
    payload_sha256 = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
    with closing(_connect(database_path)) as connection:
        connection.execute("BEGIN IMMEDIATE")
        current_row = _current_row(connection, record_type)
        current_version_id = current_row["version_id"] if current_row else None
        if current_row and current_row["payload_sha256"] == payload_sha256:
            connection.rollback()
            return _write_result(
                operation="persist",
                status="already_persisted",
                current_version_id=current_version_id,
                version=_row_to_version(current_row),
                warnings=validation["warnings"],
            )
        if current_version_id != expected_parent_version_id:
            connection.rollback()
            return _write_result(
                operation="persist",
                status="conflict",
                current_version_id=current_version_id,
                errors=[
                    (
                        "expected_parent_version_id does not match the current version; "
                        "re-read and reconcile before asking for confirmation again"
                    )
                ],
                warnings=validation["warnings"],
            )

        previous_payload = (
            json.loads(current_row["payload_json"]) if current_row else None
        )
        change_summary = _change_summary(previous_payload, payload, record_type)
        version_material = _canonical_json(
            {
                "record_type": record_type,
                "parent_version_id": expected_parent_version_id,
                "payload_sha256": payload_sha256,
            }
        )
        version_hash = hashlib.sha256(version_material.encode("utf-8")).hexdigest()
        version_id = f"{record_type}-{version_hash[:24]}"
        committed_at = datetime.now(UTC).isoformat()
        confirmation_scope = payload["confirmation"]["scope"]
        try:
            connection.execute(
                """
                INSERT INTO state_versions(
                    version_id,
                    record_type,
                    parent_version_id,
                    committed_at,
                    payload_sha256,
                    confirmation_scope_json,
                    change_summary_json,
                    payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    record_type,
                    expected_parent_version_id,
                    committed_at,
                    payload_sha256,
                    _canonical_json(confirmation_scope),
                    _canonical_json(change_summary),
                    canonical_payload,
                ),
            )
            row = connection.execute(
                "SELECT * FROM state_versions WHERE version_id = ?", (version_id,)
            ).fetchone()
            connection.commit()
        except sqlite3.IntegrityError:
            connection.rollback()
            existing = connection.execute(
                "SELECT * FROM state_versions WHERE version_id = ?", (version_id,)
            ).fetchone()
            if existing:
                return _write_result(
                    operation="persist",
                    status="already_persisted",
                    current_version_id=existing["version_id"],
                    version=_row_to_version(existing),
                    warnings=validation["warnings"],
                )
            raise

    version = _row_to_version(row)
    return _write_result(
        operation="persist",
        status="persisted",
        persisted=True,
        current_version_id=version_id,
        version=version,
        warnings=validation["warnings"],
    )
