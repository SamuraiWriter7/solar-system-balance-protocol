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

AXES = (
    "coordination_strength",
    "audit_strength",
    "routing_strength",
    "resource_control",
    "emergency_authority",
)

INTERACTION_FAMILY = {
    "resonance": "attractive",
    "resource_pull": "attractive",
    "synchronization": "attractive",
    "conflict": "repulsive",
    "repulsion": "repulsive",
    "evidence_exchange": "exchange",
    "trace_handoff": "exchange",
}

SemanticValidator = Callable[[dict[str, Any]], list[str]]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(value, dict):
        raise ValueError(
            f"{path.name} must contain a root object."
        )

    return value


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )


def format_path(path: Any) -> str:
    parts = [str(part) for part in path]
    return ".".join(parts) if parts else "<root>"


def add_overlap_error(
    errors: list[str],
    left_name: str,
    left_values: list[str],
    right_name: str,
    right_values: list[str],
) -> None:
    overlap = set(left_values) & set(right_values)

    if overlap:
        errors.append(
            f"{left_name} and {right_name} "
            f"must not overlap: {sorted(overlap)}"
        )


def validate_solar_core(
    record: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    core = record["solar_core_state"]
    aggregate = core["aggregate_breathing_index"]
    axes = core["axes"]
    weights = aggregate["weights"]

    weight_sum = sum(
        float(weights[name])
        for name in AXES
    )

    if abs(weight_sum - 1.0) > 1e-9:
        errors.append(
            "aggregate breathing weights must sum to 1.0; "
            f"got {weight_sum:.12f}"
        )

    calculated = sum(
        float(axes[name]) * float(weights[name])
        for name in AXES
    )

    declared = float(aggregate["value"])

    if abs(calculated - declared) > 1e-6:
        errors.append(
            "aggregate breathing index must equal "
            "the weighted mean; "
            f"declared {declared:.6f}, "
            f"calculated {calculated:.6f}"
        )

    scope = core["centrality_scope"]

    names = (
        "strengthened_functions",
        "preserved_distributed_functions",
        "restricted_functions",
    )

    for index, left in enumerate(names):
        for right in names[index + 1:]:
            add_overlap_error(
                errors,
                f"centrality_scope.{left}",
                scope[left],
                f"centrality_scope.{right}",
                scope[right],
            )

    window = record["system"].get(
        "observation_window"
    )

    if window:
        if parse_datetime(
            window["ended_at"]
        ) < parse_datetime(
            window["started_at"]
        ):
            errors.append(
                "observation_window.ended_at "
                "must not precede started_at"
            )

    reversibility = record["reversibility"]
    expires_at = reversibility.get("expires_at")

    if expires_at:
        if parse_datetime(
            expires_at
        ) <= parse_datetime(
            record["created_at"]
        ):
            errors.append(
                "reversibility.expires_at "
                "must follow created_at"
            )

    if (
        core["mode"] == "emergency"
        and not reversibility["reversible"]
    ):
        errors.append(
            "emergency mode must remain reversible"
        )

    return errors


def validate_orbital_node(
    record: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    orbit = record["orbit"]
    orbit_class = orbit["orbit_class"]
    distance = float(
        orbit["distance_from_core"]
    )
    binding = float(
        orbit["binding_strength"]
    )
    autonomy = float(
        orbit["autonomy_level"]
    )

    frequency = orbit["interaction_frequency"]
    mode = frequency["mode"]
    interval = int(
        frequency["nominal_interval_seconds"]
    )

    relationship = record["core_relationship"]

    add_overlap_error(
        errors,
        "core_relationship.bound_functions",
        relationship["bound_functions"],
        "core_relationship.locally_governed_functions",
        relationship["locally_governed_functions"],
    )

    transition = record["transition_policy"]
    targets = set(
        transition["allowed_target_orbits"]
    )

    if orbit_class in targets:
        errors.append(
            "allowed_target_orbits "
            "must not include current orbit"
        )

    if (
        mode in {
            "continuous",
            "event_driven",
            "none",
        }
        and interval != 0
    ):
        errors.append(
            f"{mode} interaction must use interval 0"
        )

    if (
        mode in {
            "high",
            "periodic",
            "low",
        }
        and interval <= 0
    ):
        errors.append(
            f"{mode} interaction must use "
            "a positive interval"
        )

    if orbit_class == "inner":
        if distance > 0.35:
            errors.append(
                "inner orbit distance "
                "must not exceed 0.35"
            )

        if binding < 0.6:
            errors.append(
                "inner orbit binding "
                "must be at least 0.6"
            )

    if (
        orbit_class == "middle"
        and not 0.25 <= distance <= 0.75
    ):
        errors.append(
            "middle orbit distance must be "
            "between 0.25 and 0.75"
        )

    if orbit_class == "outer":
        if distance < 0.55:
            errors.append(
                "outer orbit distance "
                "must be at least 0.55"
            )

        if autonomy < 0.6:
            errors.append(
                "outer orbit autonomy "
                "must be at least 0.6"
            )

    if orbit_class == "comet":
        profile = record.get("comet_profile")

        if mode != "event_driven":
            errors.append(
                "comet orbit must use "
                "event_driven interaction"
            )

        if not profile:
            errors.append(
                "comet orbit requires comet_profile"
            )

        elif (
            not profile["activation_triggers"]
            or profile["active_window_seconds"] <= 0
        ):
            errors.append(
                "comet_profile must define "
                "triggers and active window"
            )

        if not (
            {"inner", "middle"} & targets
        ):
            errors.append(
                "comet orbit must approach "
                "inner or middle orbit"
            )

        if not transition["departure_triggers"]:
            errors.append(
                "comet orbit requires "
                "departure triggers"
            )

        if not transition["return_conditions"]:
            errors.append(
                "comet orbit requires "
                "return conditions"
            )

    if orbit_class == "dormant":
        state = record["node"][
            "operational_state"
        ]

        if state not in {
            "standby",
            "dormant",
        }:
            errors.append(
                "dormant orbit must be "
                "standby or dormant"
            )

        if mode not in {
            "event_driven",
            "none",
        }:
            errors.append(
                "dormant orbit must use "
                "event_driven or none"
            )

        peer_strength = record[
            "interaction_profile"
        ]["peer_interaction_strength"]

        if peer_strength > 0.25:
            errors.append(
                "dormant orbit "
                "peer_interaction_strength "
                "must not exceed 0.25"
            )

    if transition["transition_allowed"]:
        if not targets:
            errors.append(
                "transition-enabled nodes "
                "require target orbits"
            )

        if not transition["approach_triggers"]:
            errors.append(
                "transition-enabled nodes "
                "require approach triggers"
            )

        if not transition["departure_triggers"]:
            errors.append(
                "transition-enabled nodes "
                "require departure triggers"
            )

        if not transition["return_conditions"]:
            errors.append(
                "transition-enabled nodes "
                "require return conditions"
            )

    elif targets:
        errors.append(
            "transition-disabled nodes "
            "must not define targets"
        )

    return errors


def validate_tidal_interaction(
    record: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    participants = record["participants"]
    source = participants["source"]
    target = participants["target"]
    mediators = participants["mediators"]

    if source["node_id"] == target["node_id"]:
        errors.append(
            "source and target node_id must differ"
        )

    mediator_ids = [
        item["node_id"]
        for item in mediators
    ]

    if len(mediator_ids) != len(
        set(mediator_ids)
    ):
        errors.append(
            "mediator node_id values must be unique"
        )

    primary_ids = {
        source["node_id"],
        target["node_id"],
    }

    mediator_overlap = (
        primary_ids & set(mediator_ids)
    )

    if mediator_overlap:
        errors.append(
            "mediators must differ from "
            "source and target: "
            f"{sorted(mediator_overlap)}"
        )

    interaction = record["interaction"]
    interaction_type = interaction[
        "interaction_type"
    ]

    expected_family = INTERACTION_FAMILY[
        interaction_type
    ]

    if (
        interaction["interaction_family"]
        != expected_family
    ):
        errors.append(
            f"{interaction_type} must use "
            f"family {expected_family}"
        )

    safeguards = record["safeguards"]

    if (
        interaction["intensity"]
        > safeguards[
            "maximum_allowed_intensity"
        ]
    ):
        errors.append(
            "interaction intensity exceeds "
            "its configured maximum"
        )

    started_at = parse_datetime(
        interaction["started_at"]
    )

    ended_at_value = interaction["ended_at"]

    if ended_at_value:
        ended_at = parse_datetime(
            ended_at_value
        )

        if ended_at < started_at:
            errors.append(
                "interaction.ended_at "
                "must follow started_at"
            )

    elif interaction["status"] == "completed":
        errors.append(
            "completed interactions require ended_at"
        )

    payload = record["payload"]

    if interaction_type in {
        "conflict",
        "repulsion",
    }:
        if not payload["evidence_refs"]:
            errors.append(
                f"{interaction_type} "
                "requires evidence_refs"
            )

        if not safeguards["audit_required"]:
            errors.append(
                f"{interaction_type} "
                "must require audit"
            )

    if (
        interaction_type == "evidence_exchange"
        and not payload["evidence_refs"]
    ):
        errors.append(
            "evidence_exchange "
            "requires evidence_refs"
        )

    if (
        interaction_type == "trace_handoff"
        and not payload["trace_refs"]
    ):
        errors.append(
            "trace_handoff requires trace_refs"
        )

    if interaction_type == "resource_pull":
        if not payload["resource_refs"]:
            errors.append(
                "resource_pull "
                "requires resource_refs"
            )

        if "resource_request" not in payload:
            errors.append(
                "resource_pull "
                "requires resource_request"
            )

    if (
        interaction_type == "synchronization"
        and not payload["sync_scope"]
    ):
        errors.append(
            "synchronization requires sync_scope"
        )

    if interaction["intensity"] >= 0.8:
        if not safeguards[
            "human_review_required"
        ]:
            errors.append(
                "intensity >= 0.8 "
                "requires human review"
            )

    if safeguards["human_review_required"]:
        if (
            safeguards["review_status"]
            == "not_required"
        ):
            errors.append(
                "required human review needs "
                "an active review status"
            )

    elif (
        safeguards["review_status"]
        != "not_required"
    ):
        errors.append(
            "non-required review must use "
            "not_required status"
        )

    if (
        safeguards["consent_model"]
        == "mutual_required"
        and safeguards["consent_status"]
        == "not_applicable"
    ):
        errors.append(
            "mutual consent cannot be "
            "not_applicable"
        )

    resolution = record["resolution"]

    if (
        not interaction["core_mediation"]
        and resolution["resolution_mode"]
        == "core_mediated"
    ):
        errors.append(
            "core_mediated resolution requires "
            "core_mediation=true"
        )

    if (
        resolution["resolution_mode"]
        in {
            "peer_to_peer",
            "local_cluster",
        }
        and not interaction[
            "local_resolution_attempted"
        ]
    ):
        errors.append(
            "peer/local resolution "
            "requires a local attempt"
        )

    expires_at = resolution["expires_at"]

    if expires_at:
        if parse_datetime(
            expires_at
        ) <= parse_datetime(
            record["created_at"]
        ):
            errors.append(
                "resolution.expires_at "
                "must follow created_at"
            )

    orbit_change = record[
        "effects"
    ]["orbit_change"]

    if orbit_change["requested"]:
        source_target = orbit_change[
            "source_target_orbit"
        ]

        target_target = orbit_change[
            "target_target_orbit"
        ]

        if (
            source_target is None
            and target_target is None
        ):
            errors.append(
                "orbit change requires "
                "at least one target orbit"
            )

        if not orbit_change["reason"]:
            errors.append(
                "orbit change requires a reason"
            )

        if not resolution["return_conditions"]:
            errors.append(
                "orbit change requires "
                "return conditions"
            )

        if (
            source_target
            == source["orbit_class"]
        ):
            errors.append(
                "source target orbit must differ "
                "from current orbit"
            )

        if (
            target_target
            == target["orbit_class"]
        ):
            errors.append(
                "target target orbit must differ "
                "from current orbit"
            )

    else:
        residual_values = (
            orbit_change["source_target_orbit"],
            orbit_change["target_target_orbit"],
            orbit_change["reason"],
        )

        if any(
            value is not None
            for value in residual_values
        ):
            errors.append(
                "orbit targets and reason must be "
                "null when not requested"
            )

    route_effect = record[
        "effects"
    ]["route_effect"]

    if route_effect in {
        "divert",
        "isolate",
    }:
        if not resolution["return_conditions"]:
            errors.append(
                f"{route_effect} requires "
                "return conditions"
            )

    related_definitions = set(
        record["trace"][
            "related_definition_ids"
        ]
    )

    required_definitions = {
        source["orbital_definition_id"],
        target["orbital_definition_id"],
        *(
            item["orbital_definition_id"]
            for item in mediators
        ),
    }

    missing_definitions = (
        required_definitions
        - related_definitions
    )

    if missing_definitions:
        errors.append(
            "trace.related_definition_ids "
            "is missing: "
            f"{sorted(missing_definitions)}"
        )

    return errors


TARGETS: tuple[
    tuple[
        str,
        str,
        str,
        SemanticValidator,
    ],
    ...
] = (
    (
        "Solar Core State Record",
        "solar-core-state.schema.json",
        "solar-core-state.example.yaml",
        validate_solar_core,
    ),
    (
        "Orbital Node Definition",
        "orbital-node-definition.schema.json",
        "orbital-node-definition.example.yaml",
        validate_orbital_node,
    ),
    (
        "Tidal Interaction Record",
        "tidal-interaction-record.schema.json",
        "tidal-interaction-record.example.yaml",
        validate_tidal_interaction,
    ),
)


def validate_target(
    name: str,
    schema_name: str,
    example_name: str,
    semantic_validator: SemanticValidator,
) -> list[str]:
    schema_path = (
        ROOT
        / "schemas"
        / schema_name
    )

    example_path = (
        ROOT
        / "examples"
        / example_name
    )

    print(f"[validate] {name}")
    print(
        "  schema : "
        f"{schema_path.relative_to(ROOT)}"
    )
    print(
        "  example: "
        f"{example_path.relative_to(ROOT)}"
    )

    schema = load_json(schema_path)

    Draft202012Validator.check_schema(
        schema
    )

    print(f"[schema-ok] {name}")

    record = load_yaml(example_path)

    validator = Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    )

    schema_errors = sorted(
        validator.iter_errors(record),
        key=lambda item: list(
            item.absolute_path
        ),
    )

    errors = [
        (
            f"{format_path(error.absolute_path)}: "
            f"{error.message}"
        )
        for error in schema_errors
    ]

    if not errors:
        errors.extend(
            semantic_validator(record)
        )

    if errors:
        for error in errors:
            print(f"[error] {error}")
    else:
        print(f"[example-ok] {name}")

    print()

    return errors


def main() -> int:
    print(
        "=== Solar System Balance "
        "Protocol Validation ==="
    )
    print()

    all_errors: list[str] = []

    try:
        for (
            name,
            schema_name,
            example_name,
            validator,
        ) in TARGETS:
            errors = validate_target(
                name,
                schema_name,
                example_name,
                validator,
            )

            all_errors.extend(
                f"{name}: {error}"
                for error in errors
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
            "Validation failed with "
            f"{len(all_errors)} error(s)."
        )
        return 1

    print("All validations passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
