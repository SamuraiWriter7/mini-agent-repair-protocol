#!/usr/bin/env python3
"""
MARP v0.1-v0.3 integrated fixture validator.

v0.1:
    Repair record schema and semantic validation.

v0.2:
    Lifecycle record schema and semantic validation.

v0.3:
    Repair lineage, causal ordering, evidence bindings,
    authorization history, hold tracking, source records,
    and recovery gate validation.

The v0.3 sources are synthetic test fixtures.
Passing these checks does not prove real-world evidence
authenticity, trusted authorization, or runtime safety.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]

VERSIONS = {
    "v0.1": (
        "schemas/repair-record.schema.json",
        4,
        6,
    ),
    "v0.2": (
        "schemas/repair-lifecycle-v0.2.schema.json",
        6,
        6,
    ),
    "v0.3": (
        "schemas/repair-lineage-v0.3.schema.json",
        6,
        8,
    ),
}

EXPECTED_V03_ERRORS = {
    "missing-predecessor.json":
        "MISSING_PREDECESSOR",
    "circular-lineage.json":
        "CIRCULAR_LINEAGE",
    "cross-target-lineage.json":
        "CROSS_TARGET_LINEAGE",
    "verification-before-repair.json":
        "VERIFICATION_BEFORE_REPAIR",
    "release-without-approval.json":
        "RELEASE_WITHOUT_APPROVAL",
    "release-with-active-hold.json":
        "RELEASE_WITH_ACTIVE_HOLD",
    "invalid-evidence-binding.json":
        "INVALID_EVIDENCE_BINDING",
    "revoked-authorization-reuse.json":
        "REVOKED_AUTHORIZATION_REUSE",
}

ACTIVE = {"authorized", "executed", "verified"}

ROLES = {
    "diagnose": "diagnostic",
    "contain": "containment",
    "repair": "repair",
    "verify": "verification",
    "replace": "replacement",
}

TRANSITIONS = {
    "authorization_granted": {
        ("observed", "authorized"),
    },
    "operation_held": {
        (state, "held")
        for state in (
            "observed",
            "authorized",
            "contained",
            "repairing",
            "verification_pending",
        )
    },
    "containment_applied": {
        ("authorized", "contained"),
    },
    "repair_started": {
        ("contained", "repairing"),
    },
    "repair_completed": {
        ("repairing", "verification_pending"),
    },
    "verification_passed": {
        ("verification_pending", "verified"),
    },
    "verification_failed": {
        ("verification_pending", "failed"),
    },
    "release_approved": {
        ("verified", "verified"),
    },
    "containment_released": {
        ("verified", "released"),
    },
    "authorization_revoked": {
        (state, "held")
        for state in (
            "authorized",
            "contained",
            "repairing",
            "verification_pending",
        )
    },
    "authorization_expired": {
        (state, "held")
        for state in (
            "authorized",
            "contained",
            "repairing",
            "verification_pending",
        )
    },
    "hold_resolved": {
        ("held", "authorized"),
        ("held", "contained"),
    },
}

PERMISSIONS = {
    "containment_applied": "contain",
    "repair_started": "repair",
    "repair_completed": "repair",
    "verification_passed": "verify",
    "verification_failed": "verify",
    "release_approved": "release",
    "containment_released": "release",
    "hold_resolved": "resolve_hold",
}

AUTHORIZED_EVENTS = set(PERMISSIONS)

EXECUTION_EVENTS = {
    "containment_applied",
    "repair_started",
    "repair_completed",
    "containment_released",
}

GATE_CONDITIONS = {
    "lineage_continuity",
    "containment_exists",
    "repair_authorized",
    "repair_completed",
    "independent_verification",
    "verification_evidence",
    "release_approved",
    "release_authorized",
    "no_active_hold",
    "no_revoked_authorization",
    "no_expired_authorization",
    "evidence_integrity",
    "source_records_resolved",
}


class SemanticError(ValueError):
    pass


def require(
    condition: bool,
    code: str,
    detail: str = "",
) -> None:
    if not condition:
        message = code
        if detail:
            message += f": {detail}"
        raise SemanticError(message)


def read_object(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        result = json.load(handle)

    if not isinstance(result, dict):
        raise ValueError(
            f"JSON root must be an object: {path}"
        )

    return result


def instant(value: str) -> datetime:
    result = datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )
    require(
        result.utcoffset() is not None,
        "TIMEZONE_REQUIRED",
    )
    return result


def make_validator(
    schema_path: Path,
) -> Draft202012Validator:
    schema = read_object(schema_path)
    Draft202012Validator.check_schema(schema)

    return Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    )


def schema_errors(
    record: dict[str, Any],
    validator: Draft202012Validator,
) -> list[Any]:
    return sorted(
        validator.iter_errors(record),
        key=lambda error: (
            tuple(map(str, error.absolute_path)),
            error.message,
        ),
    )


def check_schema(
    record: dict[str, Any],
    validator: Draft202012Validator,
) -> None:
    errors = schema_errors(record, validator)

    if errors:
        error = errors[0]
        location = "/".join(
            map(str, error.absolute_path)
        ) or "<root>"

        raise SemanticError(
            f"SCHEMA_ERROR at {location}: "
            f"{error.message}"
        )


def temporal_bounds(
    authority: dict[str, Any],
    event_time: datetime,
) -> None:
    issued = authority.get("issued_at")
    expiry = authority.get("expires_at")
    revoked = authority.get("revoked_at")

    if issued:
        issue_time = instant(issued)
        require(
            event_time >= issue_time,
            "AUTHORIZATION_NOT_YET_VALID",
        )
    else:
        issue_time = None

    if expiry:
        expiry_time = instant(expiry)

        if issue_time:
            require(
                expiry_time > issue_time,
                "INVALID_AUTHORIZATION_TIME_RANGE",
            )

        require(
            event_time < expiry_time,
            "EXPIRED_AUTHORIZATION_EXECUTION",
        )

    if revoked:
        revoked_time = instant(revoked)

        if issue_time:
            require(
                revoked_time >= issue_time,
                "REVOCATION_BEFORE_ISSUANCE",
            )

        require(
            event_time < revoked_time,
            "REVOKED_AUTHORIZATION_EXECUTION",
        )


# ============================================================
# v0.1 semantic validation
# ============================================================

def semantic_v01(record: dict[str, Any]) -> None:
    operation = record["operation"]
    agent = record["mini_agent"]
    target = record["target"]
    authority = record["authority"]
    verification = record["verification"]

    kind = operation["operation_type"]
    status = operation["status"]

    require(
        agent["role"] == ROLES[kind],
        "ROLE_MISMATCH",
    )

    require(
        operation["state_changing"] is (
            kind != "diagnose"
        ),
        "INVALID_STATE_CHANGE_FLAG",
    )

    require(
        operation["scope"] in target["authorized_scope"],
        "OUT_OF_SCOPE_INTERVENTION",
    )

    if operation["state_changing"] and status in ACTIVE:
        require(
            authority["authorization_status"] == "granted",
            "AUTHORIZATION_NOT_GRANTED",
        )

        require(
            bool(authority.get("authorization_id")),
            "MISSING_AUTHORIZATION_ID",
        )

        require(
            kind in authority.get(
                "authorized_operations", []
            ),
            "UNAUTHORIZED_OPERATION_TYPE",
        )

        require(
            agent["mini_agent_id"] != authority[
                "controller_id"
            ],
            "SELF_AUTHORIZATION",
        )

    if kind == "replace" and status in ACTIVE:
        require(
            target.get("replaceable") is True,
            "TARGET_NOT_REPLACEABLE",
        )

    ids = verification.get(
        "verification_evidence_ids", []
    )

    require(
        set(ids).issubset(set(record["evidence"])),
        "INVALID_VERIFICATION_EVIDENCE_REFERENCE",
    )

    if status == "verified":
        require(
            verification["verification_status"] == "passed",
            "VERIFICATION_NOT_PASSED",
        )

        require(
            bool(verification.get("verifier_id")),
            "MISSING_VERIFIER",
        )

        require(
            verification["verifier_id"]
            != agent["mini_agent_id"],
            "SELF_VERIFICATION",
        )

        require(
            bool(ids),
            "MISSING_VERIFICATION_EVIDENCE",
        )
    else:
        require(
            verification["verification_status"] != "passed",
            "UNCONFIRMED_VERIFICATION_STATUS",
        )


# ============================================================
# v0.2 semantic validation
# ============================================================

def semantic_v02(record: dict[str, Any]) -> None:
    event = record["event_type"]
    transition = (
        record["previous_state"],
        record["next_state"],
    )

    require(
        transition in TRANSITIONS[event],
        "INVALID_LIFECYCLE_TRANSITION",
    )

    authority = record["authority"]
    verification = record["verification"]
    containment = record.get("containment")
    hold = record.get("hold")

    now = instant(record["timestamp"])

    ids = verification.get(
        "verification_evidence_ids", []
    )

    require(
        set(ids).issubset(set(record["evidence"])),
        "INVALID_VERIFICATION_EVIDENCE_REFERENCE",
    )

    if event in AUTHORIZED_EVENTS:
        require(
            authority["authorization_status"] == "granted",
            "AUTHORIZATION_NOT_GRANTED",
        )

        require(
            bool(authority.get("authorization_id")),
            "MISSING_AUTHORIZATION_ID",
        )

        require(
            PERMISSIONS[event] in authority.get(
                "authorized_operations", []
            ),
            "UNAUTHORIZED_OPERATION_TYPE",
        )

        if event in EXECUTION_EVENTS:
            require(
                bool(authority.get("issued_at"))
                and bool(authority.get("expires_at")),
                "AUTHORIZATION_TIME_BOUNDARY_MISSING",
            )

        temporal_bounds(authority, now)

        require(
            record["actor_id"] != authority["controller_id"],
            "SELF_AUTHORIZATION",
        )

        if containment:
            require(
                containment["scope"] in authority.get(
                    "authorized_scopes", []
                ),
                "OUT_OF_SCOPE_INTERVENTION",
            )

    if containment:
        if "applied_at" in containment:
            require(
                instant(containment["applied_at"]) <= now,
                "CONTAINMENT_APPLIED_IN_FUTURE",
            )

        if "released_at" in containment:
            released = instant(
                containment["released_at"]
            )

            require(
                released <= now,
                "RELEASE_TIMESTAMP_IN_FUTURE",
            )

            if "applied_at" in containment:
                require(
                    instant(containment["applied_at"])
                    <= released,
                    "RELEASE_BEFORE_CONTAINMENT",
                )

    if event in (
        "containment_applied",
        "repair_started",
    ):
        require(
            containment is not None
            and containment["status"] == "active",
            "CONTAINMENT_NOT_ACTIVE",
        )

    if event == "operation_held":
        require(
            hold is not None
            and hold["status"] == "active",
            "HOLD_NOT_ACTIVE",
        )

    if event in (
        "authorization_revoked",
        "authorization_expired",
    ):
        expected = (
            "revoked"
            if event == "authorization_revoked"
            else "expired"
        )

        require(
            authority["authorization_status"] == expected,
            "AUTHORIZATION_STATUS_EVENT_MISMATCH",
        )

        require(
            hold is not None
            and hold["status"] == "active",
            "HOLD_NOT_ACTIVE",
        )

        if event == "authorization_revoked":
            require(
                record["actor_id"]
                == authority["controller_id"],
                "REVOCATION_ACTOR_MISMATCH",
            )

            require(
                bool(authority.get("revoked_at")),
                "MISSING_REVOCATION_TIMESTAMP",
            )

            require(
                instant(authority["revoked_at"]) == now,
                "REVOCATION_TIMESTAMP_MISMATCH",
            )

        if containment:
            require(
                containment["status"] == "active",
                "CONTAINMENT_NOT_PRESERVED",
            )

    if event == "verification_passed":
        require(
            verification["verification_status"] == "passed",
            "VERIFICATION_NOT_PASSED",
        )

        require(
            record["actor_id"]
            == verification.get("verifier_id"),
            "VERIFIER_ACTOR_MISMATCH",
        )

        require(
            bool(ids),
            "MISSING_VERIFICATION_EVIDENCE",
        )

        if containment:
            require(
                containment["status"] == "active",
                "PREMATURE_CONTAINMENT_RELEASE",
            )

    if event == "release_approved":
        require(
            containment is not None
            and containment["status"] == "release_pending",
            "RELEASE_NOT_PENDING",
        )

    if event == "containment_released":
        require(
            verification["verification_status"] == "passed",
            "RELEASE_WITHOUT_VERIFICATION",
        )

        require(
            bool(ids),
            "MISSING_RELEASE_VERIFICATION_EVIDENCE",
        )

        require(
            containment is not None
            and containment["status"] == "released",
            "CONTAINMENT_NOT_RELEASED",
        )

        require(
            bool(containment.get("released_at")),
            "MISSING_RELEASE_TIMESTAMP",
        )

        require(
            instant(containment["released_at"]) == now,
            "RELEASE_TIMESTAMP_MISMATCH",
        )

        require(
            hold is None or hold["status"] != "active",
            "RELEASE_WHILE_HELD",
        )


# ============================================================
# v0.3 lineage validation
# ============================================================

def source_path(reference: str) -> Path:
    base = (
        ROOT / "examples" / "v0.3" / "sources"
    ).resolve()

    path = (ROOT / reference).resolve()

    require(
        path.is_relative_to(base),
        "UNSAFE_SOURCE_REFERENCE",
        reference,
    )

    require(
        path.suffix == ".json",
        "INVALID_SOURCE_EXTENSION",
        reference,
    )

    return path


def check_lineage_graph(
    records: list[dict[str, Any]],
) -> None:
    ids = [item["event_id"] for item in records]

    require(
        len(ids) == len(set(ids)),
        "DUPLICATE_EVENT_ID",
    )

    by_id = {
        item["event_id"]: item
        for item in records
    }

    for item in records:
        predecessor = item["previous_event_id"]

        if predecessor is not None:
            require(
                predecessor in by_id,
                "MISSING_PREDECESSOR",
                f"{item['event_id']} -> {predecessor}",
            )

    # Cycle detection precedes linear-order checks.
    visited: set[str] = set()
    active: set[str] = set()

    def visit(event_id: str) -> None:
        if event_id in active:
            raise SemanticError(
                f"CIRCULAR_LINEAGE: {event_id}"
            )

        if event_id in visited:
            return

        active.add(event_id)

        predecessor = by_id[event_id][
            "previous_event_id"
        ]

        if predecessor is not None:
            visit(predecessor)

        active.remove(event_id)
        visited.add(event_id)

    for event_id in ids:
        visit(event_id)

    require(
        records[0]["previous_event_id"] is None,
        "INVALID_LINEAGE_ROOT",
    )

    for previous, current in zip(
        records, records[1:]
    ):
        require(
            current["previous_event_id"]
            == previous["event_id"],
            "LINEAGE_DISCONTINUITY",
            current["event_id"],
        )


def check_v03_source(
    bundle: dict[str, Any],
    record: dict[str, Any],
    schemas: dict[str, Draft202012Validator],
) -> dict[str, Any]:
    path = source_path(record["record_reference"])

    require(
        path.is_file(),
        "SOURCE_RECORD_NOT_FOUND",
        str(path.relative_to(ROOT)),
    )

    source = read_object(path)

    version = record["source_version"]

    if version == "0.2.0":
        check_schema(source, schemas["v0.2"])

    elif (
        version == "0.3.0"
        and record["event_type"] == "hold_resolved"
    ):
        check_schema(source, schemas["hold"])

    else:
        raise SemanticError(
            f"UNSUPPORTED_SOURCE_VERSION: {version}"
        )

    for field in (
        "operation_id",
        "target_id",
        "actor_id",
        "event_type",
        "previous_state",
        "next_state",
        "timestamp",
    ):
        require(
            source[field] == record[field],
            "SOURCE_METADATA_MISMATCH",
            field,
        )

    require(
        source["schema_version"] == version,
        "SOURCE_VERSION_MISMATCH",
    )

    if version == "0.2.0":
        containment = source.get("containment")

        if containment:
            require(
                containment["containment_id"]
                == bundle["containment_id"],
                "SOURCE_CONTAINMENT_MISMATCH",
            )
    else:
        require(
            source["containment_id"]
            == bundle["containment_id"],
            "SOURCE_CONTAINMENT_MISMATCH",
        )

    return source


def check_evidence(
    bundle: dict[str, Any],
    sources: dict[str, dict[str, Any]],
) -> None:
    records = {
        record["event_id"]: record
        for record in bundle["records"]
    }

    seen: set[str] = set()

    for evidence in bundle["evidence_bindings"]:
        evidence_id = evidence["evidence_id"]

        require(
            evidence_id not in seen,
            "DUPLICATE_EVIDENCE_ID",
        )
        seen.add(evidence_id)

        event_id = evidence["event_id"]

        require(
            event_id in records,
            "INVALID_EVIDENCE_BINDING",
            f"unknown event {event_id}",
        )

        event = records[event_id]

        require(
            evidence["target_id"]
            == bundle["target_id"],
            "INVALID_EVIDENCE_BINDING",
            evidence_id,
        )

        require(
            evidence["operation_id"]
            == event["operation_id"],
            "INVALID_EVIDENCE_BINDING",
            evidence_id,
        )

        source = sources[event_id]

        require(
            evidence_id in source["evidence"],
            "INVALID_EVIDENCE_BINDING",
            evidence_id,
        )

    for record in bundle["records"]:
        source = sources[record["event_id"]]

        ids = {
            item["evidence_id"]
            for item in bundle["evidence_bindings"]
            if item["event_id"] == record["event_id"]
        }

        require(
            set(source["evidence"]) == ids,
            "SOURCE_EVIDENCE_MISMATCH",
            record["event_id"],
        )

    gate = bundle["recovery_gate"]

    require(
        set(gate["evidence_references"]).issubset(seen),
        "INVALID_GATE_EVIDENCE_REFERENCE",
    )

    for record in bundle["records"]:
        if record["event_type"] == "verification_passed":
            source = sources[record["event_id"]]

            verification_ids = set(
                source["verification"].get(
                    "verification_evidence_ids", []
                )
            )

            bound_ids = {
                item["evidence_id"]
                for item in bundle["evidence_bindings"]
                if (
                    item["event_id"] == record["event_id"]
                    and item["evidence_type"]
                    == "verification"
                )
            }

            require(
                bool(bound_ids)
                and verification_ids == bound_ids,
                "INVALID_VERIFICATION_EVIDENCE",
                record["event_id"],
            )


def check_authorizations(
    bundle: dict[str, Any],
) -> None:
    bindings = bundle.get(
        "authorization_bindings", []
    )

    by_id: dict[str, dict[str, Any]] = {}

    for binding in bindings:
        authorization_id = binding[
            "authorization_id"
        ]

        require(
            authorization_id not in by_id,
            "DUPLICATE_AUTHORIZATION_ID",
        )

        by_id[authorization_id] = binding

    revoked: dict[str, datetime] = {}

    for record in bundle["records"]:
        event = record["event_type"]
        when = instant(record["timestamp"])

        if event == "authorization_revoked":
            authorization_id = record[
                "authorization_id"
            ]

            revoked[authorization_id] = when

        if event not in AUTHORIZED_EVENTS:
            continue

        authorization_id = record.get(
            "authorization_id"
        )

        require(
            authorization_id in by_id,
            "MISSING_AUTHORIZATION_BINDING",
            record["event_id"],
        )

        binding = by_id[authorization_id]

        if event == "release_approved":
            require(
                record["actor_id"]
                == binding["controller_id"],
                "RELEASE_APPROVAL_ACTOR_MISMATCH",
            )

        else:
            require(
                record["actor_id"]
                == binding["authorized_actor_id"],
                "AUTHORIZATION_ACTOR_MISMATCH",
            )

        require(
            PERMISSIONS[event]
            in binding["authorized_operations"],
            "UNAUTHORIZED_OPERATION_TYPE",
            record["event_id"],
        )

        issued = instant(binding["issued_at"])

        require(
            when >= issued,
            "AUTHORIZATION_NOT_YET_VALID",
        )

        if binding.get("expires_at"):
            expiry = instant(
                binding["expires_at"]
            )

            require(
                when < expiry,
                "EXPIRED_AUTHORIZATION_EXECUTION",
                record["event_id"],
            )

        revocation_time = revoked.get(
            authorization_id
        )

        if binding.get("revoked_at"):
            declared = instant(
                binding["revoked_at"]
            )

            if (
                revocation_time is None
                or declared < revocation_time
            ):
                revocation_time = declared

        if (
            revocation_time is not None
            and when >= revocation_time
        ):
            raise SemanticError(
                "REVOKED_AUTHORIZATION_REUSE: "
                + record["event_id"]
            )

        require(
            record["actor_id"]
            != binding["controller_id"]
            or event == "release_approved",
            "SELF_AUTHORIZATION",
            record["event_id"],
        )


def check_causality(
    bundle: dict[str, Any],
) -> tuple[set[str], set[str]]:
    records = bundle["records"]

    completed = False
    verified = False
    contained = False
    approval = False

    active_holds: set[str] = set()
    resolved_holds: set[str] = set()

    previous = None

    for record in records:
        event = record["event_type"]
        when = instant(record["timestamp"])

        if previous is not None:
            require(
                when >= instant(previous["timestamp"]),
                "INVALID_EVENT_ORDER",
            )

        # Prefer specific safety failures over generic
        # state-continuity errors.
        if event == "verification_passed":
            require(
                completed,
                "VERIFICATION_BEFORE_REPAIR",
                record["event_id"],
            )

        if event == "containment_released":
            require(
                not active_holds,
                "RELEASE_WITH_ACTIVE_HOLD",
                ",".join(sorted(active_holds)),
            )

            require(
                approval,
                "RELEASE_WITHOUT_APPROVAL",
                record["event_id"],
            )

            require(
                verified,
                "RELEASE_WITHOUT_VERIFICATION",
            )

        transition = (
            record["previous_state"],
            record["next_state"],
        )

        require(
            transition in TRANSITIONS[event],
            "INVALID_LIFECYCLE_TRANSITION",
            record["event_id"],
        )

        if previous is not None:
            require(
                previous["next_state"]
                == record["previous_state"],
                "INVALID_STATE_CONTINUITY",
                record["event_id"],
            )

        if event == "containment_applied":
            contained = True

        elif event == "repair_completed":
            completed = True

        elif event == "verification_passed":
            verified = True

            require(
                record["actor_id"]
                != record["repair_agent_id"],
                "SELF_VERIFICATION",
            )

            repairers = {
                item["actor_id"]
                for item in records
                if (
                    item["event_type"]
                    in ("repair_started", "repair_completed")
                    and instant(item["timestamp"]) < when
                )
            }

            require(
                record["repair_agent_id"]
                in repairers
                and record["actor_id"] not in repairers,
                "INDEPENDENT_VERIFIER_MISMATCH",
            )

        elif event == "operation_held":
            active_holds.add(record["hold_id"])

        elif event in (
            "authorization_revoked",
            "authorization_expired",
        ):
            active_holds.add(record["hold_id"])

        elif event == "hold_resolved":
            hold_id = record["hold_id"]

            require(
                hold_id in active_holds,
                "HOLD_NOT_ACTIVE",
                hold_id,
            )

            active_holds.remove(hold_id)
            resolved_holds.add(hold_id)

        elif event == "release_approved":
            require(
                verified,
                "RELEASE_APPROVAL_WITHOUT_VERIFICATION",
            )
            approval = True

        elif event == "containment_released":
            require(
                contained,
                "RELEASE_WITHOUT_CONTAINMENT",
            )

        previous = record

    return active_holds, resolved_holds


def check_recovery_gate(
    bundle: dict[str, Any],
    active_holds: set[str],
) -> None:
    records = bundle["records"]
    gate = bundle["recovery_gate"]

    event_ids = {
        record["event_id"]
        for record in records
    }

    require(
        gate["evaluated_event_id"] in event_ids,
        "INVALID_GATE_EVENT_REFERENCE",
    )

    cutoff = next(
        record for record in records
        if record["event_id"]
        == gate["evaluated_event_id"]
    )

    require(
        instant(gate["evaluated_at"])
        == instant(cutoff["timestamp"]),
        "GATE_TIME_MISMATCH",
    )

    require(
        instant(bundle["evaluated_at"])
        == instant(gate["evaluated_at"]),
        "BUNDLE_GATE_TIME_MISMATCH",
    )

    require(
        cutoff is records[-1],
        "GATE_CUTOFF_NOT_FINAL",
    )

    satisfied = set(gate["satisfied_conditions"])
    blocking = set(gate["blocking_conditions"])

    require(
        satisfied.isdisjoint(blocking),
        "GATE_CONDITION_CONFLICT",
    )

    require(
        (satisfied | blocking).issubset(
            GATE_CONDITIONS
        ),
        "UNKNOWN_GATE_CONDITION",
    )

    events = {
        record["event_type"]
        for record in records
    }

    release = "containment_released" in events
    approval = "release_approved" in events
    verification = "verification_passed" in events
    repair = "repair_completed" in events

    if active_holds:
        expected = "denied"
        require(
            "no_active_hold" in blocking,
            "GATE_HOLD_MISMATCH",
        )

    elif release:
        require(
            approval and verification and repair,
            "INVALID_RELEASE_CHAIN",
        )
        expected = "allowed"

    else:
        expected = "indeterminate"

    require(
        gate["decision"] == expected,
        "RECOVERY_GATE_MISMATCH",
        f"expected={expected}, "
        f"actual={gate['decision']}",
    )

    if expected == "allowed":
        require(
            not blocking,
            "GATE_BLOCKING_CONDITIONS_PRESENT",
        )

        require(
            GATE_CONDITIONS.issubset(satisfied),
            "GATE_REQUIRED_CONDITIONS_MISSING",
        )

    if expected == "indeterminate":
        missing = {
            "repair_completed": repair,
            "independent_verification": verification,
            "release_approved": approval,
            "release_authorized": approval,
        }

        for condition, established in missing.items():
            if not established:
                require(
                    condition in blocking,
                    "GATE_MISSING_CONDITION",
                    condition,
                )


def semantic_v03(
    bundle: dict[str, Any],
    schemas: dict[str, Draft202012Validator],
) -> None:
    records = bundle["records"]

    check_lineage_graph(records)

    # Check cross-target mixing before resolving sources.
    for record in records:
        require(
            record["target_id"] == bundle["target_id"],
            "CROSS_TARGET_LINEAGE",
            record["event_id"],
        )

    # Check known invalid causality patterns early,
    # without treating a broken fixture as a valid source.
    events_seen: set[str] = set()
    active_holds: set[str] = set()
    revoked: set[str] = set()

    for record in records:
        event = record["event_type"]

        if event == "verification_passed":
            require(
                "repair_completed" in events_seen,
                "VERIFICATION_BEFORE_REPAIR",
            )

        if event == "containment_released":
            require(
                not active_holds,
                "RELEASE_WITH_ACTIVE_HOLD",
            )

            require(
                "release_approved" in events_seen,
                "RELEASE_WITHOUT_APPROVAL",
            )

        if event in AUTHORIZED_EVENTS:
            require(
                record.get("authorization_id")
                not in revoked,
                "REVOKED_AUTHORIZATION_REUSE",
            )

        if event in (
            "operation_held",
            "authorization_revoked",
            "authorization_expired",
        ):
            active_holds.add(record["hold_id"])

        elif event == "hold_resolved":
            active_holds.discard(record["hold_id"])

        if event == "authorization_revoked":
            revoked.add(record["authorization_id"])

        events_seen.add(event)

    sources = {}

    for record in records:
        sources[record["event_id"]] = check_v03_source(
            bundle,
            record,
            schemas,
        )

    check_evidence(bundle, sources)
    check_authorizations(bundle)

    active_holds, _ = check_causality(bundle)

    check_recovery_gate(
        bundle,
        active_holds,
    )


# ============================================================
# Fixture evaluation
# ============================================================

def validate_fixture(
    record: dict[str, Any],
    version: str,
    schemas: dict[str, Draft202012Validator],
) -> tuple[str, str]:
    try:
        check_schema(record, schemas[version])

        if version == "v0.1":
            semantic_v01(record)

        elif version == "v0.2":
            semantic_v02(record)

        elif version == "v0.3":
            semantic_v03(record, schemas)

        else:
            raise ValueError(
                f"Unknown version: {version}"
            )

    except SemanticError as exc:
        return "FAIL", str(exc)

    return "PASS", "VALID"


def run_fixtures(
    version: str,
    count_pass: int,
    count_fail: int,
    schemas: dict[str, Draft202012Validator],
) -> tuple[int, int]:
    total = 0
    matched = 0

    print(f"\n[version] {version}")

    for category, count, expected in (
        ("pass", count_pass, "PASS"),
        ("fail", count_fail, "FAIL"),
    ):
        directory = (
            ROOT / "examples" / version / category
        )

        if not directory.is_dir():
            raise ValueError(
                f"Missing fixture directory: {directory}"
            )

        paths = sorted(
            directory.glob("*.json")
        )

        if len(paths) != count:
            raise ValueError(
                f"{version}/{category}: "
                f"expected {count} files, "
                f"found {len(paths)}"
            )

        for path in paths:
            total += 1

            try:
                fixture = read_object(path)
                declared = fixture.pop(
                    "expected_result", None
                )

                require(
                    declared == expected,
                    "INVALID_EXPECTED_RESULT",
                    path.name,
                )

                actual, reason = validate_fixture(
                    fixture,
                    version,
                    schemas,
                )

                ok = actual == expected

                if (
                    ok
                    and version == "v0.3"
                    and category == "fail"
                ):
                    expected_error = (
                        EXPECTED_V03_ERRORS.get(
                            path.name
                        )
                    )

                    require(
                        expected_error is not None,
                        "UNKNOWN_FAIL_FIXTURE",
                    )

                    actual_error = reason.split(
                        ":", 1
                    )[0]

                    ok = (
                        actual_error == expected_error
                    )

                    if not ok:
                        reason += (
                            f"; expected_error="
                            f"{expected_error}"
                        )

            except (
                OSError,
                ValueError,
                KeyError,
                TypeError,
            ) as exc:
                actual = "INVALID_FIXTURE"
                reason = str(exc)
                ok = False

            if ok:
                matched += 1

            label = (
                "MATCH" if ok else "MISMATCH"
            )

            print(
                f"[{label}] "
                f"{path.relative_to(ROOT)} "
                f"expected={expected} actual={actual}"
            )

            if actual != "PASS":
                print(f"  reason: {reason}")

    print(f"[completed] {version}")

    return total, matched


def main() -> int:
    print(
        "=== MARP v0.1 + v0.2 + v0.3 Validation ==="
    )

    schemas = {}

    for version, (
        schema_rel,
        _,
        _,
    ) in VERSIONS.items():
        path = ROOT / schema_rel
        schemas[version] = make_validator(path)
        print(f"[schema-ok] {schema_rel}")

    hold_schema = (
        ROOT
        / "schemas"
        / "hold-resolution-v0.3.schema.json"
    )

    schemas["hold"] = make_validator(
        hold_schema
    )

    print(
        "[schema-ok] "
        "schemas/hold-resolution-v0.3.schema.json"
    )

    require(
        set(EXPECTED_V03_ERRORS)
        == {
            path.name
            for path in (
                ROOT / "examples" / "v0.3" / "fail"
            ).glob("*.json")
        },
        "FAIL_FIXTURE_MANIFEST_MISMATCH",
    )

    total = 0
    matched = 0

    for version, (
        _,
        count_pass,
        count_fail,
    ) in VERSIONS.items():
        version_total, version_matched = (
            run_fixtures(
                version,
                count_pass,
                count_fail,
                schemas,
            )
        )

        total += version_total
        matched += version_matched

    print("\n=== MARP Summary ===")
    print(f"Total: {total}")
    print(f"Matched: {matched}")
    print(f"Mismatched: {total - matched}")

    if total != 36 or matched != total:
        print(
            "[FAIL] MARP conformance mismatch"
        )
        return 1

    print(
        "[PASS] All MARP v0.1-v0.3 "
        "expectations matched"
    )

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())

    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
    ) as exc:
        print(f"[FATAL] {exc}")
        sys.exit(1)
