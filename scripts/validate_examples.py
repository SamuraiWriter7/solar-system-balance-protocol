#!/usr/bin/env python3
"""Validate Solar System Balance Protocol schemas and examples.

This validator performs two layers of checks:

1. JSON Schema validation for each protocol record.
2. Cross-field semantic validation that JSON Schema alone cannot express.

Supported protocol layers:
- v0.1 Solar Core State Record
- v0.2 Orbital Node Definition
- v0.3 Tidal Interaction Record
- v0.4 Breathing Trigger Policy
- v0.5 Life-Cycle Balance Loop
"""

from __future__ import annotations

import json
import math
import sys
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

ROOT = Path(__file__).resolve().parents[1]

AXES: tuple[str, ...] = (
    "coordination_strength",
    "audit_strength",
    "routing_strength",
    "resource_control",
    "emergency_authority",
)

INTERACTION_FAMILY: dict[str, str] = {
    "resonance": "attractive",
    "resource_pull": "attractive",
    "synchronization": "attractive",
    "conflict": "repulsive",
    "repulsion": "repulsive",
    "evidence_exchange": "exchange",
    "trace_handoff": "exchange",
}

TRIGGER_OPERATORS: dict[str, Callable[[float, float], bool]] = {
    "gt": lambda observed, threshold: observed > threshold,
    "gte": lambda observed, threshold: observed >= threshold,
    "lt": lambda observed, threshold: observed < threshold,
    "lte": lambda observed, threshold: observed <= threshold,
    "eq": lambda observed, threshold: math.isclose(
        observed,
        threshold,
        rel_tol=1e-9,
        abs_tol=1e-9,
    ),
    "neq": lambda observed, threshold: not math.isclose(
        observed,
        threshold,
        rel_tol=1e-9,
        abs_tol=1e-9,
    ),
}

DIVERSITY_ACTIONS: set[str] = {
    "activate_outer_orbit",
    "activate_contrarian_nodes",
    "wake_comet_node",
    "wake_dormant_node",
    "diversify_routes",
}

LIFECYCLE_ORDER: tuple[str, ...] = (
    "expansion",
    "exploration",
    "consolidation",
    "restoration",
    "re_expansion",
)

LIFECYCLE_TRANSITIONS: tuple[tuple[str, str], ...] = (
    ("expansion", "exploration"),
    ("exploration", "consolidation"),
    ("consolidation", "restoration"),
    ("restoration", "re_expansion"),
    ("re_expansion", "expansion"),
)

SemanticValidator = Callable[[dict[str, Any]], list[str]]
ValidationTarget = tuple[str, str, str, SemanticValidator]


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk."""

    with path.open("r", encoding="utf-8") as file:
        value = json.load(file)

    if not isinstance(value, dict):
        raise ValueError(
            f"{path.relative_to(ROOT)} "
            "must contain a JSON object at the root."
        )

    return value


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML object from disk."""

    with path.open("r", encoding="utf-8") as file:
        value = yaml.safe_load(file)

    if not isinstance(value, dict):
        raise ValueError(
            f"{path.relative_to(ROOT)} "
            "must contain a YAML object at the root."
        )

    return value


def parse_datetime(value: str) -> datetime:
    """Parse an ISO 8601 datetime, accepting a trailing Z."""

    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )


def format_path(path: Sequence[Any]) -> str:
    """Format a jsonschema error path for readable output."""

    parts = [str(part) for part in path]
    return ".".join(parts) if parts else "<root>"


def add_overlap_error(
    errors: list[str],
    left_name: str,
    left_values: Sequence[str],
    right_name: str,
    right_values: Sequence[str],
) -> None:
    """Append an error when two declared value sets overlap."""

    overlap = set(left_values) & set(right_values)

    if overlap:
        errors.append(
            f"{left_name} and {right_name} "
            f"must not overlap: {sorted(overlap)}"
        )


def ensure_unique(
    errors: list[str],
    values: Sequence[str],
    field_name: str,
) -> None:
    """Append an error when a sequence contains duplicates."""

    if len(values) != len(set(values)):
        errors.append(
            f"{field_name} values must be unique"
        )


def evaluate_metric(
    observed_value: float,
    operator_name: str,
    target_value: float,
) -> bool:
    """Evaluate a metric with a protocol comparison operator."""

    try:
        operator = TRIGGER_OPERATORS[operator_name]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported comparison operator: {operator_name}"
        ) from exc

    return operator(
        observed_value,
        target_value,
    )


def validate_solar_core_state(
    record: dict[str, Any],
) -> list[str]:
    """Validate v0.1 Solar Core State Record semantics."""

    errors: list[str] = []

    core = record["solar_core_state"]
    aggregate = core["aggregate_breathing_index"]
    axes = core["axes"]
    weights = aggregate["weights"]

    weight_sum = sum(
        float(weights[name])
        for name in AXES
    )

    if not math.isclose(
        weight_sum,
        1.0,
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        errors.append(
            "solar_core_state.aggregate_breathing_index."
            "weights must sum to 1.0; "
            f"got {weight_sum:.12f}"
        )

    calculated_index = sum(
        float(axes[name]) * float(weights[name])
        for name in AXES
    )
    declared_index = float(aggregate["value"])

    if not math.isclose(
        calculated_index,
        declared_index,
        rel_tol=0.0,
        abs_tol=1e-6,
    ):
        errors.append(
            "solar_core_state.aggregate_breathing_index."
            "value must equal the weighted mean; "
            f"declared {declared_index:.6f}, "
            f"calculated {calculated_index:.6f}"
        )

    scope = core["centrality_scope"]
    scope_names = (
        "strengthened_functions",
        "preserved_distributed_functions",
        "restricted_functions",
    )

    for index, left_name in enumerate(scope_names):
        for right_name in scope_names[index + 1 :]:
            add_overlap_error(
                errors,
                (
                    "solar_core_state.centrality_scope."
                    f"{left_name}"
                ),
                scope[left_name],
                (
                    "solar_core_state.centrality_scope."
                    f"{right_name}"
                ),
                scope[right_name],
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

    created_at = parse_datetime(record["created_at"])
    reversibility = record["reversibility"]
    expires_at = reversibility.get("expires_at")

    if expires_at is not None:
        expiry = parse_datetime(expires_at)

        if expiry <= created_at:
            errors.append(
                "reversibility.expires_at "
                "must be later than created_at"
            )

    if core["mode"] == "emergency":
        if not reversibility["reversible"]:
            errors.append(
                "emergency mode must remain reversible"
            )

        if not reversibility["human_review_required"]:
            errors.append(
                "emergency mode must require human review"
            )

        if expires_at is None:
            errors.append(
                "emergency mode must define expires_at"
            )

        if not reversibility["return_conditions"]:
            errors.append(
                "emergency mode must define "
                "at least one return condition"
            )

    return errors


def validate_orbital_node_definition(
    record: dict[str, Any],
) -> list[str]:
    """Validate v0.2 Orbital Node Definition semantics."""

    errors: list[str] = []

    orbit = record["orbit"]
    orbit_class = orbit["orbit_class"]
    distance = float(orbit["distance_from_core"])
    binding = float(orbit["binding_strength"])
    autonomy = float(orbit["autonomy_level"])

    frequency = orbit["interaction_frequency"]
    frequency_mode = frequency["mode"]
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
    target_orbits = set(
        transition["allowed_target_orbits"]
    )

    if orbit_class in target_orbits:
        errors.append(
            "transition_policy.allowed_target_orbits "
            "must not include the current orbit"
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
            "orbit.interaction_frequency."
            "nominal_interval_seconds "
            f"must be 0 when mode is {frequency_mode}"
        )

    if (
        frequency_mode in positive_interval_modes
        and interval <= 0
    ):
        errors.append(
            "orbit.interaction_frequency."
            "nominal_interval_seconds "
            f"must be greater than 0 "
            f"when mode is {frequency_mode}"
        )

    if orbit_class == "inner":
        if distance > 0.35:
            errors.append(
                "inner orbit distance_from_core "
                "must not exceed 0.35"
            )

        if binding < 0.60:
            errors.append(
                "inner orbit binding_strength "
                "must be at least 0.60"
            )

    elif orbit_class == "middle":
        if not 0.25 <= distance <= 0.75:
            errors.append(
                "middle orbit distance_from_core "
                "must be between 0.25 and 0.75"
            )

    elif orbit_class == "outer":
        if distance < 0.55:
            errors.append(
                "outer orbit distance_from_core "
                "must be at least 0.55"
            )

        if autonomy < 0.60:
            errors.append(
                "outer orbit autonomy_level "
                "must be at least 0.60"
            )

    elif orbit_class == "comet":
        comet_profile = record.get("comet_profile")

        if frequency_mode != "event_driven":
            errors.append(
                "comet orbit must use "
                "event_driven interaction"
            )

        if comet_profile is None:
            errors.append(
                "comet orbit requires comet_profile"
            )
        else:
            if not comet_profile["activation_triggers"]:
                errors.append(
                    "comet_profile.activation_triggers "
                    "must not be empty"
                )

            if int(
                comet_profile["active_window_seconds"]
            ) <= 0:
                errors.append(
                    "comet_profile.active_window_seconds "
                    "must be greater than 0"
                )

        if not ({"inner", "middle"} & target_orbits):
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

    elif orbit_class == "dormant":
        operational_state = record["node"][
            "operational_state"
        ]

        if operational_state not in {
            "standby",
            "dormant",
        }:
            errors.append(
                "dormant orbit node must be in "
                "standby or dormant state"
            )

        if frequency_mode not in {
            "event_driven",
            "none",
        }:
            errors.append(
                "dormant orbit must use "
                "event_driven or none interaction"
            )

        if orbit["orbital_phase"] != "hibernating":
            errors.append(
                "dormant orbit must use "
                "orbital_phase=hibernating"
            )

        peer_strength = float(
            record["interaction_profile"][
                "peer_interaction_strength"
            ]
        )

        if peer_strength > 0.25:
            errors.append(
                "dormant orbit peer_interaction_strength "
                "must not exceed 0.25"
            )

        if record.get("dormant_profile") is None:
            errors.append(
                "dormant orbit requires dormant_profile"
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

        if transition["approach_triggers"]:
            errors.append(
                "transition-disabled nodes must not "
                "define approach triggers"
            )

        if transition["departure_triggers"]:
            errors.append(
                "transition-disabled nodes must not "
                "define departure triggers"
            )

        if transition["return_conditions"]:
            errors.append(
                "transition-disabled nodes must not "
                "define return conditions"
            )

    return errors


def validate_tidal_interaction_record(
    record: dict[str, Any],
) -> list[str]:
    """Validate v0.3 Tidal Interaction Record semantics."""

    errors: list[str] = []

    participants = record["participants"]
    source = participants["source"]
    target = participants["target"]
    mediators = participants["mediators"]

    if source["node_id"] == target["node_id"]:
        errors.append(
            "participants.source and target "
            "node_id must differ"
        )

    mediator_ids = [
        item["node_id"]
        for item in mediators
    ]

    ensure_unique(
        errors,
        mediator_ids,
        "participants.mediators.node_id",
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
            "interaction_family="
            f"{expected_family}"
        )

    safeguards = record["safeguards"]

    if float(
        interaction["intensity"]
    ) > float(
        safeguards["maximum_allowed_intensity"]
    ):
        errors.append(
            "interaction.intensity exceeds "
            "safeguards.maximum_allowed_intensity"
        )

    started_at = parse_datetime(
        interaction["started_at"]
    )
    ended_at_value = interaction["ended_at"]

    if ended_at_value is not None:
        ended_at = parse_datetime(
            ended_at_value
        )

        if ended_at < started_at:
            errors.append(
                "interaction.ended_at "
                "must not precede started_at"
            )

    elif interaction["status"] in {
        "completed",
        "expired",
    }:
        errors.append(
            f"{interaction['status']} interactions "
            "require ended_at"
        )

    payload = record["payload"]

    if interaction_type in {
        "conflict",
        "repulsion",
    }:
        if not payload["evidence_refs"]:
            errors.append(
                f"{interaction_type} requires "
                "payload.evidence_refs"
            )

        if not safeguards["audit_required"]:
            errors.append(
                f"{interaction_type} must require audit"
            )

    if (
        interaction_type == "evidence_exchange"
        and not payload["evidence_refs"]
    ):
        errors.append(
            "evidence_exchange requires "
            "payload.evidence_refs"
        )

    if (
        interaction_type == "trace_handoff"
        and not payload["trace_refs"]
    ):
        errors.append(
            "trace_handoff requires "
            "payload.trace_refs"
        )

    if interaction_type == "resource_pull":
        if not payload["resource_refs"]:
            errors.append(
                "resource_pull requires "
                "payload.resource_refs"
            )

        if "resource_request" not in payload:
            errors.append(
                "resource_pull requires "
                "payload.resource_request"
            )

    if (
        interaction_type == "synchronization"
        and not payload["sync_scope"]
    ):
        errors.append(
            "synchronization requires "
            "payload.sync_scope"
        )

    if float(interaction["intensity"]) >= 0.80:
        if not safeguards["human_review_required"]:
            errors.append(
                "interaction intensity of 0.80 "
                "or higher requires human review"
            )

    if safeguards["human_review_required"]:
        if safeguards["review_status"] == "not_required":
            errors.append(
                "required human review must use "
                "pending, approved, or rejected status"
            )
    elif safeguards["review_status"] != "not_required":
        errors.append(
            "non-required human review must use "
            "review_status=not_required"
        )

    consent_model = safeguards["consent_model"]
    consent_status = safeguards["consent_status"]

    if (
        consent_model == "mutual_required"
        and consent_status not in {
            "pending",
            "accepted",
            "rejected",
        }
    ):
        errors.append(
            "mutual_required consent must use "
            "pending, accepted, or rejected status"
        )

    if (
        consent_status == "rejected"
        and interaction["status"] == "completed"
    ):
        errors.append(
            "an interaction with rejected consent "
            "must not be completed"
        )

    resolution = record["resolution"]

    if (
        not interaction["core_mediation"]
        and resolution["resolution_mode"]
        == "core_mediated"
    ):
        errors.append(
            "core_mediated resolution requires "
            "interaction.core_mediation=true"
        )

    if (
        resolution["resolution_mode"] in {
            "peer_to_peer",
            "local_cluster",
        }
        and not interaction[
            "local_resolution_attempted"
        ]
    ):
        errors.append(
            "peer-to-peer or local-cluster resolution "
            "requires local_resolution_attempted=true"
        )

    expires_at = resolution["expires_at"]

    if expires_at is not None:
        if parse_datetime(
            expires_at
        ) <= parse_datetime(
            record["created_at"]
        ):
            errors.append(
                "resolution.expires_at "
                "must be later than created_at"
            )

    orbit_change = record["effects"][
        "orbit_change"
    ]

    if orbit_change["requested"]:
        source_target_orbit = orbit_change[
            "source_target_orbit"
        ]
        target_target_orbit = orbit_change[
            "target_target_orbit"
        ]

        if (
            source_target_orbit is None
            and target_target_orbit is None
        ):
            errors.append(
                "requested orbit change requires "
                "at least one target orbit"
            )

        if not orbit_change["reason"]:
            errors.append(
                "requested orbit change requires a reason"
            )

        if not resolution["return_conditions"]:
            errors.append(
                "requested orbit change requires "
                "return conditions"
            )

        if (
            source_target_orbit
            == source["orbit_class"]
        ):
            errors.append(
                "source_target_orbit must differ from "
                "the source current orbit"
            )

        if (
            target_target_orbit
            == target["orbit_class"]
        ):
            errors.append(
                "target_target_orbit must differ from "
                "the target current orbit"
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
                "orbit targets and reason must be null "
                "when orbit_change.requested=false"
            )

    route_effect = record["effects"]["route_effect"]

    if route_effect in {
        "divert",
        "isolate",
    }:
        if not resolution["return_conditions"]:
            errors.append(
                f"route effect {route_effect} requires "
                "return conditions"
            )

        if expires_at is None:
            errors.append(
                f"route effect {route_effect} requires "
                "resolution.expires_at"
            )

    related_definitions = set(
        record["trace"]["related_definition_ids"]
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


def validate_breathing_trigger_policy(
    record: dict[str, Any],
) -> list[str]:
    """Validate v0.4 Breathing Trigger Policy semantics."""

    errors: list[str] = []

    trigger = record["trigger"]
    metrics = trigger["metrics"]

    metric_ids = [
        metric["metric_id"]
        for metric in metrics
    ]

    ensure_unique(
        errors,
        metric_ids,
        "trigger.metrics.metric_id",
    )

    metric_results: dict[str, bool] = {}

    for metric in metrics:
        metric_id = metric["metric_id"]
        observed = float(
            metric["observed_value"]
        )
        threshold = float(
            metric["threshold_value"]
        )
        operator_name = metric["operator"]

        metric_results[metric_id] = evaluate_metric(
            observed,
            operator_name,
            threshold,
        )

        if (
            trigger["evidence_required"]
            and not metric["evidence_refs"]
        ):
            errors.append(
                "evidence-required trigger metric "
                f"{metric_id} has no evidence_refs"
            )

    if trigger["condition_mode"] == "all":
        calculated_condition = all(
            metric_results.values()
        )
    else:
        calculated_condition = any(
            metric_results.values()
        )

    evaluation = record["evaluation"]

    if (
        evaluation["condition_result"]
        != calculated_condition
    ):
        errors.append(
            "evaluation.condition_result does not "
            "match the evaluated trigger metrics"
        )

    calculated_matches = {
        metric_id
        for metric_id, matched
        in metric_results.items()
        if matched
    }

    declared_matches = set(
        evaluation["matched_metric_ids"]
    )

    unknown_matches = (
        declared_matches - set(metric_ids)
    )

    if unknown_matches:
        errors.append(
            "evaluation.matched_metric_ids "
            "contains unknown metrics: "
            f"{sorted(unknown_matches)}"
        )

    if declared_matches != calculated_matches:
        errors.append(
            "evaluation.matched_metric_ids must "
            "exactly match the successful "
            "metric conditions"
        )

    decision = evaluation["decision"]

    if decision in {
        "activate",
        "escalate",
    }:
        if not evaluation["condition_result"]:
            errors.append(
                f"{decision} decision requires "
                "condition_result=true"
            )

        if (
            evaluation["cooldown_active"]
            and decision == "activate"
        ):
            errors.append(
                "activate decision is not allowed "
                "while cooldown_active=true"
            )

    response = record["response_plan"]
    gravity = response["gravity_adjustments"]
    orbital_actions = response["orbital_actions"]
    tidal_actions = response["tidal_actions"]
    safeguards = record["safeguards"]

    maximum_axis_delta = float(
        safeguards["maximum_axis_delta"]
    )

    for axis, delta_value in gravity.items():
        delta = float(delta_value)

        if abs(delta) > maximum_axis_delta:
            errors.append(
                f"gravity delta for {axis} exceeds "
                "safeguards.maximum_axis_delta"
            )

    if response["response_mode"] == "hold":
        nonzero_axes = [
            axis
            for axis, delta_value in gravity.items()
            if not math.isclose(
                float(delta_value),
                0.0,
                rel_tol=0.0,
                abs_tol=1e-12,
            )
        ]

        if nonzero_axes:
            errors.append(
                "hold response must not modify "
                "gravity axes: "
                f"{sorted(nonzero_axes)}"
            )

        if orbital_actions:
            errors.append(
                "hold response must not define "
                "orbital actions"
            )

        if tidal_actions:
            errors.append(
                "hold response must not define "
                "tidal actions"
            )

        if response["lifecycle_hint"] != "none":
            errors.append(
                "hold response must use "
                "lifecycle_hint=none"
            )

    for index, action in enumerate(
        orbital_actions
    ):
        action_path = (
            "response_plan.orbital_actions"
            f"[{index}]"
        )
        action_type = action["action_type"]
        target_scope = action["target_scope"]
        target_nodes = action["target_node_ids"]
        local_cluster_id = action[
            "local_cluster_id"
        ]

        if (
            target_scope == "specific_nodes"
            and not target_nodes
        ):
            errors.append(
                f"{action_path} with specific_nodes "
                "scope requires target_node_ids"
            )

        if (
            target_scope != "specific_nodes"
            and target_nodes
        ):
            errors.append(
                f"{action_path} may define "
                "target_node_ids only with "
                "specific_nodes scope"
            )

        if (
            target_scope == "local_cluster"
            and local_cluster_id is None
        ):
            errors.append(
                f"{action_path} with local_cluster "
                "scope requires local_cluster_id"
            )

        if (
            target_scope != "local_cluster"
            and local_cluster_id is not None
        ):
            errors.append(
                f"{action_path} may define "
                "local_cluster_id only with "
                "local_cluster scope"
            )

        movement_actions = {
            "move_inward",
            "move_outward",
            "wake_comet_node",
            "wake_dormant_node",
            "restore_previous_orbit",
        }

        if action_type in movement_actions:
            if action["target_orbit"] is None:
                errors.append(
                    f"{action_path} requires target_orbit"
                )
        elif action["target_orbit"] is not None:
            errors.append(
                f"{action_path} must not define "
                "target_orbit"
            )

        if (
            action["source_orbit"] is not None
            and action["source_orbit"]
            == action["target_orbit"]
        ):
            errors.append(
                f"{action_path} source and target "
                "orbits must differ"
            )

    for index, tidal_action in enumerate(
        tidal_actions
    ):
        action_path = (
            "response_plan.tidal_actions"
            f"[{index}]"
        )
        interaction_type = tidal_action[
            "interaction_type"
        ]
        expected_family = INTERACTION_FAMILY[
            interaction_type
        ]

        if (
            tidal_action["interaction_family"]
            != expected_family
        ):
            errors.append(
                f"{action_path}: {interaction_type} "
                "must use interaction_family="
                f"{expected_family}"
            )

        source_ids = set(
            tidal_action["source_node_ids"]
        )
        target_ids = set(
            tidal_action["target_node_ids"]
        )
        overlap = source_ids & target_ids

        if overlap:
            errors.append(
                f"{action_path} source and target "
                "nodes must differ: "
                f"{sorted(overlap)}"
            )

    trigger_type = trigger["trigger_type"]

    if trigger_type == "manual":
        if not trigger["manual_reason"]:
            errors.append(
                "manual trigger requires manual_reason"
            )
    elif trigger["manual_reason"] is not None:
        errors.append(
            "non-manual trigger must use "
            "manual_reason=null"
        )

    if trigger_type == "risk":
        if (
            decision == "activate"
            and float(
                gravity["audit_strength"]
            ) <= 0
        ):
            errors.append(
                "activated risk trigger must "
                "increase audit_strength"
            )

    if trigger_type == "crisis":
        timing = response["activation_timing"]

        if not safeguards["human_review_required"]:
            errors.append(
                "crisis trigger requires human review"
            )

        if not safeguards[
            "emergency_expiry_required"
        ]:
            errors.append(
                "crisis trigger requires "
                "emergency expiry"
            )

        if timing[
            "maximum_duration_seconds"
        ] is None:
            errors.append(
                "crisis trigger requires "
                "maximum_duration_seconds"
            )

        if (
            decision == "activate"
            and float(
                gravity["emergency_authority"]
            ) <= 0
        ):
            errors.append(
                "activated crisis trigger must "
                "increase emergency_authority"
            )

    if trigger_type == "innovation":
        if response["lifecycle_hint"] not in {
            "expansion",
            "exploration",
            "re_expansion",
        }:
            errors.append(
                "innovation trigger must lead toward "
                "expansion or exploration"
            )

    if trigger_type == "stagnation":
        if not safeguards[
            "stagnation_diversity_required"
        ]:
            errors.append(
                "stagnation trigger must require "
                "diversity restoration"
            )

        action_types = {
            action["action_type"]
            for action in orbital_actions
        }

        if not (
            action_types & DIVERSITY_ACTIONS
        ):
            errors.append(
                "stagnation response requires "
                "at least one diversity-restoring "
                "orbital action"
            )

        if (
            float(
                gravity["coordination_strength"]
            ) >= 0
            and float(
                gravity["routing_strength"]
            ) >= 0
        ):
            errors.append(
                "stagnation response must weaken "
                "coordination or routing gravity"
            )

        if response["lifecycle_hint"] not in {
            "expansion",
            "exploration",
            "re_expansion",
        }:
            errors.append(
                "stagnation trigger must lead toward "
                "expansion or exploration"
            )

    if safeguards["human_review_required"]:
        if safeguards["review_status"] == "not_required":
            errors.append(
                "required human review must use "
                "pending, approved, or rejected status"
            )
    elif safeguards["review_status"] != "not_required":
        errors.append(
            "non-required human review must use "
            "review_status=not_required"
        )

    rollback = record["rollback"]

    if not rollback["rollback_conditions"]:
        errors.append(
            "rollback requires at least one "
            "rollback condition"
        )

    if not rollback["rollback_actions"]:
        errors.append(
            "rollback requires at least one "
            "rollback action"
        )

    timing = response["activation_timing"]
    activation_delay = int(
        timing["activation_delay_seconds"]
    )
    maximum_duration = timing[
        "maximum_duration_seconds"
    ]
    maximum_retention = int(
        rollback["maximum_retention_seconds"]
    )

    if maximum_retention < activation_delay:
        errors.append(
            "rollback.maximum_retention_seconds "
            "must not be shorter than "
            "activation_delay_seconds"
        )

    if (
        maximum_duration is not None
        and maximum_retention
        < activation_delay + int(maximum_duration)
    ):
        errors.append(
            "rollback.maximum_retention_seconds "
            "must cover activation delay plus "
            "maximum response duration"
        )

    current_core_state = evaluation[
        "current_core_state_record_id"
    ]
    trace = record["trace"]

    related_core_states = set(
        trace["related_core_state_record_ids"]
    )

    if current_core_state not in related_core_states:
        errors.append(
            "evaluation.current_core_state_record_id "
            "must appear in "
            "trace.related_core_state_record_ids"
        )

    current_orbits = set(
        evaluation[
            "current_orbital_definition_ids"
        ]
    )
    traced_orbits = set(
        trace["related_orbital_definition_ids"]
    )
    missing_orbits = (
        current_orbits - traced_orbits
    )

    if missing_orbits:
        errors.append(
            "trace is missing orbital definitions: "
            f"{sorted(missing_orbits)}"
        )

    current_interactions = set(
        evaluation[
            "current_interaction_record_ids"
        ]
    )
    traced_interactions = set(
        trace["related_interaction_record_ids"]
    )
    missing_interactions = (
        current_interactions
        - traced_interactions
    )

    if missing_interactions:
        errors.append(
            "trace is missing interaction records: "
            f"{sorted(missing_interactions)}"
        )

    created_at = parse_datetime(
        record["created_at"]
    )
    evaluated_at = parse_datetime(
        evaluation["evaluated_at"]
    )

    if evaluated_at < created_at:
        errors.append(
            "evaluation.evaluated_at must not "
            "precede created_at"
        )

    return errors


def validate_life_cycle_balance_loop(
    record: dict[str, Any],
) -> list[str]:
    """Validate v0.5 Life-Cycle Balance Loop semantics."""

    errors: list[str] = []

    cycle = record["cycle"]
    phase_plan = record["phase_plan"]
    phases = phase_plan["phases"]
    transitions = phase_plan["transitions"]
    budget = record["balance_budget"]
    safeguards = record["safeguards"]
    closure = record["closure"]

    expected_order = tuple(
        phase_plan["expected_order"]
    )

    if expected_order != LIFECYCLE_ORDER:
        errors.append(
            "phase_plan.expected_order must "
            "exactly equal "
            f"{list(LIFECYCLE_ORDER)}"
        )

    declared_phase_names = tuple(
        phase["phase"]
        for phase in phases
    )

    if declared_phase_names != LIFECYCLE_ORDER:
        errors.append(
            "phase_plan.phases must appear "
            "exactly in lifecycle order"
        )

    declared_sequences = tuple(
        int(phase["sequence"])
        for phase in phases
    )

    if declared_sequences != (
        1,
        2,
        3,
        4,
        5,
    ):
        errors.append(
            "phase sequence values must be "
            "exactly 1 through 5"
        )

    phase_names = [
        phase["phase"]
        for phase in phases
    ]

    ensure_unique(
        errors,
        phase_names,
        "phase_plan.phases.phase",
    )

    active_phases = [
        phase["phase"]
        for phase in phases
        if phase["status"] == "active"
    ]

    if cycle["loop_status"] == "active":
        if len(active_phases) != 1:
            errors.append(
                "an active loop must contain "
                "exactly one active phase"
            )
        elif (
            cycle["active_phase"]
            != active_phases[0]
        ):
            errors.append(
                "cycle.active_phase must match "
                "the active phase record"
            )
    else:
        if active_phases:
            errors.append(
                "a non-active loop must not contain "
                "an active phase"
            )

        if cycle["active_phase"] is not None:
            errors.append(
                "a non-active loop must use "
                "cycle.active_phase=null"
            )

    phase_durations: dict[str, float] = {}
    previous_end: datetime | None = None

    for phase in phases:
        phase_name = phase["phase"]
        status = phase["status"]
        started_value = phase["started_at"]
        ended_value = phase["ended_at"]

        if (
            status in {
                "active",
                "completed",
                "blocked",
            }
            and started_value is None
        ):
            errors.append(
                f"{phase_name} phase with "
                f"status={status} requires started_at"
            )

        if status == "completed":
            if ended_value is None:
                errors.append(
                    f"completed {phase_name} phase "
                    "requires ended_at"
                )

            if not phase["output_refs"]:
                errors.append(
                    f"completed {phase_name} phase "
                    "requires output_refs"
                )

        if status in {
            "pending",
            "skipped",
        }:
            if (
                started_value is not None
                or ended_value is not None
            ):
                errors.append(
                    f"{status} {phase_name} phase "
                    "must not define timestamps"
                )

        started_at: datetime | None = None
        ended_at: datetime | None = None

        if started_value is not None:
            started_at = parse_datetime(
                started_value
            )

            if (
                previous_end is not None
                and started_at < previous_end
            ):
                errors.append(
                    f"{phase_name} starts before "
                    "the previous phase ended"
                )

        if ended_value is not None:
            ended_at = parse_datetime(
                ended_value
            )

            if started_at is None:
                errors.append(
                    f"{phase_name}.ended_at "
                    "requires started_at"
                )
            elif ended_at < started_at:
                errors.append(
                    f"{phase_name}.ended_at "
                    "must not precede started_at"
                )
            else:
                duration = (
                    ended_at - started_at
                ).total_seconds()

                phase_durations[
                    phase_name
                ] = duration

                maximum_duration = int(
                    budget[
                        "maximum_phase_duration_seconds"
                    ][phase_name]
                )

                if duration > maximum_duration:
                    errors.append(
                        f"{phase_name} duration exceeds "
                        "its configured maximum"
                    )

                previous_end = ended_at

        metric_ids = [
            metric["metric_id"]
            for metric in phase["metrics"]
        ]

        ensure_unique(
            errors,
            metric_ids,
            f"{phase_name}.metrics.metric_id",
        )

        for metric in phase["metrics"]:
            calculated_result = evaluate_metric(
                float(metric["observed_value"]),
                metric["operator"],
                float(metric["target_value"]),
            )

            if (
                metric["result"]
                != calculated_result
            ):
                errors.append(
                    f"{phase_name} metric "
                    f"{metric['metric_id']} "
                    "has an incorrect result"
                )

            if (
                safeguards[
                    "trace_continuity_required"
                ]
                and not metric["evidence_refs"]
            ):
                errors.append(
                    f"{phase_name} metric "
                    f"{metric['metric_id']} "
                    "requires evidence_refs"
                )

    restoration_phase = next(
        phase
        for phase in phases
        if phase["phase"] == "restoration"
    )

    if (
        safeguards["no_skipped_restoration"]
        and restoration_phase["status"]
        == "skipped"
    ):
        errors.append(
            "restoration phase must not be skipped"
        )

    restoration_duration = phase_durations.get(
        "restoration"
    )

    if (
        restoration_duration is not None
        and restoration_duration
        < int(
            budget[
                "minimum_restoration_duration_seconds"
            ]
        )
    ):
        errors.append(
            "restoration duration is below "
            "minimum_restoration_duration_seconds"
        )

    cycle_started = parse_datetime(
        cycle["started_at"]
    )
    cycle_ended_value = cycle["ended_at"]

    if cycle_ended_value is not None:
        cycle_ended = parse_datetime(
            cycle_ended_value
        )

        if cycle_ended < cycle_started:
            errors.append(
                "cycle.ended_at must not precede "
                "cycle.started_at"
            )
        else:
            cycle_duration = (
                cycle_ended - cycle_started
            ).total_seconds()

            if cycle_duration > int(
                budget[
                    "maximum_cycle_duration_seconds"
                ]
            ):
                errors.append(
                    "cycle duration exceeds "
                    "maximum_cycle_duration_seconds"
                )

    declared_transitions = tuple(
        (
            transition["from_phase"],
            transition["to_phase"],
        )
        for transition in transitions
    )

    expected_transition_count = (
        5
        if cycle["loop_status"] == "completed"
        else 4
    )

    if (
        len(transitions)
        != expected_transition_count
    ):
        errors.append(
            "transition count does not match "
            "cycle.loop_status"
        )

    expected_transitions = (
        LIFECYCLE_TRANSITIONS[
            :expected_transition_count
        ]
    )

    if (
        declared_transitions
        != expected_transitions
    ):
        errors.append(
            "phase transitions do not follow "
            "the required lifecycle order"
        )

    previous_transition_time: (
        datetime | None
    ) = None

    for transition in transitions:
        transition_time = parse_datetime(
            transition["triggered_at"]
        )

        if (
            previous_transition_time is not None
            and transition_time
            < previous_transition_time
        ):
            errors.append(
                "transition timestamps must "
                "be chronological"
            )

        previous_transition_time = (
            transition_time
        )

        if (
            cycle["loop_status"] == "completed"
            and not transition["condition_met"]
        ):
            errors.append(
                "completed loops require every "
                "transition condition to be met"
            )

        if (
            safeguards[
                "trace_continuity_required"
            ]
            and not transition["evidence_refs"]
        ):
            errors.append(
                "transition "
                f"{transition['from_phase']} -> "
                f"{transition['to_phase']} "
                "requires evidence_refs"
            )

        is_final_transition = (
            transition["from_phase"]
            == "re_expansion"
            and transition["to_phase"]
            == "expansion"
        )

        if is_final_transition:
            if transition["to_cycle_id"] is None:
                errors.append(
                    "re_expansion -> expansion "
                    "transition requires to_cycle_id"
                )
            elif (
                transition["to_cycle_id"]
                != cycle["next_cycle_id"]
            ):
                errors.append(
                    "final transition.to_cycle_id "
                    "must match cycle.next_cycle_id"
                )
        elif transition["to_cycle_id"] is not None:
            errors.append(
                "only re_expansion -> expansion "
                "may define to_cycle_id"
            )

    if cycle["loop_status"] == "completed":
        incomplete_phases = [
            phase["phase"]
            for phase in phases
            if phase["status"] != "completed"
        ]

        if incomplete_phases:
            errors.append(
                "completed loop contains "
                "incomplete phases: "
                f"{incomplete_phases}"
            )

        if cycle["ended_at"] is None:
            errors.append(
                "completed loop requires "
                "cycle.ended_at"
            )

        if cycle["next_cycle_id"] is None:
            errors.append(
                "completed loop requires "
                "cycle.next_cycle_id"
            )

        if not closure["loop_closed"]:
            errors.append(
                "completed loop requires "
                "closure.loop_closed=true"
            )

        if not closure[
            "next_cycle_authorized"
        ]:
            errors.append(
                "completed loop requires "
                "closure.next_cycle_authorized=true"
            )

        if not closure[
            "next_cycle_seed_refs"
        ]:
            errors.append(
                "completed loop requires "
                "closure.next_cycle_seed_refs"
            )

    if closure["next_cycle_authorized"]:
        if cycle["next_cycle_id"] is None:
            errors.append(
                "authorized next cycle requires "
                "cycle.next_cycle_id"
            )

        if not closure[
            "next_cycle_seed_refs"
        ]:
            errors.append(
                "authorized next cycle requires "
                "next_cycle_seed_refs"
            )

    if (
        closure["success_criteria_met"]
        and closure["unresolved_risks"]
    ):
        errors.append(
            "success_criteria_met=true requires "
            "no unresolved risks"
        )

    preserved_routes = set(
        closure["preserved_routes"]
    )
    retired_routes = set(
        closure["retired_routes"]
    )

    route_overlap = (
        preserved_routes & retired_routes
    )

    if route_overlap:
        errors.append(
            "routes cannot be both preserved "
            "and retired: "
            f"{sorted(route_overlap)}"
        )

    if safeguards["human_review_required"]:
        if safeguards[
            "review_status"
        ] == "not_required":
            errors.append(
                "required human review must use "
                "pending, approved, or rejected status"
            )

        if (
            cycle["loop_status"] == "completed"
            and safeguards["review_status"]
            != "approved"
        ):
            errors.append(
                "completed reviewed loop requires "
                "review_status=approved"
            )

    elif safeguards[
        "review_status"
    ] != "not_required":
        errors.append(
            "non-required human review must use "
            "review_status=not_required"
        )

    if (
        safeguards["no_permanent_expansion"]
        and cycle["loop_status"] == "completed"
        and phases[0]["ended_at"] is None
    ):
        errors.append(
            "expansion must end before loop closure"
        )

    if (
        safeguards[
            "no_permanent_consolidation"
        ]
        and cycle["loop_status"] == "completed"
        and phases[2]["ended_at"] is None
    ):
        errors.append(
            "consolidation must end "
            "before loop closure"
        )

    if (
        cycle["previous_cycle_id"]
        == cycle["cycle_id"]
    ):
        errors.append(
            "cycle.previous_cycle_id must differ "
            "from cycle.cycle_id"
        )

    if (
        cycle["next_cycle_id"]
        == cycle["cycle_id"]
    ):
        errors.append(
            "cycle.next_cycle_id must differ "
            "from cycle.cycle_id"
        )

    return errors


TARGETS: tuple[ValidationTarget, ...] = (
    (
        "Solar Core State Record",
        "solar-core-state.schema.json",
        "solar-core-state.example.yaml",
        validate_solar_core_state,
    ),
    (
        "Orbital Node Definition",
        "orbital-node-definition.schema.json",
        "orbital-node-definition.example.yaml",
        validate_orbital_node_definition,
    ),
    (
        "Tidal Interaction Record",
        "tidal-interaction-record.schema.json",
        "tidal-interaction-record.example.yaml",
        validate_tidal_interaction_record,
    ),
    (
        "Breathing Trigger Policy",
        "breathing-trigger-policy.schema.json",
        "breathing-trigger-policy.example.yaml",
        validate_breathing_trigger_policy,
    ),
    (
        "Life-Cycle Balance Loop",
        "life-cycle-balance-loop.schema.json",
        "life-cycle-balance-loop.example.yaml",
        validate_life_cycle_balance_loop,
    ),
)


def validate_target(
    name: str,
    schema_name: str,
    example_name: str,
    semantic_validator: SemanticValidator,
) -> list[str]:
    """Validate one schema/example pair."""

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
        key=lambda error: list(
            error.absolute_path
        ),
    )

    errors = [
        (
            f"{format_path(error.absolute_path)}: "
            f"{error.message}"
        )
        for error in schema_errors
    ]

    if not schema_errors:
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
    """Run all protocol validations."""

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
            semantic_validator,
        ) in TARGETS:
            target_errors = validate_target(
                name,
                schema_name,
                example_name,
                semantic_validator,
            )

            all_errors.extend(
                f"{name}: {error}"
                for error in target_errors
            )

    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError,
        yaml.YAMLError,
        SchemaError,
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
