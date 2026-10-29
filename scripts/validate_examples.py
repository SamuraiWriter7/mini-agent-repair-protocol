#!/usr/bin/env python3
"""
Mini-Agent Repair Protocol (MARP)
Integrated Fixture Validator v0.1-v0.4

v0.1:
    Repair records, scope, authority, and verification.

v0.2:
    Repair lifecycle, holds, containment, revocation,
    and recovery transitions.

v0.3:
    Repair lineage, causal history, evidence bindings,
    source records, and independent recovery gates.

v0.4:
    Multi-agent coordination, dependencies, concurrency,
    conflict control, authorization boundaries,
    independent verification, and reconciliation.

Expected fixture counts:
    v0.1:  4 PASS + 6 FAIL = 10
    v0.2:  6 PASS + 6 FAIL = 12
    v0.3:  6 PASS + 8 FAIL = 14
    v0.4:  6 PASS + 8 FAIL = 14
    Total: 50

Passing synthetic fixtures does not establish real-world
authorization authenticity or runtime safety.
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
    "v0.4": (
        "schemas/repair-coordination-v0.4.schema.json",
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

EXPECTED_V04_ERRORS = {
    "cyclic-task-dependency.json":
        "CYCLIC_TASK_DEPENDENCY",
    "unknown-task-dependency.json":
        "UNKNOWN_TASK_DEPENDENCY",
    "concurrent-write-conflict.json":
        "CONCURRENT_WRITE_CONFLICT",
    "concurrency-budget-exceeded.json":
        "CONCURRENCY_BUDGET_EXCEEDED",
    "unauthorized-task-scope.json":
        "UNAUTHORIZED_TASK_SCOPE",
    "self-verification-accepted.json":
        "SELF_VERIFICATION_ACCEPTED",
    "unresolved-conflict-accepted.json":
        "UNRESOLVED_CONFLICT_ACCEPTED",
    "revoked-task-dispatched.json":
        "REVOKED_TASK_DISPATCHED",
}

ACTIVE = {
    "authorized",
    "executed",
    "verified",
}

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


# ============================================================
# Common utilities
# ============================================================

class SemanticError(ValueError):
    """Raised when a semantic invariant is violated."""


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
# MARP v0.1
# Repair record validation
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
        operation["state_changing"]
        is (kind != "diagnose"),
        "INVALID_STATE_CHANGE_FLAG",
    )

    require(
        operation["scope"]
        in target["authorized_scope"],
        "OUT_OF_SCOPE_INTERVENTION",
    )

    if (
        operation["state_changing"]
        and status in ACTIVE
    ):
        require(
            authority["authorization_status"]
            == "granted",
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
            agent["mini_agent_id"]
            != authority["controller_id"],
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
            verification["verification_status"]
            == "passed",
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
            verification["verification_status"]
            != "passed",
            "UNCONFIRMED_VERIFICATION_STATUS",
        )


# ============================================================
# MARP v0.2
# Lifecycle validation
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
            authority["authorization_status"]
            == "granted",
            "AUTHORIZATION_NOT_GRANTED",
        )

        require(
            bool(authority.get("authorization_id")),
            "MISSING_AUTHORIZATION_ID",
        )

        require(
            PERMISSIONS[event]
            in authority.get(
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
            record["actor_id"]
            != authority["controller_id"],
            "SELF_AUTHORIZATION",
        )

        if containment:
            require(
                containment["scope"]
                in authority.get(
                    "authorized_scopes", []
                ),
                "OUT_OF_SCOPE_INTERVENTION",
            )

    if containment:
        if "applied_at" in containment:
            require(
                instant(containment["applied_at"])
                <= now,
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
            authority["authorization_status"]
            == expected,
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
                instant(authority["revoked_at"])
                == now,
                "REVOCATION_TIMESTAMP_MISMATCH",
            )

        if containment:
            require(
                containment["status"] == "active",
                "CONTAINMENT_NOT_PRESERVED",
            )

    if event == "verification_passed":
        require(
            verification["verification_status"]
            == "passed",
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
            and containment["status"]
            == "release_pending",
            "RELEASE_NOT_PENDING",
        )

    if event == "containment_released":
        require(
            verification["verification_status"]
            == "passed",
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
            instant(containment["released_at"])
            == now,
            "RELEASE_TIMESTAMP_MISMATCH",
        )

        require(
            hold is None
            or hold["status"] != "active",
            "RELEASE_WHILE_HELD",
        )


# ============================================================
# MARP v0.3
# Lineage and causal verification
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
    ids = [
        item["event_id"]
        for item in records
    ]

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
                f"{item['event_id']} -> "
                f"{predecessor}",
            )

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
        records,
        records[1:],
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
    path = source_path(
        record["record_reference"]
    )

    require(
        path.is_file(),
        "SOURCE_RECORD_NOT_FOUND",
        str(path.relative_to(ROOT)),
    )

    source = read_object(path)
    version = record["source_version"]

    if version == "0.2.0":
        check_schema(
            source,
            schemas["v0.2"],
        )

    elif (
        version == "0.3.0"
        and record["event_type"] == "hold_resolved"
    ):
        check_schema(
            source,
            schemas["hold"],
        )

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
            if item["event_id"]
            == record["event_id"]
        }

        require(
            set(source["evidence"]) == ids,
            "SOURCE_EVIDENCE_MISMATCH",
            record["event_id"],
        )

    gate = bundle["recovery_gate"]

    require(
        set(gate["evidence_references"])
        .issubset(seen),
        "INVALID_GATE_EVIDENCE_REFERENCE",
    )

    for record in bundle["records"]:
        if record["event_type"] != "verification_passed":
            continue

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
                item["event_id"]
                == record["event_id"]
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
                    in (
                        "repair_started",
                        "repair_completed",
                    )
                    and instant(item["timestamp"])
                    < when
                )
            }

            require(
                record["repair_agent_id"]
                in repairers
                and record["actor_id"]
                not in repairers,
                "INDEPENDENT_VERIFIER_MISMATCH",
            )

        elif event == "operation_held":
            active_holds.add(
                record["hold_id"]
            )

        elif event in (
            "authorization_revoked",
            "authorization_expired",
        ):
            active_holds.add(
                record["hold_id"]
            )

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
        record
        for record in records
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

    satisfied = set(
        gate["satisfied_conditions"]
    )

    blocking = set(
        gate["blocking_conditions"]
    )

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
            "independent_verification":
                verification,
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

    for record in records:
        require(
            record["target_id"]
            == bundle["target_id"],
            "CROSS_TARGET_LINEAGE",
            record["event_id"],
        )

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
            active_holds.discard(
                record["hold_id"]
            )

        if event == "authorization_revoked":
            revoked.add(
                record["authorization_id"]
            )

        events_seen.add(event)

    sources = {}

    for record in records:
        sources[record["event_id"]] = (
            check_v03_source(
                bundle,
                record,
                schemas,
            )
        )

    check_evidence(bundle, sources)
    check_authorizations(bundle)

    active_holds, _ = check_causality(
        bundle
    )

    check_recovery_gate(
        bundle,
        active_holds,
    )


# ============================================================
# MARP v0.4
# Distributed repair coordination
# ============================================================

def check_unique_v04(
    values: list[str],
    error_code: str,
) -> None:
    require(
        len(values) == len(set(values)),
        error_code,
    )


def task_interval_v04(
    task: dict[str, Any],
    evaluated_at: str,
) -> tuple[datetime, datetime]:
    start = instant(task["started_at"])

    if task["status"] == "completed":
        end = instant(task["completed_at"])
    else:
        end = instant(evaluated_at)

    require(
        start < end,
        "INVALID_TASK_TIME_RANGE",
        task["task_id"],
    )

    return start, end


def intervals_overlap_v04(
    left: dict[str, Any],
    right: dict[str, Any],
    evaluated_at: str,
) -> bool:
    left_start, left_end = task_interval_v04(
        left,
        evaluated_at,
    )

    right_start, right_end = task_interval_v04(
        right,
        evaluated_at,
    )

    return (
        left_start < right_end
        and right_start < left_end
    )


def check_dependencies_v04(
    tasks: list[dict[str, Any]],
    by_task: dict[str, dict[str, Any]],
) -> None:
    # Unknown references are checked before cycles.
    for task in tasks:
        for dependency in task["depends_on"]:
            require(
                dependency in by_task,
                "UNKNOWN_TASK_DEPENDENCY",
                f"{task['task_id']} -> "
                f"{dependency}",
            )

    visited: set[str] = set()
    active: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in active:
            raise SemanticError(
                "CYCLIC_TASK_DEPENDENCY: "
                + task_id
            )

        if task_id in visited:
            return

        active.add(task_id)

        for predecessor in by_task[
            task_id
        ]["depends_on"]:
            visit(predecessor)

        active.remove(task_id)
        visited.add(task_id)

    for task_id in by_task:
        visit(task_id)

    for task in tasks:
        if task["status"] not in {
            "running",
            "completed",
        }:
            continue

        require(
            "started_at" in task,
            "MISSING_EXECUTION_START",
            task["task_id"],
        )

        start = instant(
            task["started_at"]
        )

        for dependency in task["depends_on"]:
            predecessor = by_task[dependency]

            require(
                predecessor["status"]
                == "completed",
                "DEPENDENCY_NOT_COMPLETED",
                dependency,
            )

            require(
                "completed_at" in predecessor,
                "DEPENDENCY_COMPLETION_TIME_MISSING",
                dependency,
            )

            require(
                instant(predecessor["completed_at"])
                <= start,
                "DEPENDENCY_ORDER_VIOLATION",
                task["task_id"],
            )


def check_task_authority_v04(
    bundle: dict[str, Any],
    by_agent: dict[str, dict[str, Any]],
) -> None:
    authority = bundle["authority"]
    evaluated = instant(
        bundle["evaluated_at"]
    )

    require(
        authority["authorized_target_id"]
        == bundle["target_id"],
        "AUTHORITY_TARGET_MISMATCH",
    )

    require(
        authority["authorization_status"]
        == "granted",
        "COORDINATION_AUTHORIZATION_NOT_GRANTED",
    )

    issued = instant(
        authority["issued_at"]
    )

    require(
        evaluated >= issued,
        "COORDINATION_NOT_YET_AUTHORIZED",
    )

    if authority.get("expires_at"):
        require(
            evaluated
            < instant(authority["expires_at"]),
            "COORDINATION_AUTHORIZATION_EXPIRED",
        )

    if authority.get("revoked_at"):
        require(
            evaluated
            < instant(authority["revoked_at"]),
            "COORDINATION_AUTHORIZATION_REVOKED",
        )

    controller_scopes = set(
        authority["authorized_scopes"]
    )

    for task in bundle["tasks"]:
        task_id = task["task_id"]
        agent_id = task["assigned_agent_id"]

        require(
            agent_id in by_agent,
            "UNASSIGNED_TASK",
            task_id,
        )

        agent = by_agent[agent_id]

        require(
            task["target_id"]
            == bundle["target_id"],
            "TASK_TARGET_MISMATCH",
            task_id,
        )

        require(
            task["resource_scope"]
            in controller_scopes
            and task["resource_scope"]
            in agent["authorized_scopes"],
            "UNAUTHORIZED_TASK_SCOPE",
            task_id,
        )

        require(
            task["authorization_id"]
            == agent.get("authorization_id"),
            "TASK_AUTHORIZATION_MISMATCH",
            task_id,
        )

        require(
            task["operation"]
            in agent["authorized_operations"],
            "UNAUTHORIZED_TASK_OPERATION",
            task_id,
        )

        if task["status"] not in {
            "running",
            "completed",
        }:
            continue

        require(
            "started_at" in task,
            "MISSING_EXECUTION_START",
            task_id,
        )

        start, end = task_interval_v04(
            task,
            bundle["evaluated_at"],
        )

        require(
            start >= issued,
            "TASK_BEFORE_COORDINATION_AUTHORIZATION",
            task_id,
        )

        if authority.get("expires_at"):
            require(
                end <= instant(
                    authority["expires_at"]
                ),
                "TASK_OUTSIDE_COORDINATION_AUTHORIZATION",
                task_id,
            )

        expiry = agent.get(
            "authorization_expires_at"
        )

        if expiry:
            require(
                end <= instant(expiry),
                "TASK_AUTHORIZATION_EXPIRED",
                task_id,
            )

        revoked = agent.get(
            "authorization_revoked_at"
        )

        if revoked:
            revocation_time = instant(
                revoked
            )

            require(
                end <= revocation_time,
                "REVOKED_TASK_DISPATCHED",
                task_id,
            )

        require(
            agent["assignment_status"]
            not in {"held", "revoked"}
            or (
                agent["assignment_status"]
                == "revoked"
                and revoked is not None
                and end <= instant(revoked)
            ),
            "INVALID_ACTIVE_ASSIGNMENT",
            task_id,
        )


def check_concurrency_v04(
    bundle: dict[str, Any],
) -> None:
    events: list[
        tuple[datetime, int]
    ] = []

    for task in bundle["tasks"]:
        if task["status"] not in {
            "running",
            "completed",
        }:
            continue

        start, end = task_interval_v04(
            task,
            bundle["evaluated_at"],
        )

        events.append((start, 1))
        events.append((end, -1))

    # At identical times, finish before start.
    events.sort(
        key=lambda item: (
            item[0],
            item[1],
        )
    )

    running = 0
    maximum = 0

    for _, change in events:
        running += change
        maximum = max(maximum, running)

    authorized_max = bundle[
        "authority"
    ]["max_concurrency"]

    require(
        maximum <= authorized_max,
        "CONCURRENCY_BUDGET_EXCEEDED",
        f"observed={maximum}, "
        f"authorized={authorized_max}",
    )


def check_conflicts_v04(
    bundle: dict[str, Any],
    by_task: dict[str, dict[str, Any]],
) -> None:
    conflicts = bundle["conflicts"]

    check_unique_v04(
        [
            conflict["conflict_id"]
            for conflict in conflicts
        ],
        "DUPLICATE_CONFLICT_ID",
    )

    by_pair: dict[
        frozenset[str],
        dict[str, Any],
    ] = {}

    for conflict in conflicts:
        first, second = conflict["task_ids"]

        require(
            first in by_task
            and second in by_task,
            "UNKNOWN_CONFLICT_TASK",
            conflict["conflict_id"],
        )

        pair = frozenset(
            (first, second)
        )

        require(
            pair not in by_pair,
            "DUPLICATE_CONFLICT_PAIR",
            conflict["conflict_id"],
        )

        by_pair[pair] = conflict

        require(
            by_task[first]["resource_scope"]
            == conflict["resource_scope"]
            == by_task[second]["resource_scope"],
            "CONFLICT_SCOPE_MISMATCH",
            conflict["conflict_id"],
        )

        disposition = conflict[
            "disposition"
        ]

        if disposition == "blocked":
            require(
                all(
                    by_task[task_id]["status"]
                    not in {
                        "running",
                        "completed",
                    }
                    for task_id
                    in conflict["task_ids"]
                ),
                "BLOCKED_CONFLICT_EXECUTED",
                conflict["conflict_id"],
            )

        elif disposition == "serialized":
            order = conflict["resolution"][
                "execution_order"
            ]

            require(
                set(order)
                == set(conflict["task_ids"]),
                "INVALID_SERIALIZATION_ORDER",
                conflict["conflict_id"],
            )

            preceding = by_task[
                order[0]
            ]

            following = by_task[
                order[1]
            ]

            require(
                preceding["status"]
                == "completed"
                and following["status"]
                == "completed",
                "SERIALIZATION_INCOMPLETE",
                conflict["conflict_id"],
            )

            require(
                instant(preceding["completed_at"])
                <= instant(
                    following["started_at"]
                ),
                "SERIALIZATION_ORDER_VIOLATION",
                conflict["conflict_id"],
            )

            require(
                order[0]
                in following["depends_on"],
                "SERIALIZATION_DEPENDENCY_MISSING",
                conflict["conflict_id"],
            )

        elif disposition == "externally_resolved":
            resolution = conflict["resolution"]

            require(
                resolution["resolver_id"]
                == bundle["authority"][
                    "controller_id"
                ],
                "CONFLICT_RESOLVER_NOT_EXTERNAL",
                conflict["conflict_id"],
            )

    executed_tasks = [
        task
        for task in bundle["tasks"]
        if task["status"] in {
            "running",
            "completed",
        }
    ]

    for index, left in enumerate(
        executed_tasks
    ):
        for right in executed_tasks[index + 1:]:
            if (
                left["resource_scope"]
                != right["resource_scope"]
            ):
                continue

            if not (
                left["access_mode"]
                in {"write", "exclusive"}
                or right["access_mode"]
                in {"write", "exclusive"}
            ):
                continue

            if not intervals_overlap_v04(
                left,
                right,
                bundle["evaluated_at"],
            ):
                continue

            pair = frozenset((
                left["task_id"],
                right["task_id"],
            ))

            conflict = by_pair.get(pair)

            # An externally resolved conflict must
            # have a separate trusted authority.
            require(
                conflict is not None
                and conflict["disposition"]
                == "externally_resolved"
                and left["access_mode"]
                != "exclusive"
                and right["access_mode"]
                != "exclusive",
                "CONCURRENT_WRITE_CONFLICT",
                f"{left['task_id']} / "
                f"{right['task_id']}",
            )


def check_verification_v04(
    bundle: dict[str, Any],
    by_task: dict[str, dict[str, Any]],
) -> None:
    repairs = {
        task["task_id"]: task
        for task in bundle["tasks"]
        if task["operation"] == "repair"
    }

    verifications = [
        task
        for task in bundle["tasks"]
        if (
            task["operation"] == "verify"
            and task["status"] == "completed"
        )
    ]

    verified = set(
        bundle["reconciliation"][
            "verified_task_ids"
        ]
    )

    for repair_id in verified:
        require(
            repair_id in repairs,
            "INVALID_VERIFIED_TASK_REFERENCE",
            repair_id,
        )

        repair = repairs[repair_id]

        matching = [
            task
            for task in verifications
            if repair_id in task["depends_on"]
        ]

        require(
            bool(matching),
            "INDEPENDENT_VERIFICATION_MISSING",
            repair_id,
        )

        for verification in matching:
            require(
                verification["assigned_agent_id"]
                != repair["assigned_agent_id"],
                "SELF_VERIFICATION_ACCEPTED",
                repair_id,
            )

    if (
        bundle["reconciliation"]["decision"]
        == "accepted"
    ):
        for repair_id, repair in repairs.items():
            if repair["status"] == "completed":
                require(
                    repair_id in verified,
                    "REPAIR_NOT_INDEPENDENTLY_VERIFIED",
                    repair_id,
                )


def check_reconciliation_v04(
    bundle: dict[str, Any],
    by_task: dict[str, dict[str, Any]],
) -> None:
    reconciliation = bundle[
        "reconciliation"
    ]

    require(
        reconciliation["coordination_id"]
        == bundle["coordination_id"],
        "RECONCILIATION_COORDINATION_MISMATCH",
    )

    require(
        instant(reconciliation["evaluated_at"])
        == instant(bundle["evaluated_at"]),
        "RECONCILIATION_TIME_MISMATCH",
    )

    task_ids = set(by_task)

    require(
        set(
            reconciliation["considered_task_ids"]
        ) == task_ids,
        "RECONCILIATION_TASK_SET_MISMATCH",
    )

    conflict_ids = {
        conflict["conflict_id"]
        for conflict in bundle["conflicts"]
    }

    require(
        set(reconciliation["conflict_ids"])
        == conflict_ids,
        "RECONCILIATION_CONFLICT_SET_MISMATCH",
    )

    evidence_ids = {
        evidence
        for task in bundle["tasks"]
        for evidence in task["evidence_ids"]
    }

    require(
        set(reconciliation["evidence_ids"])
        .issubset(evidence_ids),
        "RECONCILIATION_EVIDENCE_MISMATCH",
    )

    unresolved = {
        task["task_id"]
        for task in bundle["tasks"]
        if task["status"] != "completed"
    }

    blocked = {
        conflict["conflict_id"]
        for conflict in bundle["conflicts"]
        if conflict["disposition"] == "blocked"
    }

    decision = reconciliation[
        "decision"
    ]

    if decision == "accepted":
        require(
            not unresolved
            and not blocked,
            "UNRESOLVED_CONFLICT_ACCEPTED",
            ",".join(
                sorted(unresolved | blocked)
            ),
        )

        require(
            not reconciliation[
                "unresolved_task_ids"
            ],
            "RECONCILIATION_UNRESOLVED_TASK_MISMATCH",
        )

    else:
        require(
            set(
                reconciliation["unresolved_task_ids"]
            ) == unresolved,
            "RECONCILIATION_UNRESOLVED_TASK_MISMATCH",
        )

    if decision == "held":
        require(
            bool(unresolved),
            "HELD_WITHOUT_UNRESOLVED_TASK",
        )

        require(
            all(
                task["status"]
                not in {"running", "failed"}
                for task in bundle["tasks"]
            ),
            "UNSAFE_HELD_RECONCILIATION",
        )


def semantic_v04(
    bundle: dict[str, Any],
) -> None:
    agents = bundle["agents"]
    tasks = bundle["tasks"]

    check_unique_v04(
        [
            agent["agent_id"]
            for agent in agents
        ],
        "DUPLICATE_AGENT_ID",
    )

    check_unique_v04(
        [
            task["task_id"]
            for task in tasks
        ],
        "DUPLICATE_TASK_ID",
    )

    by_agent = {
        agent["agent_id"]: agent
        for agent in agents
    }

    by_task = {
        task["task_id"]: task
        for task in tasks
    }

    # Deterministic error priority is necessary
    # for matching the eight negative fixtures.

    check_dependencies_v04(
        tasks,
        by_task,
    )

    check_task_authority_v04(
        bundle,
        by_agent,
    )

    check_concurrency_v04(
        bundle
    )

    check_conflicts_v04(
        bundle,
        by_task,
    )

    check_verification_v04(
        bundle,
        by_task,
    )

    check_reconciliation_v04(
        bundle,
        by_task,
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
        check_schema(
            record,
            schemas[version],
        )

        if version == "v0.1":
            semantic_v01(record)

        elif version == "v0.2":
            semantic_v02(record)

        elif version == "v0.3":
            semantic_v03(
                record,
                schemas,
            )

        elif version == "v0.4":
            semantic_v04(record)

        else:
            raise ValueError(
                f"Unknown version: {version}"
            )

    except SemanticError as exc:
        return "FAIL", str(exc)

    return "PASS", "VALID"


def expected_error_manifest(
    version: str,
) -> dict[str, str] | None:
    if version == "v0.3":
        return EXPECTED_V03_ERRORS

    if version == "v0.4":
        return EXPECTED_V04_ERRORS

    return None


def check_fail_fixture_manifest(
    version: str,
) -> None:
    manifest = expected_error_manifest(
        version
    )

    if manifest is None:
        return

    directory = (
        ROOT / "examples" / version / "fail"
    )

    actual = {
        path.name
        for path in directory.glob("*.json")
    }

    require(
        set(manifest) == actual,
        "FAIL_FIXTURE_MANIFEST_MISMATCH",
        version,
    )


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
            ROOT
            / "examples"
            / version
            / category
        )

        if not directory.is_dir():
            raise ValueError(
                f"Missing fixture directory: "
                f"{directory}"
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
                fixture = read_object(
                    path
                )

                declared = fixture.pop(
                    "expected_result",
                    None,
                )

                require(
                    declared == expected,
                    "INVALID_EXPECTED_RESULT",
                    path.name,
                )

                actual, reason = (
                    validate_fixture(
                        fixture,
                        version,
                        schemas,
                    )
                )

                ok = actual == expected

                manifest = expected_error_manifest(
                    version
                )

                if (
                    ok
                    and category == "fail"
                    and manifest is not None
                ):
                    expected_error = (
                        manifest.get(path.name)
                    )

                    require(
                        expected_error is not None,
                        "UNKNOWN_FAIL_FIXTURE",
                        path.name,
                    )

                    actual_error = reason.split(
                        ":",
                        1,
                    )[0]

                    ok = (
                        actual_error
                        == expected_error
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
                "MATCH"
                if ok
                else "MISMATCH"
            )

            print(
                f"[{label}] "
                f"{path.relative_to(ROOT)} "
                f"expected={expected} "
                f"actual={actual}"
            )

            if actual != "PASS":
                print(
                    f"  reason: {reason}"
                )

    print(f"[completed] {version}")

    return total, matched


# ============================================================
# Main entry point
# ============================================================

def main() -> int:
    print(
        "=== MARP v0.1-v0.4 Validation ==="
    )

    schemas: dict[
        str,
        Draft202012Validator,
    ] = {}

    for version, (
        schema_rel,
        _,
        _,
    ) in VERSIONS.items():
        path = ROOT / schema_rel

        schemas[version] = make_validator(
            path
        )

        print(
            f"[schema-ok] {schema_rel}"
        )

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

    check_fail_fixture_manifest("v0.3")
    check_fail_fixture_manifest("v0.4")

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

    if total != 50 or matched != total:
        print(
            "[FAIL] MARP conformance mismatch"
        )
        return 1

    print(
        "[PASS] All MARP v0.1-v0.4 "
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
