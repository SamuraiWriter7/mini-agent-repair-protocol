# Changelog

All notable changes to the Mini-Agent Repair Protocol (MARP) are documented in this file.

This project follows the principles of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and uses [Semantic Versioning](https://semver.org/).

MARP is an experimental protocol specification.

Version numbers indicate specification evolution and conformance coverage, not production deployment readiness.

---

## [Unreleased]

### Planned

Potential future extensions include:

- Cryptographically signed authorization receipts
- Authenticated evidence and provenance records
- Trusted recovery-point integrity verification
- Runtime authorization enforcement
- Automated containment enforcement interfaces
- Recovery execution and failure-injection benchmarks
- Cross-agent recovery coordination
- Federated recovery knowledge sharing
- External interoperability conformance tests

These are research and design directions.

They are not implemented features or normative requirements of MARP v0.5.

---

## [0.5.0] - 2026-10-30

### Safe Rollback, Compensation, and Recovery

Extended MARP with a structured recovery model for failed or partially completed AI repair operations.

MARP v0.5 introduces explicit controls for rollback eligibility, compensating actions, bounded recovery attempts, independent recovery verification, and recovery reconciliation.

The central principle is:

**A failed repair does not authorize unlimited or unsafe recovery behavior.**

### Added

#### Recovery Specification

Added:

`specs/marp-v0.5.md`

Defined recovery structures for:

- Failure assessment
- External recovery authorization
- Recovery agent assignment
- Recovery action planning
- Rollback eligibility
- Compensation operations
- Containment preservation
- Recovery attempt budgets
- Recovery verification
- Recovery reconciliation

#### Recovery Schema

Added:

`schemas/repair-recovery-v0.5.schema.json`

The schema uses JSON Schema Draft 2020-12.

Recovery records include:

- Recovery identifier
- Target identifier
- Coordination and lineage references
- External authority metadata
- Failure assessment
- Recovery agents
- Recovery actions
- Independent verification records
- Reconciliation decision
- Evaluation timestamp

Defined four recovery methods:

- `rollback`
- `compensation`
- `containment_only`
- `no_action`

#### Safe Rollback

Introduced explicit recovery-point records.

A recovery point includes:

- Recovery point identifier
- State reference
- State evidence references
- Compatibility assessment
- Rollback scope
- Optional assessment metadata

Defined compatibility states:

- `compatible`
- `incompatible`
- `indeterminate`

An executed rollback must use a compatible recovery point within its authorized scope.

A previous snapshot is not automatically a safe recovery point.

#### Compensation

Introduced compensation records for operations that cannot be safely reversed through direct rollback.

Compensation records include:

- Original operation identifier
- Compensating operation
- Intended mitigation
- Residual risks
- Supporting evidence

Compensation does not imply complete reversal of the original operation.

#### Recovery Attempt Boundaries

Introduced:

- Maximum recovery attempt count
- Maximum concurrent recovery operations
- Recovery authorization time boundaries
- Agent-specific authorization time boundaries
- Revocation-aware recovery validation

Successful recovery does not retroactively justify an unauthorized extra attempt.

#### Independent Recovery Verification

Defined a separate verification stage for completed recovery operations.

Supported verification outcomes:

- `passed`
- `failed`
- `indeterminate`

The recovery agent must not independently certify its own recovery action.

A completed rollback is not automatically a verified recovery.

#### Recovery Reconciliation

Defined recovery reconciliation outcomes:

- `recovered`
- `contained`
- `rejected`
- `indeterminate`

A `recovered` decision requires successful independent verification of applicable recovery actions.

Unresolved actions must not be silently accepted.

Containment release remains separate from recovery completion.

#### Positive Conformance Fixtures

Added six expected-PASS examples:

- `examples/v0.5/pass/authorized-rollback.json`
- `examples/v0.5/pass/verified-rollback.json`
- `examples/v0.5/pass/compensated-partial-repair.json`
- `examples/v0.5/pass/containment-preserved.json`
- `examples/v0.5/pass/bounded-recovery-attempts.json`
- `examples/v0.5/pass/independent-recovery-reconciliation.json`

#### Negative Conformance Fixtures

Added eight expected-FAIL examples:

- `examples/v0.5/fail/missing-recovery-point.json`
- `examples/v0.5/fail/unsafe-rollback.json`
- `examples/v0.5/fail/unauthorized-recovery-scope.json`
- `examples/v0.5/fail/cyclic-recovery-dependency.json`
- `examples/v0.5/fail/recovery-budget-exceeded.json`
- `examples/v0.5/fail/revoked-recovery-dispatched.json`
- `examples/v0.5/fail/self-verified-recovery.json`
- `examples/v0.5/fail/unverified-recovery-accepted.json`

Total v0.5 fixtures:

- 6 expected-PASS
- 8 expected-FAIL
- 14 total

### Changed

#### Integrated Semantic Validator

Updated:

`scripts/validate_examples.py`

Extended the integrated validator to cover MARP v0.1 through v0.5.

Added recovery-specific semantic checks for:

- Missing recovery points
- Incompatible rollback execution
- Unauthorized recovery scopes
- Cyclic recovery dependencies
- Recovery attempt budget violations
- Recovery authorization revocation
- Recovery concurrency limits
- Self-verification
- Unverified recovery acceptance
- Reconciliation consistency
- Premature containment release

Negative fixtures are checked against expected error codes.

#### GitHub Actions

Updated:

`.github/workflows/validate.yml`

Extended automated validation from 50 to 64 fixtures.

Maintained:

- Python 3.10 and Python 3.12 matrix
- JSON Schema validation
- Python syntax checking
- v0.3 source fixture generation
- Generated-source consistency checks
- Fixture count validation
- Expected-result matching
- GitHub Actions job summaries

#### Documentation

Updated:

`README.md`

Consolidated the architecture and security boundaries of MARP v0.1 through v0.5.

### Validation

The integrated GitHub Actions workflow passed after the v0.5 extension.

Validation coverage:

| Version | PASS | FAIL | Total |
|---|---:|---:|---:|
| v0.1 | 4 | 6 | 10 |
| v0.2 | 6 | 6 | 12 |
| v0.3 | 6 | 8 | 14 |
| v0.4 | 6 | 8 | 14 |
| v0.5 | 6 | 8 | 14 |
| **Total** | **28** | **36** | **64** |

Reported integrated validation result:

```text
=== MARP Summary ===
Total: 64
Matched: 64
Mismatched: 0
[PASS] All MARP v0.1-v0.5 expectations matched
```

The result establishes conformance against the implemented synthetic checks.

It does not establish production recovery effectiveness or system-wide safety.

### Security

MARP v0.5 establishes the following recovery safety principles:

1. Recovery must remain externally authorized.
2. Rollback requires a compatible recovery point.
3. Recovery actions must remain within authorized scopes.
4. Recovery dependencies must not contain cycles.
5. Recovery attempts must remain bounded.
6. Revoked recovery authorization must not permit further execution.
7. Recovery execution and verification must remain independent.
8. Recovery completion does not automatically mean recovery success.
9. Unverified recovery must not be accepted as recovered.
10. Containment must not be released solely because recovery completed.

### Known Limitations

- Recovery actions are represented as records, not executed by the validator.
- Recovery-point compatibility is based on declared assessment metadata.
- Evidence references are not cryptographically authenticated.
- Authorization authenticity depends on external enforcement.
- Actual state restoration is outside the conformance suite.
- Compensation does not guarantee complete reversal.
- Runtime containment must be enforced by external mechanisms.
- Agent independence is checked at the recorded identity level.
- Synthetic conformance does not establish operational recovery safety.

---

## [0.4.0] - 2026-10-30

### Multi-Agent Repair Coordination

Extended MARP from individual repair operations to coordinated workflows involving multiple mini-agents.

### Added

#### Coordination Schema

Added:

`schemas/repair-coordination-v0.4.schema.json`

Defined records for:

- Coordinated repair operations
- Agent assignments
- Task dependencies
- Resource access scopes
- Concurrency restrictions
- Conflict records
- External conflict resolution
- Independent verification
- Coordination reconciliation

#### Dependency Validation

Introduced checks for:

- Unknown task dependencies
- Cyclic dependency graphs
- Execution before dependency completion
- Invalid execution ordering

#### Conflict and Concurrency Controls

Introduced:

- Concurrency budgets
- Shared-resource conflict detection
- Serialized execution
- Explicit conflict dispositions
- External conflict-resolution references

#### Independent Verification

Extended independent verification requirements to coordinated repair workflows.

A repair agent cannot independently verify its own work as a substitute for external verification.

#### Conformance Fixtures

Added six expected-PASS and eight expected-FAIL fixtures.

Negative tests cover:

- Cyclic task dependencies
- Unknown task dependencies
- Concurrent write conflicts
- Concurrency budget violations
- Unauthorized task scopes
- Self-verification acceptance
- Unresolved conflict acceptance
- Revoked task dispatch

### Changed

Extended the integrated validator and GitHub Actions workflow to support v0.1 through v0.4.

### Validation

v0.4 adds 14 fixtures.

Cumulative coverage through v0.4:

- 22 expected-PASS fixtures
- 28 expected-FAIL fixtures
- 50 fixtures total

The integrated GitHub Actions workflow passed.

### Security

The v0.4 coordination model maintains external authorization and least-privilege boundaries.

Agent cooperation does not imply shared authority.

---

## [0.3.0] - 2026-10-30

### Repair Lineage and Recovery Gates

Introduced causal repair history, source records, evidence bindings, and recovery gate evaluation.

### Added

#### Repair Lineage Schema

Added:

`schemas/repair-lineage-v0.3.schema.json`

Defined:

- Event identifiers
- Predecessor references
- Causal ordering
- Target consistency
- Source-record references
- Evidence bindings
- Authorization bindings
- Recovery gate decisions

#### Hold Resolution Schema

Added:

`schemas/hold-resolution-v0.3.schema.json`

Introduced explicit records for resolving held operations.

#### Source Fixture Generation

Added:

`scripts/generate_v0.3_sources.py`

Supports:

- Generation of source fixtures
- Source consistency checking
- Repeatable validation of referenced records

#### Recovery Gate

Introduced three recovery gate outcomes:

- `allowed`
- `denied`
- `indeterminate`

The recovery gate evaluates recorded safety conditions without independently granting new authority.

#### Conformance Fixtures

Added six expected-PASS and eight expected-FAIL fixtures.

Negative tests cover:

- Missing predecessor references
- Circular lineage
- Cross-target lineage
- Verification before repair completion
- Release without approval
- Release with active holds
- Invalid evidence bindings
- Reuse of revoked authorization

### Changed

Extended semantic validation to cover lineage continuity and cross-record relationships.

### Validation

v0.3 adds 14 fixtures.

Cumulative coverage through v0.3:

- 16 expected-PASS fixtures
- 20 expected-FAIL fixtures
- 36 fixtures total

### Security

The v0.3 specification strengthens traceability and prevents unsupported recovery or release decisions.

Evidence references remain subject to external authenticity verification.

---

## [0.2.0] - 2026-10-30

### Repair Lifecycle and Containment

Extended MARP with explicit lifecycle transitions, containment states, holds, and authorization changes.

### Added

#### Lifecycle Schema

Added:

`schemas/repair-lifecycle-v0.2.schema.json`

Defined lifecycle events including:

- `authorization_granted`
- `operation_held`
- `containment_applied`
- `repair_started`
- `repair_completed`
- `verification_passed`
- `verification_failed`
- `release_approved`
- `containment_released`
- `authorization_revoked`
- `authorization_expired`
- `hold_resolved`

#### Lifecycle Safety

Introduced checks for:

- Valid state transitions
- Active authorization
- Authorization expiration
- Authorization revocation
- Containment preservation
- Verification evidence
- Release authorization
- Hold resolution

#### Conformance Fixtures

Added six expected-PASS and six expected-FAIL fixtures.

### Changed

Extended the integrated validator with v0.2 lifecycle semantic checks.

### Validation

v0.2 adds 12 fixtures.

Cumulative coverage through v0.2:

- 10 expected-PASS fixtures
- 12 expected-FAIL fixtures
- 22 fixtures total

### Security

A state-changing repair must not continue without valid authorization.

Containment release and repair completion are separate lifecycle events.

---

## [0.1.0] - 2026-10-26

### Initial Release

Established the first version of the Mini-Agent Repair Protocol (MARP).

MARP defines a lightweight, model-agnostic framework for bounded AI maintenance operations performed by modular, least-privilege mini-agents.

The initial specification focuses on authorization boundaries, local interventions, independent verification, and auditable operation records.

### Added

#### Core Specification

Added:

`SPEC.md`

Established seven foundational principles:

1. External operation
2. Locality
3. Least privilege
4. Independent verification
5. Replaceability
6. Traceability
7. Safe inaction

Defined five operation types:

- `diagnose`
- `contain`
- `repair`
- `verify`
- `replace`

Defined seven operation statuses:

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

Features include:

- JSON Schema Draft 2020-12
- Operation identity and type
- Mini-agent identity and role
- Target identity and scope
- Authorization metadata
- Verification metadata
- Evidence references
- State-changing operation constraints
- Component replaceability requirements

#### Conformance Fixtures

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

Total initial coverage:

- 4 expected-PASS fixtures
- 6 expected-FAIL fixtures
- 10 fixtures total

#### Semantic Validator

Added:

`scripts/validate_examples.py`

Implemented:

- JSON Schema validation
- Semantic invariant validation
- Expected-result matching
- Authorization boundary checks
- Operation-role consistency
- Scope restrictions
- Independent verification
- Evidence reference consistency
- Component replacement eligibility

#### Continuous Integration

Added:

`.github/workflows/validate.yml`

Features include:

- Push validation
- Pull request validation
- Manual workflow dispatch
- Python 3.10 and Python 3.12
- Read-only repository permissions
- Syntax checking
- Schema validation
- Conformance validation

#### Dependency Management

Added:

`requirements.txt`

Declared dependencies required by the conformance validator.

### Validation

Initial conformance testing passed through GitHub Actions.

Initial coverage:

- 10 fixtures
- 10 expected matches
- Zero mismatches

### Security

The initial specification prohibits:

- Self-authorization
- Self-verification
- Unauthorized state-changing operations
- Out-of-scope intervention
- Unauthorized component replacement
- Unsupported verification claims
- Execution under insufficient authorization

These safeguards are evaluated through records and synthetic tests.

They do not constitute runtime enforcement.

### Design Statement

> Repair locally.  
> Verify independently.  
> Preserve the whole.

---

## Versioning Policy

MARP follows Semantic Versioning principles.

- **PATCH:** Editorial corrections and compatible fixes.
- **MINOR:** New protocol capabilities, schemas, and validation requirements.
- **MAJOR:** Incompatible changes to normative protocol behavior or record formats.

Before version 1.0.0, MARP remains experimental.

Compatibility expectations may evolve.

GitHub Release tags and specification milestones should be distinguished when tracking publication history.

---

## Project Scope

MARP provides:

- Protocol specifications
- JSON Schemas
- Synthetic positive and negative fixtures
- Semantic validation
- Automated conformance testing
- Documented authorization and recovery boundaries

MARP does not provide:

- Autonomous production repair agents
- Production rollback execution
- Guaranteed system recovery
- Cryptographic authorization infrastructure
- Runtime safety certification

The long-term objective is to support interoperable, auditable, and replaceable AI maintenance components while preserving external authorization and independent verification.

---

## Guiding Statement

> A capable repair agent is not necessarily an authorized repair agent.
>
> An executed repair is not necessarily a verified repair.
>
> A completed rollback is not necessarily a successful recovery.
>
> Recovery does not automatically authorize containment release.

**Repair locally. Verify independently. Recover safely. Preserve the whole.**

