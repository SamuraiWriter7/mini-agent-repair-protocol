
# Changelog

All notable changes to the Mini-Agent Repair Protocol
(MARP) are documented in this file.

This project follows the principles of
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and uses [Semantic Versioning](https://semver.org/).

MARP is an experimental protocol specification.
Version numbers indicate specification evolution,
not production deployment readiness.

---

## [Unreleased]

### Planned

- Extended operation lifecycle validation
- Explicit containment and release records
- Authorization expiry and revocation handling
- Multi-step repair workflow references
- Component replacement lineage
- Recovery and rollback coordination
- External authorization and evidence verification
- Federated mini-agent interoperability

These items are prospective and are not part of
the normative v0.1 specification.

---

## [0.1.0] - 2026-10-26

### Initial Release

Established the first version of the
Mini-Agent Repair Protocol (MARP).

MARP defines a lightweight, model-agnostic framework
for bounded AI maintenance operations performed
by modular, least-privilege mini-agents.

The specification focuses on authorization boundaries,
local interventions, independent verification,
and auditable operation records.

### Added

#### Core Specification

- Introduced `SPEC.md` defining MARP v0.1.
- Established seven core design principles:
  - External operation
  - Locality
  - Least privilege
  - Independent verification
  - Replaceability
  - Traceability
  - Safe inaction
- Defined four principal roles:
  - Target
  - Mini-Agent
  - Authority Controller
  - Independent Verifier
- Defined five operation types:
  - `diagnose`
  - `contain`
  - `repair`
  - `verify`
  - `replace`
- Defined seven operation statuses:
  - `proposed`
  - `authorized`
  - `executed`
  - `verified`
  - `rejected`
  - `failed`
  - `held`

#### Repair Record Schema

Added:

`schemas/repair-record.schema.json`

- JSON Schema Draft 2020-12 support.
- Required operation and identity metadata.
- Target identification and bounded scope declarations.
- Authorization status and reference fields.
- Verification status and evidence references.
- State-changing operation constraints.
- Verified-state evidence requirements.
- Component replaceability requirements.
- Strict top-level and nested property validation.

#### Conformance Examples

Added four expected-PASS fixtures:

- `examples/v0.1/pass/diagnose-observation.json`
- `examples/v0.1/pass/authorized-local-containment.json`
- `examples/v0.1/pass/independently-verified-repair.json`
- `examples/v0.1/pass/authorized-component-replacement.json`

Added six expected-FAIL fixtures:

- `examples/v0.1/fail/missing-authorization.json`
- `examples/v0.1/fail/self-authorization.json`
- `examples/v0.1/fail/self-verification.json`
- `examples/v0.1/fail/out-of-scope-intervention.json`
- `examples/v0.1/fail/missing-verification-evidence.json`
- `examples/v0.1/fail/execution-while-held.json`

Total initial conformance coverage:

- 4 expected-PASS examples
- 6 expected-FAIL examples
- 10 examples in total

#### Semantic Validator

Added:

`scripts/validate_examples.py`

The validator performs three validation stages:

1. JSON Schema validation
2. Semantic invariant validation
3. Expected-result matching

Implemented checks include:

- Operation-role consistency
- Read-only diagnosis enforcement
- State-changing operation classification
- Exact operation-scope matching
- Active authorization requirements
- Self-authorization prohibition
- Unauthorized operation rejection
- Invalid success-claim rejection
- Component replaceability checks
- Verification evidence reference consistency
- Self-verification prohibition
- Missing verification evidence rejection
- Verification state consistency

Test-only `expected_result` metadata is removed
before validating the production record structure.

Expected-FAIL examples are considered successful
tests when invalid records are correctly rejected.

#### Continuous Integration

Added:

`.github/workflows/validate.yml`

- Automatic validation on push.
- Automatic validation on pull requests.
- Manual workflow dispatch support.
- Python 3.10 and Python 3.12 validation matrix.
- Python syntax checking.
- Schema and semantic conformance execution.
- Failure on unexpected validation results.
- GitHub Actions job summary output.
- Read-only repository permissions.

#### Dependency Management

Added:

`requirements.txt`

- Declared the `jsonschema` dependency.
- Enabled reproducible dependency installation
  within the supported version range.

#### Documentation

- Added an overview of MARP architecture.
- Documented the five operation types.
- Documented authorization and verification boundaries.
- Provided repository structure and validation instructions.
- Clarified experimental status and security limitations.
- Defined future interoperability directions.

### Security

The initial specification establishes the following
record-level security invariants:

- Mini-agents MUST NOT authorize their own
  state-changing operations.
- Mini-agents MUST NOT independently verify
  their own completed operations.
- State-changing operations require explicit
  granted authorization before execution.
- Operations MUST remain within their recorded
  authorized target scope.
- Component replacement requires the target
  to be marked replaceable.
- Verified operations require verification
  evidence references.
- Pending authorization MUST NOT be treated
  as execution permission.
- Diagnostic observations MUST remain read-only.

These constraints are validated against MARP
records and do not constitute runtime enforcement.

### Validation

Initial conformance testing was reported successful
using GitHub Actions.

Expected validation summary:

```text
=== MARP v0.1 Summary ===
Total examples : 10
Matched        : 10
Mismatched     : 0
[PASS] All MARP v0.1 expectations matched
```

The validation result establishes fixture-level
conformance for the implemented checks.

It does not establish:

- Production system safety
- Repair effectiveness
- Cryptographic authorization authenticity
- Evidence authenticity
- Runtime containment enforcement
- Complete independence of verification entities

### Known Limitations

- Each record describes one operation.
- Full lifecycle transition history is not modeled.
- Authorization expiry and revocation are not
  evaluated against an external authority registry.
- Scope checks use exact string matching.
- Verification independence is checked at the
  identifier level.
- Evidence is represented by references rather
  than authenticated evidence objects.
- Replacement history is not represented.
- Rollback and recovery orchestration are not defined.
- Runtime execution is outside the protocol's
  initial conformance implementation.
- Federated mini-agent coordination is not yet defined.

### Design Statement

> Repair locally.
> Verify independently.
> Preserve the whole.

---

## Versioning Policy

MARP uses the following versioning approach:

- **PATCH:** Editorial corrections and compatible fixes.
- **MINOR:** New compatible protocol capabilities,
  schemas, or validation requirements.
- **MAJOR:** Incompatible changes to normative
  protocol behavior or record formats.

Until version 1.0.0, the protocol remains experimental.

Compatibility expectations may evolve as the
specification matures.

---

## Project Scope

MARP provides a protocol specification, example
records, and automated conformance validation.

It does not provide an autonomous production
repair system.

The long-term objective is to support
interoperable, auditable, and replaceable
AI maintenance components while preserving
explicit human or external authority boundaries.
