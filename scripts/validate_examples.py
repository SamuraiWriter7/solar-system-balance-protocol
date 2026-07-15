#!/usr/bin/env python3
"""Validate Solar System Balance Protocol schemas and examples."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]

AXIS_NAMES = (
    "coordination_strength",
    "audit_strength",
    "routing_strength",
    "resource_control",
    "emergency_authority",
)

SemanticValidator = Callable[[dict[str, Any]], list[str]]


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


def semantic_solar_core_state(
    record: dict[str, Any],
) -> list[str]:
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

    observation_window = record["system"].get(
        "observation_window"
    )

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


def semantic_orbital_node_definition(
    record: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    orbit = record["orbit"]
    orbit_class = orbit["orbit_class"]
    distance = float(orbit["distance_from_core"])
    binding = float(orbit["binding_strength"])
    autonomy = float(orbit["autonomy_level"])

    frequency = orbit["interaction_frequency"]
    frequency_mode = frequency["mode"]
    interval = int(frequency["nominal_interval_seconds"])

    relationship = record["core_relationship"]
    bound_functions = set(relationship["bound_functions"])
    local_functions = set(
        relationship["locally_governed_functions"]
    )

    overlap = bound_functions & local_functions

    if overlap:
        errors.append(
            "core_relationship.bound_functions and "
            "locally_governed_functions must not overlap: "
            f"{sorted(overlap)}"
        )

    transition = record["transition_policy"]
    target_orbits = set(transition["allowed_target_orbits"])

    if orbit_class in target_orbits:
        errors.append(
            "transition_policy.allowed_target_orbits "
            "must not include the node's current orbit"
        )

    zero_interval_modes = {
        "continuous",
        "event_driven",
        "none",
    }

    positive_interval_modes = {
        "high",
        "periodic",
        "low",
    }

    if (
        frequency_mode in zero_interval_modes
        and interval != 0
    ):
        errors.append(
            "interaction_frequency.nominal_interval_seconds "
            f"must be 0 when mode is {frequency_mode}"
        )

    if (
        frequency_mode in positive_interval_modes
        and interval <= 0
    ):
        errors.append(
            "interaction_frequency.nominal_interval_seconds "
            f"must be greater than 0 when mode is {frequency_mode}"
        )

    if orbit_class == "inner":
        if distance > 0.35:
            errors.append(
                "inner orbit distance_from_core "
                "must not exceed 0.35"
            )

        if binding < 0.6:
            errors.append(
                "inner orbit binding_strength "
                "must be at least 0.6"
            )

    if orbit_class == "middle":
        if not 0.25 <= distance <= 0.75:
            errors.append(
                "middle orbit distance_from_core "
                "must be between 0.25 and 0.75"
            )

    if orbit_class == "outer":
        if distance < 0.55:
            errors.append(
                "outer orbit distance_from_core "
                "must be at least 0.55"
            )

        if autonomy < 0.6:
            errors.append(
                "outer orbit autonomy_level "
                "must be at least 0.6"
            )

    if orbit_class == "comet":
        if frequency_mode != "event_driven":
            errors.append(
                "comet orbit must use event_driven interaction"
            )

        comet_profile = record.get("comet_profile")

        if not comet_profile:
            errors.append(
                "comet orbit requires comet_profile"
            )
        else:
            if not comet_profile["activation_triggers"]:
                errors.append(
                    "comet_profile.activation_triggers "
                    "must not be empty"
                )

            if comet_profile["active_window_seconds"] <= 0:
                errors.append(
                    "comet_profile.active_window_seconds "
                    "must be greater than 0"
                )

        if not (
            {"inner", "middle"} & target_orbits
        ):
            errors.append(
                "comet orbit must be able to approach "
                "inner or middle orbit"
            )

        if not transition["departure_triggers"]:
            errors.append(
                "comet orbit requires at least one "
                "departure trigger"
            )

        if not transition["return_conditions"]:
            errors.append(
                "comet orbit requires explicit "
                "return conditions"
            )

    if orbit_class == "dormant":
        operational_state = record["node"][
            "operational_state"
        ]

        if operational_state not in {
            "standby",
            "dormant",
        }:
            errors.append(
                "dormant orbit node must be in "
                "standby or dormant operational state"
            )

        if frequency_mode not in {
            "event_driven",
            "none",
        }:
            errors.append(
                "dormant orbit must use event_driven "
                "or none interaction mode"
            )

        if record["interaction_profile"][
            "peer_interaction_strength"
        ] > 0.25:
            errors.append(
                "dormant orbit peer_interaction_strength "
                "must not exceed 0.25"
            )

    if transition["transition_allowed"]:
        if not target_orbits:
            errors.append(
                "transition-enabled nodes require "
                "at least one allowed target orbit"
            )

        if not transition["approach_triggers"]:
            errors.append(
                "transition-enabled nodes require "
                "at least one approach trigger"
            )

        if not transition["departure_triggers"]:
            errors.append(
                "transition-enabled nodes require "
                "at least one departure trigger"
            )

        if not transition["return_conditions"]:
            errors.append(
                "transition-enabled nodes require "
                "at least one return condition"
            )

    else:
        if target_orbits:
            errors.append(
                "transition-disabled nodes must not "
                "define target orbits"
            )

    return errors


VALIDATION_TARGETS: tuple[
    tuple[str, Path, Path, SemanticValidator],
    ...
] = (
    (
        "Solar Core State Record",
        ROOT / "schemas" / "solar-core-state.schema.json",
        ROOT / "examples" / "solar-core-state.example.yaml",
        semantic_solar_core_state,
    ),
    (
        "Orbital Node Definition",
        ROOT / "schemas" / "orbital-node-definition.schema.json",
        ROOT / "examples" / "orbital-node-definition.example.yaml",
        semantic_orbital_node_definition,
    ),
)


def validate_target(
    name: str,
    schema_path: Path,
    example_path: Path,
    semantic_validator: SemanticValidator,
) -> list[str]:
    errors: list[str] = []

    print(f"[validate] {name}")
    print(f"  schema : {schema_path.relative_to(ROOT)}")
    print(f"  example: {example_path.relative_to(ROOT)}")

    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)

    print(f"[schema-ok] {name}")

    record = load_yaml(example_path)

    validator = Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    )

    schema_errors = sorted(
        validator.iter_errors(record),
        key=lambda error: list(error.absolute_path),
    )

    for error in schema_errors:
        errors.append(
            f"{format_path(error.absolute_path)}: "
            f"{error.message}"
        )

    if not schema_errors:
        errors.extend(semantic_validator(record))

    if errors:
        for error in errors:
            print(f"[error] {error}")
    else:
        print(f"[example-ok] {name}")

    print()

    return errors


def main() -> int:
    print("=== Solar System Balance Protocol Validation ===")
    print()

    all_errors: list[str] = []

    try:
        for (
            name,
            schema_path,
            example_path,
            semantic_validator,
        ) in VALIDATION_TARGETS:
            target_errors = validate_target(
                name,
                schema_path,
                example_path,
                semantic_validator,
            )

            all_errors.extend(
                f"{name}: {error}"
                for error in target_errors
            )

    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        yaml.YAMLError,
    ) as exc:
        print(f"[fatal] {exc}")
        return 1

    if all_errors:
        print(
            f"Validation failed with "
            f"{len(all_errors)} error(s)."
        )
        return 1

    print("All validations passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
