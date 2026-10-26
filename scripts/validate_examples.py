#!/usr/bin/env python3
"""
Mini-Agent Repair Protocol (MARP)
v0.1 Conformance Example Validator

Validation layers:
1. JSON Schema validation
2. Semantic validation
3. Expected-result matching

Expected test coverage:
- 4 PASS examples
- 6 FAIL examples

A correctly rejected FAIL example counts as MATCH.

Requirements:
    pip install jsonschema>=4.18,<5

Usage:
    python scripts/validate_examples.py
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parent.parent

SCHEMA_PATH = (
    ROOT / "schemas" / "repair-record.schema.json"
)

EXAMPLES_ROOT = ROOT / "examples" / "v0.1"

EXPECTED_COUNTS = {
    "PASS": 4,
    "FAIL": 6,
}

OPERATION_ROLES = {
    "diagnose": "diagnostic",
    "contain": "containment",
    "repair": "repair",
    "verify": "verification",
    "replace": "replacement",
}

ACTIVE_STATUSES = {
    "authorized",
    "executed",
    "verified",
}


class SemanticValidationError(ValueError):
    """Raised when a MARP semantic invariant is violated."""


def require(
    condition: bool,
    code: str,
    message: str,
) -> None:
    if not condition:
        raise SemanticValidationError(
            f"{code}: {message}"
        )


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError(
            f"JSON root must be an object: {path}"
        )

    return data


def load_schema() -> Draft202012Validator:
    schema = load_json(SCHEMA_PATH)

    Draft202012Validator.check_schema(schema)

    return Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    )


def validate_semantics(
    record: dict[str, Any],
) -> None:
    """
    Validate MARP v0.1 semantic invariants.

    This function assumes JSON Schema validation
    has already succeeded.

    Note:
    Record-level checks do not establish actual
    authorization or evidence authenticity.
    """

    operation = record["operation"]
    agent = record["mini_agent"]
    target = record["target"]
    authority = record["authority"]
    verification = record["verification"]

    operation_type = operation["operation_type"]
    status = operation["status"]
    state_changing = operation["state_changing"]

    agent_id = agent["mini_agent_id"]
    controller_id = authority["controller_id"]

    authorization_status = authority[
        "authorization_status"
    ]

    # --------------------------------------------------
    # 1. Operation and role consistency
    # --------------------------------------------------

    expected_role = OPERATION_ROLES[operation_type]

    require(
        agent["role"] == expected_role,
        "ROLE_MISMATCH",
        (
            f"Operation '{operation_type}' requires "
            f"role '{expected_role}'."
        ),
    )

    # --------------------------------------------------
    # 2. Read-only diagnosis
    # --------------------------------------------------

    if operation_type == "diagnose":
        require(
            state_changing is False,
            "DIAGNOSE_STATE_CHANGE",
            "Diagnosis MUST remain read-only.",
        )
    else:
        require(
            state_changing is True,
            "INVALID_STATE_CHANGE_FLAG",
            (
                f"Operation '{operation_type}' "
                "MUST be marked state-changing "
                "under the v0.1 schema."
            ),
        )

    # --------------------------------------------------
    # 3. Exact scope matching
    # --------------------------------------------------

    operation_scope = operation["scope"]
    authorized_scopes = target["authorized_scope"]

    require(
        operation_scope in authorized_scopes,
        "OUT_OF_SCOPE_INTERVENTION",
        (
            f"Scope '{operation_scope}' is not "
            "within the recorded target scope."
        ),
    )

    # --------------------------------------------------
    # 4. External authorization
    # --------------------------------------------------

    if state_changing and status in ACTIVE_STATUSES:

        require(
            authorization_status == "granted",
            "EXECUTION_WITHOUT_ACTIVE_AUTHORIZATION",
            (
                "Active state-changing operations "
                "require granted authorization."
            ),
        )

        require(
            bool(authority.get("authorization_id")),
            "MISSING_AUTHORIZATION_ID",
            "Authorization ID is required.",
        )

        authorized_operations = authority.get(
            "authorized_operations", []
        )

        require(
            operation_type in authorized_operations,
            "UNAUTHORIZED_OPERATION_TYPE",
            (
                f"Operation '{operation_type}' "
                "is not explicitly authorized."
            ),
        )

        require(
            agent_id != controller_id,
            "SELF_AUTHORIZATION",
            (
                "A mini-agent MUST NOT authorize "
                "its own state-changing operation."
            ),
        )

    # --------------------------------------------------
    # 5. Non-active states cannot claim success
    # --------------------------------------------------

    if status in {"held", "rejected", "failed"}:
        require(
            verification["verification_status"]
            != "passed",
            "INVALID_SUCCESS_CLAIM",
            (
                "Held, rejected, or failed operations "
                "MUST NOT claim successful verification."
            ),
        )

    # --------------------------------------------------
    # 6. Component replacement
    # --------------------------------------------------

    if operation_type == "replace":
        if status in ACTIVE_STATUSES:
            require(
                target.get("replaceable") is True,
                "TARGET_NOT_REPLACEABLE",
                (
                    "Active component replacement "
                    "requires replaceable=true."
                ),
            )

    # --------------------------------------------------
    # 7. Verification evidence references
    # --------------------------------------------------

    evidence_ids = set(record["evidence"])

    verification_ids = verification.get(
        "verification_evidence_ids", []
    )

    require(
        set(verification_ids).issubset(evidence_ids),
        "INVALID_VERIFICATION_EVIDENCE_REFERENCE",
        (
            "Verification evidence references MUST "
            "exist in the evidence list."
        ),
    )

    # --------------------------------------------------
    # 8. Verified-state requirements
    # --------------------------------------------------

    if status == "verified":

        require(
            verification["verification_status"]
            == "passed",
            "VERIFICATION_NOT_PASSED",
            (
                "Verified operations require "
                "verification_status=passed."
            ),
        )

        verifier_id = verification.get("verifier_id")

        require(
            bool(verifier_id),
            "MISSING_VERIFIER",
            (
                "Verified operations require "
                "an independent verifier."
            ),
        )

        require(
            agent_id != verifier_id,
            "SELF_VERIFICATION",
            (
                "A mini-agent MUST NOT verify "
                "its own operation."
            ),
        )

        require(
            bool(verification_ids),
            "MISSING_VERIFICATION_EVIDENCE",
            (
                "Verified operations require "
                "verification evidence."
            ),
        )

        require(
            bool(evidence_ids),
            "MISSING_OPERATION_EVIDENCE",
            (
                "Verified operations require "
                "supporting evidence."
            ),
        )

    # --------------------------------------------------
    # 9. Verification state consistency
    # --------------------------------------------------

    if status != "verified":
        require(
            verification["verification_status"]
            != "passed",
            "UNCONFIRMED_VERIFICATION_STATUS",
            (
                "A passed verification decision "
                "requires operation.status=verified."
            ),
        )


def validate_record(
    record: dict[str, Any],
    validator: Draft202012Validator,
) -> tuple[bool, str]:
    """
    Return:
        (True, "VALID") for accepted records.
        (False, reason) for rejected records.
    """

    errors = sorted(
        validator.iter_errors(record),
        key=lambda error: (
            "/".join(map(str, error.absolute_path)),
            error.message,
        ),
    )

    if errors:
        error = errors[0]

        location = "/".join(
            map(str, error.absolute_path)
        )

        if not location:
            location = "<root>"

        return (
            False,
            (
                f"SCHEMA_ERROR at {location}: "
                f"{error.message}"
            ),
        )

    try:
        validate_semantics(record)
    except SemanticValidationError as exc:
        return False, str(exc)

    return True, "VALID"


def collect_examples() -> list[tuple[Path, str]]:
    """
    Discover all JSON fixtures in pass/ and fail/.

    Also enforce the v0.1 baseline fixture counts.
    """

    examples: list[tuple[Path, str]] = []

    for directory_name, expectation in (
        ("pass", "PASS"),
        ("fail", "FAIL"),
    ):
        directory = EXAMPLES_ROOT / directory_name

        if not directory.is_dir():
            raise FileNotFoundError(
                f"Missing example directory: {directory}"
            )

        paths = sorted(directory.glob("*.json"))

        expected_count = EXPECTED_COUNTS[expectation]

        if len(paths) != expected_count:
            raise ValueError(
                f"{expectation} fixture count mismatch: "
                f"expected={expected_count}, "
                f"actual={len(paths)}"
            )

        for path in paths:
            examples.append((path, expectation))

    return examples


def validate_example(
    path: Path,
    directory_expectation: str,
    validator: Draft202012Validator,
) -> tuple[bool, str, str, str]:
    """
    Returns:
        matched
        expected_result
        actual_result
        reason
    """

    try:
        example = load_json(path)

        expected = example.get("expected_result")

        if expected not in ("PASS", "FAIL"):
            return (
                False,
                str(expected),
                "INVALID_FIXTURE",
                "Missing or invalid expected_result.",
            )

        if expected != directory_expectation:
            return (
                False,
                expected,
                "INVALID_FIXTURE",
                (
                    "Fixture expectation conflicts "
                    "with its pass/fail directory."
                ),
            )

        # Remove test-only metadata before schema
        # and semantic validation.
        record = copy.deepcopy(example)
        record.pop("expected_result", None)

        valid, reason = validate_record(
            record,
            validator,
        )

        actual = "PASS" if valid else "FAIL"

        return (
            actual == expected,
            expected,
            actual,
            reason,
        )

    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError,
    ) as exc:
        return (
            False,
            directory_expectation,
            "INVALID_FIXTURE",
            f"Fixture processing error: {exc}",
        )


def main() -> int:
    print("=== MARP v0.1 Validation ===")
    print()

    try:
        validator = load_schema()
        print(f"[schema-ok] {SCHEMA_PATH.relative_to(ROOT)}")

        examples = collect_examples()

    except Exception as exc:
        print(f"[fatal] {exc}", file=sys.stderr)
        return 1

    print()

    total = 0
    matched = 0
    mismatches = 0

    for path, directory_expectation in examples:
        total += 1

        (
            is_match,
            expected,
            actual,
            reason,
        ) = validate_example(
            path,
            directory_expectation,
            validator,
        )

        relative_path = path.relative_to(ROOT)

        if is_match:
            matched += 1
            label = "MATCH"
        else:
            mismatches += 1
            label = "MISMATCH"

        print(
            f"[{label}] {relative_path} "
            f"expected={expected} actual={actual}"
        )

        if actual == "FAIL":
            print(f"  reason: {reason}")

        elif not is_match:
            print(f"  reason: {reason}")

    print()
    print("=== MARP v0.1 Summary ===")
    print(f"Total examples : {total}")
    print(f"Matched        : {matched}")
    print(f"Mismatched     : {mismatches}")

    if mismatches:
        print("[FAIL] MARP conformance mismatch")
        return 1

    print("[PASS] All MARP v0.1 expectations matched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
