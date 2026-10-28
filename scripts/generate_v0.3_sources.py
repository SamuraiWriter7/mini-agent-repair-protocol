#!/usr/bin/env python3
"""
MARP v0.3 source fixture generator.

Generates local source records referenced by the
v0.3 repair-lineage example bundles.

Usage:
    python scripts/generate_v0.3_sources.py
    python scripts/generate_v0.3_sources.py --check
    python scripts/generate_v0.3_sources.py --force

Requirements:
    jsonschema>=4.18,<5

Safety:
    - Only writes under examples/v0.3/sources/
    - Does not modify the source lineage bundles
    - Does not overwrite existing files by default
    - Preserves intentional FAIL-case defects
    - Generated records are synthetic test fixtures
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]

EXAMPLES = ROOT / "examples" / "v0.3"
SOURCES = EXAMPLES / "sources"

SCHEMA_V02 = (
    ROOT / "schemas"
    / "repair-lifecycle-v0.2.schema.json"
)

SCHEMA_HOLD = (
    ROOT / "schemas"
    / "hold-resolution-v0.3.schema.json"
)

SCHEMA_LINEAGE = (
    ROOT / "schemas"
    / "repair-lineage-v0.3.schema.json"
)

SCOPE = "component-runtime-configuration"
CONTROLLER = "external-authority-controller-001"
REVIEWER = "external-safety-reviewer-001"

ACTION_MAP = {
    "containment_applied": "contain",
    "repair_started": "repair",
    "repair_completed": "repair",
    "verification_passed": "verify",
    "verification_failed": "verify",
    "release_approved": "release",
    "containment_released": "release",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")

    return data


def canonical(data: dict[str, Any]) -> str:
    return json.dumps(
        data,
        indent=2,
        ensure_ascii=False,
        sort_keys=False,
    ) + "\n"


def validate_schema(
    data: dict[str, Any],
    schema: dict[str, Any],
    label: str,
) -> None:
    validator = Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    )
    errors = sorted(
        validator.iter_errors(data),
        key=lambda error: str(error.json_path),
    )

    if errors:
        first = errors[0]
        raise ValueError(
            f"{label}: {first.json_path}: {first.message}"
        )


def safe_source_path(reference: str) -> Path:
    if not isinstance(reference, str):
        raise ValueError("Invalid record_reference")

    path = (ROOT / reference).resolve()
    base = SOURCES.resolve()

    if not path.is_relative_to(base):
        raise ValueError(
            f"Unsafe source reference: {reference}"
        )

    if path.suffix != ".json":
        raise ValueError(
            f"Source must be JSON: {reference}"
        )

    return path


def bindings_for(
    bundle: dict[str, Any],
    event_id: str,
) -> list[dict[str, Any]]:
    return [
        item
        for item in bundle.get("evidence_bindings", [])
        if item["event_id"] == event_id
    ]


def find_authorization(
    bundle: dict[str, Any],
    authorization_id: str | None,
) -> dict[str, Any] | None:
    if not authorization_id:
        return None

    for item in bundle.get("authorization_bindings", []):
        if item["authorization_id"] == authorization_id:
            return item

    return None


def authorization_authority(
    bundle: dict[str, Any],
    record: dict[str, Any],
) -> dict[str, Any]:
    event = record["event_type"]
    auth_id = record.get("authorization_id")
    binding = find_authorization(bundle, auth_id)

    authority: dict[str, Any] = {
        "controller_id": (
            binding["controller_id"]
            if binding else CONTROLLER
        ),
        "authorization_status": "not_required",
    }

    if not auth_id:
        return authority

    authority["authorization_id"] = auth_id

    if event == "authorization_revoked":
        authority["authorization_status"] = "revoked"
    elif event == "authorization_expired":
        authority["authorization_status"] = "expired"
    elif event == "operation_held":
        authority["authorization_status"] = "pending"
    else:
        authority["authorization_status"] = "granted"

    if binding:
        operations = list(binding["authorized_operations"])

        # A v0.2 source record describes the grant.
        # It does not redefine the lineage binding.
        authority["authorized_operations"] = [
            item for item in operations
            if item != "resolve_hold"
        ]
        authority["authorized_scopes"] = list(
            binding["authorized_scopes"]
        )
        authority["issued_at"] = binding["issued_at"]

        if "expires_at" in binding:
            authority["expires_at"] = binding["expires_at"]

        if "revoked_at" in binding:
            authority["revoked_at"] = binding["revoked_at"]
    else:
        action = ACTION_MAP.get(event, "repair")
        authority["authorized_operations"] = [action]
        authority["authorized_scopes"] = [SCOPE]
        authority["issued_at"] = record["timestamp"]

    if event == "authorization_granted":
        authority["authorization_status"] = "granted"

    return authority


def verification_record(
    bundle: dict[str, Any],
    record: dict[str, Any],
) -> dict[str, Any]:
    event = record["event_type"]
    evidence = bindings_for(
        bundle,
        record["event_id"],
    )

    verification_ids = [
        item["evidence_id"]
        for item in evidence
        if item["evidence_type"] == "verification"
    ]

    if event == "verification_passed":
        return {
            "verifier_id": record["actor_id"],
            "verification_status": "passed",
            "verification_evidence_ids": verification_ids,
        }

    if event == "verification_failed":
        return {
            "verifier_id": record["actor_id"],
            "verification_status": "failed",
            "verification_evidence_ids": verification_ids,
        }

    if event == "containment_released":
        verifier = next(
            (
                item["actor_id"]
                for item in bundle["records"]
                if item["event_type"] == "verification_passed"
            ),
            "independent-verifier-unknown",
        )

        all_verification_ids = [
            item["evidence_id"]
            for item in bundle["evidence_bindings"]
            if item["evidence_type"] == "verification"
        ]

        return {
            "verifier_id": verifier,
            "verification_status": "passed",
            "verification_evidence_ids": all_verification_ids,
        }

    return {
        "verification_status": "pending",
        "verification_evidence_ids": [],
    }


def containment_record(
    bundle: dict[str, Any],
    record: dict[str, Any],
) -> dict[str, Any] | None:
    event = record["event_type"]

    containment_events = {
        "containment_applied",
        "repair_started",
        "repair_completed",
        "verification_passed",
        "verification_failed",
        "operation_held",
        "authorization_revoked",
        "authorization_expired",
        "release_approved",
        "containment_released",
    }

    if event not in containment_events:
        return None

    applied = next(
        (
            item["timestamp"]
            for item in bundle["records"]
            if item["event_type"] == "containment_applied"
        ),
        record["timestamp"],
    )

    if event == "containment_released":
        status = "released"
    elif event == "release_approved":
        status = "release_pending"
    else:
        status = "active"

    result: dict[str, Any] = {
        "containment_id": bundle["containment_id"],
        "scope": SCOPE,
        "status": status,
        "applied_at": applied,
    }

    if status == "released":
        result["released_at"] = record["timestamp"]

    return result


def hold_record(
    record: dict[str, Any],
) -> dict[str, Any] | None:
    event = record["event_type"]

    if event not in {
        "operation_held",
        "authorization_revoked",
        "authorization_expired",
    }:
        return None

    return {
        "hold_id": record["hold_id"],
        "status": "active",
        "reason": (
            "Synthetic safety hold for MARP v0.3 testing"
        ),
        "review_authority_id": REVIEWER,
    }


def generate_v02(
    bundle: dict[str, Any],
    record: dict[str, Any],
) -> dict[str, Any]:
    event = record["event_type"]
    evidence = bindings_for(bundle, record["event_id"])

    source: dict[str, Any] = {
        "schema_version": "0.2.0",
        "lifecycle_id": (
            bundle["lineage_id"]
            + "-"
            + record["event_id"]
        ),
        "operation_id": record["operation_id"],
        "target_id": record["target_id"],
        "actor_id": record["actor_id"],
        "event_type": event,
        "previous_state": record["previous_state"],
        "next_state": record["next_state"],
        "authority": authorization_authority(
            bundle, record
        ),
        "verification": verification_record(
            bundle, record
        ),
        "evidence": [
            item["evidence_id"]
            for item in evidence
        ],
        "timestamp": record["timestamp"],
    }

    containment = containment_record(bundle, record)
    if containment is not None:
        source["containment"] = containment

    hold = hold_record(record)
    if hold is not None:
        source["hold"] = hold

    return source


def generate_hold_resolution(
    bundle: dict[str, Any],
    record: dict[str, Any],
) -> dict[str, Any]:
    auth_id = record["authorization_id"]
    binding = find_authorization(bundle, auth_id)

    if binding is None:
        raise ValueError(
            f"Missing hold resolution authorization: {auth_id}"
        )

    evidence = bindings_for(
        bundle,
        record["event_id"],
    )
    evidence_ids = [
        item["evidence_id"] for item in evidence
    ]
    resolution_ids = [
        item["evidence_id"]
        for item in evidence
        if item["evidence_type"] == "hold_resolution"
    ]

    authority = {
        "controller_id": binding["controller_id"],
        "authorization_id": auth_id,
        "authorization_status": "granted",
        "authorized_actor_id": record["actor_id"],
        "authorized_operations": ["resolve_hold"],
        "authorized_scopes": binding["authorized_scopes"],
        "issued_at": binding["issued_at"],
    }

    if "expires_at" in binding:
        authority["expires_at"] = binding["expires_at"]

    return {
        "schema_version": "0.3.0",
        "lifecycle_id": (
            bundle["lineage_id"]
            + "-"
            + record["event_id"]
        ),
        "operation_id": record["operation_id"],
        "target_id": record["target_id"],
        "containment_id": bundle["containment_id"],
        "actor_id": record["actor_id"],
        "event_type": "hold_resolved",
        "previous_state": record["previous_state"],
        "next_state": record["next_state"],
        "hold_id": record["hold_id"],
        "authorization_id": auth_id,
        "authority": authority,
        "hold_resolution": {
            "hold_id": record["hold_id"],
            "previous_status": "active",
            "next_status": "resolved",
            "decision": "resolve",
            "review_authority_id": record["actor_id"],
            "reason": (
                "External safety review completed; "
                "containment remains active."
            ),
            "resolution_evidence_ids": resolution_ids,
            "resolved_at": record["timestamp"],
            "containment_status": "active",
            "repair_resume_authorized": False,
            "containment_release_authorized": False,
        },
        "evidence": evidence_ids,
        "timestamp": record["timestamp"],
    }


def process_bundle(
    bundle_path: Path,
    schemas: dict[str, dict[str, Any]],
    check: bool,
    force: bool,
) -> tuple[int, int, int]:
    bundle = load_json(bundle_path)

    # Test metadata is not part of the production schema.
    instance = {
        key: value
        for key, value in bundle.items()
        if key != "expected_result"
    }

    validate_schema(
        instance,
        schemas["lineage"],
        str(bundle_path),
    )

    created = 0
    unchanged = 0
    differences = 0

    for record in bundle["records"]:
        path = safe_source_path(
            record["record_reference"]
        )

        version = record["source_version"]

        if version == "0.2.0":
            source = generate_v02(bundle, record)
            schema = schemas["v02"]
        elif (
            version == "0.3.0"
            and record["event_type"] == "hold_resolved"
        ):
            source = generate_hold_resolution(
                bundle, record
            )
            schema = schemas["hold"]
        else:
            raise ValueError(
                f"Unsupported event version: {version}"
            )

        validate_schema(
            source,
            schema,
            str(path),
        )

        desired = canonical(source)

        if path.exists():
            current = path.read_text(encoding="utf-8")

            if current == desired:
                print(f"[MATCH] {path.relative_to(ROOT)}")
                unchanged += 1
                continue

            if check or not force:
                print(f"[DIFF] {path.relative_to(ROOT)}")
                differences += 1
                continue

        elif check:
            print(f"[MISSING] {path.relative_to(ROOT)}")
            differences += 1
            continue

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        path.write_text(
            desired,
            encoding="utf-8",
        )
        print(f"[WRITE] {path.relative_to(ROOT)}")
        created += 1

    return created, unchanged, differences


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate MARP v0.3 source fixtures"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check source fixtures without writing",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite differing generated sources",
    )

    args = parser.parse_args()

    if args.check and args.force:
        parser.error(
            "--check and --force cannot be combined"
        )

    schemas = {
        "v02": load_json(SCHEMA_V02),
        "hold": load_json(SCHEMA_HOLD),
        "lineage": load_json(SCHEMA_LINEAGE),
    }

    for name, schema in schemas.items():
        Draft202012Validator.check_schema(schema)
        print(f"[schema-ok] {name}")

    total_created = 0
    total_unchanged = 0
    total_differences = 0

    bundles: list[Path] = []

    for category in ("pass", "fail"):
        directory = EXAMPLES / category

        if not directory.is_dir():
            raise ValueError(
                f"Missing directory: {directory}"
            )

        bundles.extend(
            sorted(directory.glob("*.json"))
        )

    if len(bundles) != 14:
        raise ValueError(
            "Expected exactly 14 v0.3 bundles; "
            f"found {len(bundles)}"
        )

    references: set[Path] = set()

    for bundle_path in bundles:
        bundle = load_json(bundle_path)

        for record in bundle.get("records", []):
            reference = safe_source_path(
                record["record_reference"]
            )

            if reference in references:
                raise ValueError(
                    f"Duplicate source reference: {reference}"
                )

            references.add(reference)

    for bundle_path in bundles:
        print(
            f"\n[bundle] {bundle_path.relative_to(ROOT)}"
        )

        created, unchanged, differences = process_bundle(
            bundle_path,
            schemas,
            args.check,
            args.force,
        )

        total_created += created
        total_unchanged += unchanged
        total_differences += differences

    print("\n=== MARP v0.3 Source Summary ===")
    print(f"Bundles: {len(bundles)}")
    print(f"References: {len(references)}")
    print(f"Written: {total_created}")
    print(f"Matched: {total_unchanged}")
    print(f"Missing or different: {total_differences}")

    if total_differences:
        print("[FAIL] Source fixtures need attention")
        return 1

    print("[PASS] Source fixture generation/check complete")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
    ) as exc:
        print(f"[FATAL] {exc}", file=sys.stderr)
        sys.exit(1)
