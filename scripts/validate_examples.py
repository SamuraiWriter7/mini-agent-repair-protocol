#!/usr/bin/env python3
"""MARP v0.1/v0.2 conformance fixture validator.

Checks JSON Schema, record-level semantic invariants, and expected outcomes.
Fixtures are standalone: no historical event chain or external authority registry
is available, so real-world authorization, provenance, and release prerequisites
cannot be proven by this validator.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent.parent
VERSIONS = {
    "v0.1": ("schemas/repair-record.schema.json", 4, 6),
    "v0.2": ("schemas/repair-lifecycle-v0.2.schema.json", 6, 6),
}
ACTIVE = {"authorized", "executed", "verified"}
ROLES = {"diagnose": "diagnostic", "contain": "containment", "repair": "repair", "verify": "verification", "replace": "replacement"}
TRANSITIONS = {
    "authorization_granted": {("observed", "authorized")},
    "operation_held": {(s, "held") for s in ("observed", "authorized", "contained", "repairing", "verification_pending")},
    "containment_applied": {("authorized", "contained")},
    "repair_started": {("contained", "repairing")},
    "repair_completed": {("repairing", "verification_pending")},
    "verification_passed": {("verification_pending", "verified")},
    "verification_failed": {("verification_pending", "failed")},
    "release_approved": {("verified", "verified")},
    "containment_released": {("verified", "released")},
    "authorization_revoked": {(s, "held") for s in ("authorized", "contained", "repairing", "verification_pending")},
    "authorization_expired": {(s, "held") for s in ("authorized", "contained", "repairing", "verification_pending")},
}
PERMISSIONS = {
    "containment_applied": "contain",
    "repair_started": "repair",
    "repair_completed": "repair",
    "verification_passed": "verify",
    "verification_failed": "verify",
    "release_approved": "release",
    "containment_released": "release",
}
# Certain events are records of decisions, not a new state-changing action.
AUTHORIZED_EVENTS = set(PERMISSIONS)
EXECUTION_EVENTS = {"containment_applied", "repair_started", "repair_completed", "containment_released"}


class SemanticError(ValueError):
    pass


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise SemanticError(f"{code}: {detail}" if detail else code)


def read_object(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return data


def instant(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.utcoffset() is not None, "TIMEZONE_REQUIRED")
    return parsed


def temporal_bounds(authority: dict[str, Any], event_time: datetime) -> None:
    issued = authority.get("issued_at")
    expiry = authority.get("expires_at")
    if issued:
        issue_time = instant(issued)
        require(event_time >= issue_time, "AUTHORIZATION_NOT_YET_VALID")
    else:
        issue_time = None
    if expiry:
        expiry_time = instant(expiry)
        if issue_time:
            require(expiry_time > issue_time, "INVALID_AUTHORIZATION_TIME_RANGE")
        require(event_time < expiry_time, "EXPIRED_AUTHORIZATION_EXECUTION")
    revoked = authority.get("revoked_at")
    if revoked:
        revoke_time = instant(revoked)
        if issue_time:
            require(revoke_time >= issue_time, "REVOCATION_BEFORE_ISSUANCE")
        require(event_time < revoke_time, "REVOKED_AUTHORIZATION_EXECUTION")


def semantic_v01(record: dict[str, Any]) -> None:
    op, agent, target = record["operation"], record["mini_agent"], record["target"]
    authority, verification = record["authority"], record["verification"]
    kind, status = op["operation_type"], op["status"]
    require(agent["role"] == ROLES[kind], "ROLE_MISMATCH")
    require(op["state_changing"] is (kind != "diagnose"), "INVALID_STATE_CHANGE_FLAG")
    require(op["scope"] in target["authorized_scope"], "OUT_OF_SCOPE_INTERVENTION")
    if op["state_changing"] and status in ACTIVE:
        require(authority["authorization_status"] == "granted", "AUTHORIZATION_NOT_GRANTED")
        require(bool(authority.get("authorization_id")), "MISSING_AUTHORIZATION_ID")
        require(kind in authority.get("authorized_operations", []), "UNAUTHORIZED_OPERATION_TYPE")
        require(agent["mini_agent_id"] != authority["controller_id"], "SELF_AUTHORIZATION")
    if kind == "replace" and status in ACTIVE:
        require(target.get("replaceable") is True, "TARGET_NOT_REPLACEABLE")
    ids = verification.get("verification_evidence_ids", [])
    require(set(ids).issubset(set(record["evidence"])), "INVALID_VERIFICATION_EVIDENCE_REFERENCE")
    if status == "verified":
        require(verification["verification_status"] == "passed", "VERIFICATION_NOT_PASSED")
        require(bool(verification.get("verifier_id")), "MISSING_VERIFIER")
        require(verification["verifier_id"] != agent["mini_agent_id"], "SELF_VERIFICATION")
        require(bool(ids), "MISSING_VERIFICATION_EVIDENCE")
    else:
        require(verification["verification_status"] != "passed", "UNCONFIRMED_VERIFICATION_STATUS")


def semantic_v02(record: dict[str, Any]) -> None:
    event = record["event_type"]
    transition = (record["previous_state"], record["next_state"])
    require(transition in TRANSITIONS[event], "INVALID_LIFECYCLE_TRANSITION")
    authority, verification = record["authority"], record["verification"]
    containment, hold = record.get("containment"), record.get("hold")
    now = instant(record["timestamp"])
    ids = verification.get("verification_evidence_ids", [])
    require(set(ids).issubset(set(record["evidence"])), "INVALID_VERIFICATION_EVIDENCE_REFERENCE")
    if event in AUTHORIZED_EVENTS:
        require(authority["authorization_status"] == "granted", "AUTHORIZATION_NOT_GRANTED")
        require(bool(authority.get("authorization_id")), "MISSING_AUTHORIZATION_ID")
        require(PERMISSIONS[event] in authority.get("authorized_operations", []), "UNAUTHORIZED_OPERATION_TYPE")
        # These fixtures require time-bounded grants for state-changing actions.
        if event in EXECUTION_EVENTS:
            require(bool(authority.get("issued_at")) and bool(authority.get("expires_at")), "AUTHORIZATION_TIME_BOUNDARY_MISSING")
        temporal_bounds(authority, now)
        require(record["actor_id"] != authority["controller_id"], "SELF_AUTHORIZATION")
        if containment:
            require(containment["scope"] in authority.get("authorized_scopes", []), "OUT_OF_SCOPE_INTERVENTION")
    if containment:
        if "applied_at" in containment:
            require(instant(containment["applied_at"]) <= now, "CONTAINMENT_APPLIED_IN_FUTURE")
        if "released_at" in containment:
            require(instant(containment["released_at"]) <= now, "RELEASE_TIMESTAMP_IN_FUTURE")
            if "applied_at" in containment:
                require(instant(containment["applied_at"]) <= instant(containment["released_at"]), "RELEASE_BEFORE_CONTAINMENT")
    if event in ("containment_applied", "repair_started"):
        require(containment is not None and containment["status"] == "active", "CONTAINMENT_NOT_ACTIVE")
    if event == "operation_held":
        require(hold is not None and hold["status"] == "active", "HOLD_NOT_ACTIVE")
    if event in ("authorization_revoked", "authorization_expired"):
        expected = "revoked" if event == "authorization_revoked" else "expired"
        require(authority["authorization_status"] == expected, "AUTHORIZATION_STATUS_EVENT_MISMATCH")
        require(hold is not None and hold["status"] == "active", "HOLD_NOT_ACTIVE")
        if event == "authorization_revoked":
            require(record["actor_id"] == authority["controller_id"], "REVOCATION_ACTOR_MISMATCH")
            require(bool(authority.get("revoked_at")), "MISSING_REVOCATION_TIMESTAMP")
            require(instant(authority["revoked_at"]) == now, "REVOCATION_TIMESTAMP_MISMATCH")
            if authority.get("issued_at"):
                require(now >= instant(authority["issued_at"]), "REVOCATION_BEFORE_ISSUANCE")
        if containment:
            require(containment["status"] == "active", "CONTAINMENT_NOT_PRESERVED")
    if event == "verification_passed":
        require(verification["verification_status"] == "passed", "VERIFICATION_NOT_PASSED")
        require(record["actor_id"] == verification.get("verifier_id"), "VERIFIER_ACTOR_MISMATCH")
        require(bool(ids), "MISSING_VERIFICATION_EVIDENCE")
        if containment:
            require(containment["status"] == "active", "PREMATURE_CONTAINMENT_RELEASE")
    if event == "release_approved":
        require(containment is not None and containment["status"] == "release_pending", "RELEASE_NOT_PENDING")
    if event == "containment_released":
        require(verification["verification_status"] == "passed", "RELEASE_WITHOUT_VERIFICATION")
        require(bool(ids), "MISSING_RELEASE_VERIFICATION_EVIDENCE")
        require(containment is not None and containment["status"] == "released", "CONTAINMENT_NOT_RELEASED")
        require(bool(containment.get("released_at")), "MISSING_RELEASE_TIMESTAMP")
        require(instant(containment["released_at"]) == now, "RELEASE_TIMESTAMP_MISMATCH")
        require(hold is None or hold["status"] != "active", "RELEASE_WHILE_HELD")
    # History-level prerequisites such as prior release_approved are intentionally
    # not asserted here: standalone fixtures have no authoritative predecessor chain.


def validate(record: dict[str, Any], schema_validator: Draft202012Validator, version: str) -> tuple[str, str]:
    errors = sorted(schema_validator.iter_errors(record), key=lambda e: (list(map(str, e.absolute_path)), e.message))
    if errors:
        e = errors[0]
        where = "/".join(map(str, e.absolute_path)) or "<root>"
        return "FAIL", f"SCHEMA_ERROR at {where}: {e.message}"
    try:
        (semantic_v01 if version == "v0.1" else semantic_v02)(record)
    except (SemanticError, ValueError) as e:
        return "FAIL", f"SEMANTIC_ERROR: {e}"
    return "PASS", "VALID"


def main() -> int:
    total, matched = 0, 0
    print("=== MARP v0.1 + v0.2 Validation ===")
    for version, (schema_rel, count_pass, count_fail) in VERSIONS.items():
        print(f"\n[version] {version}")
        schema_path = ROOT / schema_rel
        try:
            schema = read_object(schema_path)
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
        except (OSError, ValueError, Exception) as exc:
            print(f"[FATAL] Unable to load schema {schema_rel}: {exc}")
            return 1
        for folder, expected_count, expected in (("pass", count_pass, "PASS"), ("fail", count_fail, "FAIL")):
            directory = ROOT / "examples" / version / folder
            if not directory.is_dir():
                print(f"[FATAL] Missing fixture directory: {directory}")
                return 1
            paths = sorted(directory.glob("*.json"))
            if len(paths) != expected_count:
                print(f"[FATAL] {version}/{folder}: expected {expected_count} files, found {len(paths)}")
                return 1
            for path in paths:
                total += 1
                try:
                    fixture = read_object(path)
                    fixture_expected = fixture.pop("expected_result", None)
                    if fixture_expected != expected:
                        raise ValueError(f"expected_result must be {expected}, got {fixture_expected!r}")
                    actual, reason = validate(fixture, validator, version)
                    ok = actual == expected
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    actual, reason, ok = "INVALID_FIXTURE", str(exc), False
                matched += int(ok)
                print(f"[{'MATCH' if ok else 'MISMATCH'}] {path.relative_to(ROOT)} expected={expected} actual={actual}")
                if actual != "PASS":
                    print(f"  reason: {reason}")
        print(f"[completed] {version}")
    print(f"\n=== MARP Summary ===\nTotal: {total}\nMatched: {matched}\nMismatched: {total - matched}")
    if total != 22 or matched != total:
        print("[FAIL] MARP conformance mismatch")
        return 1
    print("[PASS] All MARP v0.1 + v0.2 expectations matched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
