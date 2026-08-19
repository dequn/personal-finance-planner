"""Read-only validation for proposed and explicitly confirmed planning state."""

from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = PLUGIN_ROOT / "schemas"
SCHEMA_FILES = {
    ("profile", "proposed"): "financial-profile-proposal.schema.json",
    ("profile", "confirmed"): "financial-profile-confirmed.schema.json",
    ("goals", "proposed"): "financial-goals-proposal.schema.json",
    ("goals", "confirmed"): "financial-goals-confirmed.schema.json",
    ("allocation", "proposed"): "target-allocation-proposal.schema.json",
    ("allocation", "confirmed"): "target-allocation-confirmed.schema.json",
}

ASSET_DESTINATION_CATEGORIES = {
    "true_cash",
    "deposits_and_direct_sovereign",
    "other_fixed_income",
    "equity",
    "crypto_and_other_high_risk",
}
ALLOCATION_COLLECTION_IDS = {
    "goal_sleeves": "goal_sleeve_id",
    "hard_floors": "floor_id",
    "asset_destinations": "destination_id",
    "allocation_groups": "group_id",
    "maturity_overlay": "maturity_bucket_id",
    "liquidity_overlay": "liquidity_bucket_id",
}
GOAL_V02_CLASSIFICATION_FIELDS = {
    "goal_category",
    "goal_subtype",
    "outcome_type",
}

_FORBIDDEN_KEY_PATTERNS = (
    re.compile(r"(^|_)(account|bank_account|card)(_|$).*(number|no|id)$"),
    re.compile(r"(^|_)(government|identity|national|taxpayer)(_|$).*(number|no|id)$"),
    re.compile(
        r"(^|_)(password|passwd|passcode|pin|otp|api_key|access_token|refresh_token|cookie|session_cookie)(_|$)"
    ),
    re.compile(r"(^|_)(qr_code|device_identifier|device_id)(_|$)"),
)


def _schema(kind: str, state: str) -> dict[str, Any]:
    filename = SCHEMA_FILES[(kind, state)]
    return json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))


def schema_as_json(kind: str, state: str) -> str:
    """Return one public planning-state schema as formatted JSON."""
    return json.dumps(_schema(kind, state), ensure_ascii=False, indent=2)


def _path(parts: Any) -> str:
    return "$" + "".join(
        f"[{part}]" if isinstance(part, int) else f".{part}" for part in parts
    )


def _privacy_errors(value: Any, path: tuple[Any, ...] = ()) -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]+", "_", str(key).casefold()).strip("_")
            if any(pattern.search(normalized) for pattern in _FORBIDDEN_KEY_PATTERNS):
                errors.append(
                    f"{_path((*path, key))}: sensitive credential or identifier fields are forbidden"
                )
            errors.extend(_privacy_errors(child, (*path, key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_privacy_errors(child, (*path, index)))
    return errors


def _duplicate_errors(payload: dict[str, Any], kind: str) -> list[str]:
    collection = payload.get("facts" if kind == "profile" else "goals", [])
    key = "field_id" if kind == "profile" else "goal_id"
    ids = [item.get(key) for item in collection if isinstance(item, dict)]
    duplicates = sorted({item_id for item_id in ids if ids.count(item_id) > 1})
    if not duplicates:
        return []
    return [f"$.{key}s: duplicate stable IDs: {', '.join(duplicates)}"]


def _reference_errors(
    payload: dict[str, Any], kind: str, target_state: str
) -> list[str]:
    collection_name = "facts" if kind == "profile" else "goals"
    id_key = "field_id" if kind == "profile" else "goal_id"
    reference_key = "field_ids" if kind == "profile" else "goal_ids"
    items = payload.get(collection_name, [])
    known_ids = {
        item[id_key]
        for item in items
        if isinstance(item, dict) and isinstance(item.get(id_key), str)
    }
    errors: list[str] = []

    for index, conflict in enumerate(payload.get("conflicts", [])):
        if not isinstance(conflict, dict):
            continue
        unknown = sorted(set(conflict.get(reference_key, [])) - known_ids)
        if unknown:
            errors.append(
                f"$.conflicts[{index}].{reference_key}: unknown stable IDs: "
                f"{', '.join(unknown)}"
            )

    if target_state == "confirmed" and isinstance(payload.get("confirmation"), dict):
        scope = payload["confirmation"].get("scope", [])
        unknown = sorted(set(scope) - known_ids)
        if unknown:
            errors.append(
                "$.confirmation.scope: scope must contain known stable IDs; unknown: "
                f"{', '.join(unknown)}"
            )
    return errors


def _goal_range_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for index, goal in enumerate(payload.get("goals", [])):
        if not isinstance(goal, dict):
            continue
        amount = goal.get("amount")
        if isinstance(amount, dict) and amount.get("kind") == "range":
            minimum = amount.get("minimum")
            maximum = amount.get("maximum")
            if (
                isinstance(minimum, (int, float))
                and isinstance(maximum, (int, float))
                and minimum > maximum
            ):
                errors.append(f"$.goals[{index}].amount: minimum cannot exceed maximum")
        timing = goal.get("timing")
        if isinstance(timing, dict) and timing.get("kind") == "range":
            start_year = timing.get("start_year")
            end_year = timing.get("end_year")
            if (
                isinstance(start_year, int)
                and isinstance(end_year, int)
                and start_year > end_year
            ):
                errors.append(
                    f"$.goals[{index}].timing: start_year cannot exceed end_year"
                )
    return errors


def _goal_version_errors(payload: dict[str, Any]) -> list[str]:
    """Reject hybrid goal records whose fields do not match their version."""
    if payload.get("schema_version") != "0.1.0":
        return []

    errors: list[str] = []
    for index, goal in enumerate(payload.get("goals", [])):
        if not isinstance(goal, dict):
            continue
        unexpected = sorted(GOAL_V02_CLASSIFICATION_FIELDS & set(goal))
        if unexpected:
            errors.append(
                f"$.goals[{index}]: schema_version 0.1.0 cannot contain v0.2 "
                "classification fields: " + ", ".join(unexpected)
            )
    return errors


def _decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return Decimal(str(value))


def _allocation_items(
    payload: dict[str, Any], collection_name: str, id_key: str
) -> dict[str, dict[str, Any]]:
    return {
        item[id_key]: item
        for item in payload.get(collection_name, [])
        if isinstance(item, dict) and isinstance(item.get(id_key), str)
    }


def _allocation_duplicate_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    all_locations: dict[str, list[str]] = {}
    for collection_name, id_key in ALLOCATION_COLLECTION_IDS.items():
        ids = [
            item.get(id_key)
            for item in payload.get(collection_name, [])
            if isinstance(item, dict) and isinstance(item.get(id_key), str)
        ]
        duplicates = sorted({item_id for item_id in ids if ids.count(item_id) > 1})
        if duplicates:
            errors.append(
                f"$.{collection_name}: duplicate stable IDs: {', '.join(duplicates)}"
            )
        for item_id in ids:
            all_locations.setdefault(item_id, []).append(collection_name)

    cross_collection = sorted(
        item_id for item_id, locations in all_locations.items() if len(locations) > 1
    )
    if cross_collection:
        errors.append(
            "$: stable IDs must be unique across allocation collections: "
            + ", ".join(cross_collection)
        )
    return errors


def _allocation_reference_errors(
    payload: dict[str, Any], target_state: str
) -> list[str]:
    errors: list[str] = []
    destinations = _allocation_items(payload, "asset_destinations", "destination_id")
    goal_sleeves = _allocation_items(payload, "goal_sleeves", "goal_sleeve_id")
    all_ids: set[str] = set()
    for collection_name, id_key in ALLOCATION_COLLECTION_IDS.items():
        all_ids.update(_allocation_items(payload, collection_name, id_key))

    reference_specs = (
        ("goal_sleeves", "destination_ids", set(destinations)),
        ("hard_floors", "eligible_destination_ids", set(destinations)),
        ("asset_destinations", "linked_goal_sleeve_ids", set(goal_sleeves)),
        ("allocation_groups", "member_destination_ids", set(destinations)),
    )
    for collection_name, reference_key, known_ids in reference_specs:
        for index, item in enumerate(payload.get(collection_name, [])):
            if not isinstance(item, dict):
                continue
            references = item.get(reference_key, [])
            reference_ids = (
                {value for value in references if isinstance(value, str)}
                if isinstance(references, list)
                else set()
            )
            unknown = sorted(reference_ids - known_ids)
            if unknown:
                errors.append(
                    f"$.{collection_name}[{index}].{reference_key}: unknown stable IDs: "
                    + ", ".join(unknown)
                )

    for index, conflict in enumerate(payload.get("conflicts", [])):
        if not isinstance(conflict, dict):
            continue
        involved = conflict.get("involved_ids", [])
        involved_ids = (
            {value for value in involved if isinstance(value, str)}
            if isinstance(involved, list)
            else set()
        )
        unknown = sorted(involved_ids - all_ids)
        if unknown:
            errors.append(
                f"$.conflicts[{index}].involved_ids: unknown stable IDs: "
                + ", ".join(unknown)
            )

    if target_state == "confirmed" and isinstance(payload.get("confirmation"), dict):
        scope_value = payload["confirmation"].get("scope", [])
        scope = (
            {value for value in scope_value if isinstance(value, str)}
            if isinstance(scope_value, list)
            else set()
        )
        unknown = sorted(scope - all_ids)
        omitted = sorted(all_ids - scope)
        if unknown:
            errors.append(
                "$.confirmation.scope: unknown stable IDs: " + ", ".join(unknown)
            )
        if omitted:
            errors.append(
                "$.confirmation.scope: confirmed allocation must cover every stable ID; "
                "missing: " + ", ".join(omitted)
            )
    return errors


def _target_range_errors(
    item: dict[str, Any], path: str, *, require_central: bool
) -> list[str]:
    target_range = item.get("target_range")
    if not isinstance(target_range, dict):
        return []
    minimum = _decimal(target_range.get("minimum_pct"))
    central = _decimal(target_range.get("central_pct"))
    maximum = _decimal(target_range.get("maximum_pct"))
    errors: list[str] = []
    if minimum is not None and maximum is not None and minimum > maximum:
        errors.append(f"{path}.target_range: minimum_pct cannot exceed maximum_pct")
    if require_central and central is None:
        errors.append(f"{path}.target_range: central_pct is required when confirmed")
    if central is not None and minimum is not None and central < minimum:
        errors.append(f"{path}.target_range: central_pct cannot be below minimum_pct")
    if central is not None and maximum is not None and central > maximum:
        errors.append(f"{path}.target_range: central_pct cannot exceed maximum_pct")
    return errors


def _overlay_percentage_errors(
    payload: dict[str, Any], collection_name: str, target_state: str
) -> list[str]:
    items = [
        item for item in payload.get(collection_name, []) if isinstance(item, dict)
    ]
    errors: list[str] = []
    for index, item in enumerate(items):
        errors.extend(
            _target_range_errors(
                item,
                f"$.{collection_name}[{index}]",
                require_central=target_state == "confirmed",
            )
        )
    if target_state != "confirmed" or not items:
        return errors

    minimums = [
        _decimal(item.get("target_range", {}).get("minimum_pct")) for item in items
    ]
    centrals = [
        _decimal(item.get("target_range", {}).get("central_pct")) for item in items
    ]
    maximums = [
        _decimal(item.get("target_range", {}).get("maximum_pct")) for item in items
    ]
    if all(value is not None for value in (*minimums, *maximums)) and (
        sum(minimums, Decimal(0)) > 100 or sum(maximums, Decimal(0)) < 100
    ):
        errors.append(
            f"$.{collection_name}: percentage ranges must permit a complete 100% allocation"
        )
    if all(value is not None for value in centrals):
        total = sum(centrals, Decimal(0))
        if abs(total - Decimal(100)) > Decimal("0.01"):
            errors.append(
                f"$.{collection_name}: central_pct values must sum to 100; got {total}"
            )
    return errors


def _destination_errors(payload: dict[str, Any], target_state: str) -> list[str]:
    items = [
        item for item in payload.get("asset_destinations", []) if isinstance(item, dict)
    ]
    errors = _overlay_percentage_errors(payload, "asset_destinations", target_state)
    categories = [
        item["category"] for item in items if isinstance(item.get("category"), str)
    ]
    duplicates = sorted(
        {category for category in categories if categories.count(category) > 1}
    )
    if duplicates:
        errors.append(
            "$.asset_destinations: duplicate mutually exclusive categories: "
            + ", ".join(duplicates)
        )
    if target_state == "confirmed":
        missing = sorted(ASSET_DESTINATION_CATEGORIES - set(categories))
        extra = sorted(set(categories) - ASSET_DESTINATION_CATEGORIES)
        if missing or extra:
            errors.append(
                "$.asset_destinations: confirmed allocation must contain each canonical "
                "category exactly once; missing="
                + ",".join(missing)
                + "; extra="
                + ",".join(extra)
            )
    return errors


def _allocation_group_errors(
    payload: dict[str, Any], target_state: str
) -> list[str]:
    destinations = _allocation_items(payload, "asset_destinations", "destination_id")
    groups = [
        item for item in payload.get("allocation_groups", []) if isinstance(item, dict)
    ]
    allowed_categories = {
        "low_risk": {
            "true_cash",
            "deposits_and_direct_sovereign",
            "other_fixed_income",
        },
        "high_risk": {"equity", "crypto_and_other_high_risk"},
    }
    errors: list[str] = []
    for index, group in enumerate(groups):
        path = f"$.allocation_groups[{index}]"
        errors.extend(
            _target_range_errors(
                group,
                path,
                require_central=target_state == "confirmed",
            )
        )
        member_ids = [
            value
            for value in group.get("member_destination_ids", [])
            if isinstance(value, str) and value in destinations
        ]
        group_type = group.get("group_type")
        if group_type in allowed_categories:
            invalid_members = sorted(
                member_id
                for member_id in member_ids
                if destinations[member_id].get("category")
                not in allowed_categories[group_type]
            )
            if invalid_members:
                errors.append(
                    f"{path}.member_destination_ids: {group_type} group contains "
                    "incompatible destinations: " + ", ".join(invalid_members)
                )

        group_range = group.get("target_range")
        member_ranges = [
            destinations[member_id].get("target_range") for member_id in member_ids
        ]
        if not isinstance(group_range, dict) or not all(
            isinstance(item, dict) for item in member_ranges
        ):
            continue
        group_minimum = _decimal(group_range.get("minimum_pct"))
        group_central = _decimal(group_range.get("central_pct"))
        group_maximum = _decimal(group_range.get("maximum_pct"))
        member_minimums = [_decimal(item.get("minimum_pct")) for item in member_ranges]
        member_centrals = [_decimal(item.get("central_pct")) for item in member_ranges]
        member_maximums = [_decimal(item.get("maximum_pct")) for item in member_ranges]
        if all(value is not None for value in (*member_minimums, *member_maximums)):
            aggregate_minimum = sum(member_minimums, Decimal(0))
            aggregate_maximum = sum(member_maximums, Decimal(0))
            if (
                group_minimum is not None
                and group_minimum > aggregate_maximum
            ) or (
                group_maximum is not None and group_maximum < aggregate_minimum
            ):
                errors.append(
                    f"{path}.target_range: group range is infeasible for member "
                    "destination ranges"
                )
        if group_central is not None and all(
            value is not None for value in member_centrals
        ):
            aggregate_central = sum(member_centrals, Decimal(0))
            if abs(group_central - aggregate_central) > Decimal("0.01"):
                errors.append(
                    f"{path}.target_range.central_pct: must equal the sum of member "
                    f"central_pct values; expected {aggregate_central}"
                )
    return errors


def _denominator_and_amount_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    denominator = payload.get("denominator")
    if not isinstance(denominator, dict):
        return errors
    minimum = _decimal(denominator.get("minimum"))
    maximum = _decimal(denominator.get("maximum"))
    if denominator.get("value_kind") == "range" and (
        minimum is not None and maximum is not None and minimum > maximum
    ):
        errors.append("$.denominator: minimum cannot exceed maximum")

    denominator_value = (
        _decimal(denominator.get("value"))
        if denominator.get("value_kind") == "exact"
        else None
    )
    for index, destination in enumerate(payload.get("asset_destinations", [])):
        if not isinstance(destination, dict) or "target_amounts" not in destination:
            continue
        amounts = destination.get("target_amounts")
        target_range = destination.get("target_range")
        path = f"$.asset_destinations[{index}].target_amounts"
        if denominator_value is None:
            errors.append(f"{path}: requires an exact denominator value")
            continue
        if not isinstance(amounts, dict) or not isinstance(target_range, dict):
            continue
        if amounts.get("currency") != denominator.get("currency"):
            errors.append(f"{path}.currency: must match denominator currency")
        pairs = (
            ("minimum", "minimum_pct"),
            ("central", "central_pct"),
            ("maximum", "maximum_pct"),
        )
        for amount_key, percentage_key in pairs:
            amount = _decimal(amounts.get(amount_key))
            percentage = _decimal(target_range.get(percentage_key))
            if amount is None or percentage is None:
                errors.append(f"{path}.{amount_key}: requires numeric {percentage_key}")
                continue
            expected = denominator_value * percentage / Decimal(100)
            if abs(amount - expected) > Decimal("0.01"):
                errors.append(
                    f"{path}.{amount_key}: must equal denominator multiplied by "
                    f"{percentage_key}; expected {expected}"
                )
    return errors


def _hard_floor_errors(payload: dict[str, Any]) -> list[str]:
    destinations = _allocation_items(payload, "asset_destinations", "destination_id")
    errors: list[str] = []
    for index, floor in enumerate(payload.get("hard_floors", [])):
        if not isinstance(floor, dict) or floor.get("kind") != "emergency_cash":
            continue
        eligible = floor.get("eligible_destination_ids", [])
        eligible_ids = eligible if isinstance(eligible, list) else []
        if not eligible_ids:
            errors.append(
                f"$.hard_floors[{index}].eligible_destination_ids: emergency cash "
                "must identify a true-cash destination"
            )
            continue
        non_cash = sorted(
            destination_id
            for destination_id in eligible_ids
            if destination_id in destinations
            and destinations[destination_id].get("category") != "true_cash"
        )
        if non_cash:
            errors.append(
                f"$.hard_floors[{index}].eligible_destination_ids: emergency cash "
                "cannot rely on non-cash destinations: " + ", ".join(non_cash)
            )
    return errors


def _ordered_bucket_errors(
    payload: dict[str, Any], collection_name: str, target_state: str
) -> list[str]:
    items = [
        item for item in payload.get(collection_name, []) if isinstance(item, dict)
    ]
    if collection_name == "maturity_overlay":
        minimum_key, maximum_key = "minimum_days", "maximum_days"
    else:
        minimum_key, maximum_key = "ordinary_min_days", "ordinary_max_days"
    errors: list[str] = []
    prior_maximum: int | None = None
    open_ended_seen = False
    for index, item in enumerate(items):
        minimum = item.get(minimum_key)
        maximum = item.get(maximum_key)
        path = f"$.{collection_name}[{index}]"
        if isinstance(minimum, int) and isinstance(maximum, int) and minimum > maximum:
            errors.append(f"{path}: {minimum_key} cannot exceed {maximum_key}")
        if open_ended_seen:
            errors.append(f"{path}: no bucket may follow an open-ended bucket")
        if index and isinstance(minimum, int) and prior_maximum is not None:
            if minimum <= prior_maximum:
                errors.append(f"{path}: bucket ranges must not overlap")
            elif target_state == "confirmed" and minimum != prior_maximum + 1:
                errors.append(f"{path}: confirmed bucket ranges must not contain gaps")
        if maximum is None:
            open_ended_seen = True
            prior_maximum = None
        elif isinstance(maximum, int):
            prior_maximum = maximum

        if collection_name == "liquidity_overlay":
            stress = item.get("stress_max_days")
            if (
                isinstance(maximum, int)
                and isinstance(stress, int)
                and stress < maximum
            ):
                errors.append(
                    f"{path}.stress_max_days: cannot be shorter than ordinary_max_days"
                )
            if maximum is None and stress is not None:
                errors.append(
                    f"{path}.stress_max_days: must be null when ordinary_max_days is null"
                )

    if target_state == "confirmed" and items:
        if items[0].get(minimum_key) != 0:
            errors.append(f"$.{collection_name}: confirmed overlay must start at day 0")
        if items[-1].get(maximum_key) is not None:
            errors.append(f"$.{collection_name}: confirmed overlay must be open-ended")
        if collection_name == "maturity_overlay":
            cash_indexes = [
                index
                for index, item in enumerate(items)
                if item.get("includes_true_cash")
            ]
            if cash_indexes != [0]:
                errors.append(
                    "$.maturity_overlay: exactly the first bucket must include true cash"
                )
    return errors


def _allocation_semantic_errors(
    payload: dict[str, Any], target_state: str
) -> list[str]:
    errors = _allocation_duplicate_errors(payload)
    errors.extend(_allocation_reference_errors(payload, target_state))
    errors.extend(_destination_errors(payload, target_state))
    errors.extend(_allocation_group_errors(payload, target_state))
    errors.extend(_overlay_percentage_errors(payload, "maturity_overlay", target_state))
    errors.extend(
        _overlay_percentage_errors(payload, "liquidity_overlay", target_state)
    )
    errors.extend(_denominator_and_amount_errors(payload))
    errors.extend(_hard_floor_errors(payload))
    errors.extend(_ordered_bucket_errors(payload, "maturity_overlay", target_state))
    errors.extend(_ordered_bucket_errors(payload, "liquidity_overlay", target_state))
    return errors


def _validate(payload_json: str, *, kind: str, target_state: str) -> dict[str, Any]:
    schema_filename = SCHEMA_FILES.get((kind, target_state))
    if schema_filename is None:
        return {
            "valid": False,
            "schema": None,
            "errors": ["target_state must be proposed or confirmed"],
            "warnings": [],
        }

    try:
        payload = json.loads(payload_json)
    except json.JSONDecodeError as exc:
        return {
            "valid": False,
            "schema": schema_filename,
            "errors": [
                f"invalid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}"
            ],
            "warnings": [],
        }

    if not isinstance(payload, dict):
        return {
            "valid": False,
            "schema": schema_filename,
            "errors": ["$: payload must be a JSON object"],
            "warnings": [],
        }

    validator = Draft202012Validator(
        _schema(kind, target_state), format_checker=FormatChecker()
    )
    errors = [
        f"{_path(error.absolute_path)}: {error.message}"
        for error in sorted(
            validator.iter_errors(payload), key=lambda item: list(item.path)
        )
    ]
    errors.extend(_privacy_errors(payload))
    if kind == "allocation":
        errors.extend(_allocation_semantic_errors(payload, target_state))
    else:
        errors.extend(_duplicate_errors(payload, kind))
        errors.extend(_reference_errors(payload, kind, target_state))
        if kind == "goals":
            errors.extend(_goal_range_errors(payload))
            errors.extend(_goal_version_errors(payload))

    warnings: list[str] = []
    if kind == "allocation":
        categories = {
            item.get("category")
            for item in payload.get("asset_destinations", [])
            if isinstance(item, dict)
        }
        if target_state == "proposed" and categories != ASSET_DESTINATION_CATEGORIES:
            warnings.append(
                "The proposal does not yet cover all five mutually exclusive asset destinations."
            )
        if target_state == "confirmed" and payload.get("missing_inputs"):
            warnings.append(
                "Confirmed allocation still has missing inputs; keep blocked implementation decisions explicit."
            )
        if any(
            isinstance(item, dict) and item.get("policy_mode") == "ceiling_only"
            for collection_name in ("asset_destinations", "allocation_groups")
            for item in payload.get(collection_name, [])
        ):
            warnings.append(
                "A ceiling-only destination does not create an instruction to fund up to its reference value."
            )
        if any(
            isinstance(item, dict) and item.get("policy_mode") == "directional_range"
            for collection_name in ("asset_destinations", "allocation_groups")
            for item in payload.get(collection_name, [])
        ):
            warnings.append(
                "A directional range has no completion deadline and does not create a trade instruction."
            )
    else:
        if target_state == "proposed" and not payload.get(
            "facts" if kind == "profile" else "goals"
        ):
            warnings.append(
                "No facts or goals were supplied; continue progressive intake without inventing values."
            )
        if target_state == "confirmed" and payload.get("missing_fields"):
            warnings.append(
                "Confirmed scope still has missing fields; keep blocked decisions explicit."
            )

    return {
        "valid": not errors,
        "schema": schema_filename,
        "errors": errors,
        "warnings": warnings,
    }


def validate_financial_profile(payload_json: str, target_state: str) -> dict[str, Any]:
    """Validate profile state without persisting or confirming it."""
    return _validate(payload_json, kind="profile", target_state=target_state)


def validate_financial_goals(payload_json: str, target_state: str) -> dict[str, Any]:
    """Validate goal state without resolving conflicts or persisting it."""
    return _validate(payload_json, kind="goals", target_state=target_state)


def validate_target_allocation(payload_json: str, target_state: str) -> dict[str, Any]:
    """Validate proposed or confirmed target-allocation policy state."""
    return _validate(payload_json, kind="allocation", target_state=target_state)
