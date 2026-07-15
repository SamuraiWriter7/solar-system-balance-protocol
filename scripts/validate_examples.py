#!/usr/bin/env python3
"""Validate Solar System Balance Protocol schemas and examples."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_PATH = ROOT / "schemas" / "solar-core-state.schema.json"
EXAMPLE_PATH = ROOT / "examples" / "solar-core-state.example.yaml"

AXIS_NAMES = (
    "coordination_strength",
    "audit_strength",
    "routing_strength",
    "resource_control",
    "emergency_authority",
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError(
            f"{path.name} must contain a YAML object at the root."
        )

    return data


def format_path(error_path: Any) -> str:
    parts = [str(part) for part in error_path]
    return ".".join(parts) if parts else "<root>"


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def semantic_errors(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    core = record["solar_core_state"]
    aggregate = core["aggregate_breathing_index"]
    axes = core["axes"]
    weights = aggregate["weights"]

    weight_sum = sum(
        float(weights[name])
        for name in AXIS_NAMES
    )

    if abs(weight_sum - 1.0) > 1e-9:
        errors.append(
            "solar_core_state.aggregate_breathing_index.weights "
            f"must sum to 1.0; got {weight_sum:.12f}"
        )

    calculated = sum(
        float(axes[name]) * float(weights[name])
        for name in AXIS_NAMES
    )

    declared = float(aggregate["value"])

    if abs(calculated - declared) > 1e-6:
        errors.append(
            "solar_core_state.aggregate_breathing_index.value "
            f"must equal the weighted mean; declared {declared:.6f}, "
            f"calculated {calculated:.6f}"
        )

    scope = core["centrality_scope"]

    scope_sets = {
        key: set(scope[key])
        for key in (
            "strengthened_functions",
            "preserved_distributed_functions",
            "restricted_functions",
        )
    }

    scope_keys = list(scope_sets)

    for index, left_key in enumerate(scope_keys):
        for right_key in scope_keys[index + 1:]:
            overlap = scope_sets[left_key] & scope_sets[right_key]

            if overlap:
                errors.append(
                    "centrality_scope entries must be mutually exclusive; "
                    f"{left_key} and {right_key} overlap: "
                    f"{sorted(overlap)}"
                )

    observation_window = record["system"].get("observation_window")

    if observation_window:
        started_at = parse_datetime(
            observation_window["started_at"]
        )
        ended_at = parse_datetime(
            observation_window["ended_at"]
        )

        if ended_at < started_at:
            errors.append(
                "system.observation_window.ended_at "
                "must not precede started_at"
            )

    reversibility = record["reversibility"]
    expires_at = reversibility.get("expires_at")

    if expires_at is not None:
        created_at = parse_datetime(record["created_at"])
        expiry = parse_datetime(expires_at)

        if expiry <= created_at:
            errors.append(
                "reversibility.expires_at "
                "must be later than created_at"
            )

    if (
        core["mode"] == "emergency"
        and not reversibility["reversible"]
    ):
        errors.append(
            "emergency mode must remain reversible"
        )

    return errors


def main() -> int:
    print("=== Solar System Balance Protocol Validation ===")
    print()
    print("[validate] Solar Core State Record")
    print(f"  schema : {SCHEMA_PATH.relative_to(ROOT)}")
    print(f"  example: {EXAMPLE_PATH.relative_to(ROOT)}")

    try:
        schema = load_json(SCHEMA_PATH)

        Draft202012Validator.check_schema(schema)

        print("[schema-ok] Solar Core State Record")

        record = load_yaml(EXAMPLE_PATH)

        validator = Draft202012Validator(
            schema,
            format_checker=FormatChecker(),
        )

        validation_errors = sorted(
            validator.iter_errors(record),
            key=lambda error: list(error.absolute_path),
        )

        if validation_errors:
            for error in validation_errors:
                print(
                    f"[error] "
                    f"{format_path(error.absolute_path)}: "
                    f"{error.message}"
                )

            return 1

        extra_errors = semantic_errors(record)

        if extra_errors:
            for error in extra_errors:
                print(f"[error] {error}")

            return 1

        print("[example-ok] Solar Core State Record")
        print()
        print("All validations passed.")

        return 0

    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        yaml.YAMLError,
    ) as exc:
        print(f"[fatal] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
