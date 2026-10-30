# Mini-Agent Repair Protocol (MARP)

**A modular, auditable protocol for AI diagnosis, containment, repair, coordination, rollback, compensation, and recovery.**

**Version:** v0.5.0  
**Status:** Experimental Specification  
**License:** Apache-2.0

> Repair locally.  
> Verify independently.  
> Recover safely.  
> Preserve the whole.

---

## 1. Overview

The Mini-Agent Repair Protocol (MARP) defines a structured approach to maintaining AI systems through small, modular, and replaceable agents.

Rather than modifying an entire AI system, MARP focuses on bounded interventions at explicitly authorized components and interfaces.

Its central principle is:

**A repair agent must not acquire unlimited authority simply because a system requires repair.**

MARP separates:

- Diagnosis
- Containment
- Repair
- Verification
- Component replacement
- Lifecycle management
- Causal lineage
- Multi-agent coordination
- Recovery and rollback
- Compensation
- Reconciliation

Every operation must remain within defined authority and scope boundaries.

MARP is model-agnostic and does not require modification of foundation-model weights.

The project provides protocol specifications, JSON Schemas, synthetic examples, and automated conformance validation.

It does not provide an autonomous production repair system.

---

## 2. Design Philosophy

MARP follows ten structural principles.

### 2.1 External Authority

Mini-agents do not grant themselves permission.

State-changing operations require authorization from an external controller.

### 2.2 Locality

Interventions are limited to explicitly identified components, interfaces, and resource scopes.

### 2.3 Least Privilege

Each agent receives only the operations and resource scopes necessary for its assigned task.

### 2.4 Independent Verification

The agent performing a repair must not independently certify its own repair as successful.

Execution and verification are distinct responsibilities.

### 2.5 Traceability

Repair operations, failures, evidence references, authorization decisions, and recovery outcomes are represented through auditable records.

### 2.6 Controlled Coordination

Multiple mini-agents may cooperate, but their dependencies, concurrency, resource conflicts, and authorization boundaries must be checked.

### 2.7 Safe Inaction

When authorization, evidence, or safety conditions are insufficient, the system may hold or reject an operation.

Inaction is a valid safety outcome.

### 2.8 Bounded Recovery

Recovery attempts must remain within explicitly authorized limits.

Failure does not justify unlimited retries.

### 2.9 Reversible Intervention

Where safe and supported, a failed repair may be reversed through an approved rollback point.

However, reversibility must be assessed rather than assumed.

### 2.10 Containment Preservation

Rollback or compensation does not automatically authorize release from containment.

Recovery completion and containment release are separate decisions.

---

## 3. Conceptual Architecture

```text
                AI System / Agent Network
                           |
                           v
                   Observable Boundary
                           |
                           v
                  External Authority
                           |
                           v
                    Mini-Agent Layer
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
       Diagnose         Contain           Repair
                                            |
                                            v
                                     Coordination
                                            |
                                 +----------+----------+
                                 |                     |
                                 v                     v
                              Success                Failure
                                 |                     |
                                 v                     v
                              Verify              Recovery
                                 |                     |
                                 |             +-------+-------+
                                 |             |       |       |
                                 |             v       v       v
                                 |          Rollback Compensate Hold
                                 |             |       |       |
                                 |             +-------+-------+
                                 |                     |
                                 |                     v
                                 |             Independent Verify
                                 |                     |
                                 +----------+----------+
                                            |
                                            v
                                      Reconciliation
                                            |
                                            v
                                      Trace / Receipt
                                            |
                                            v
                                  Conformance Validation
```

This diagram illustrates protocol capabilities and conceptual relationships.

It is not a mandatory execution sequence.

Real implementations must enforce authorization, isolation, execution boundaries, and verification through trusted runtime mechanisms.

---

## 4. Protocol Evolution

MARP evolved through five specification stages.

| Version | Focus | Main Contribution |
|---|---|---|
| v0.1 | Repair Foundation | Bounded operations and independent verification |
| v0.2 | Repair Lifecycle | State transitions, holds, containment, and authorization changes |
| v0.3 | Repair Lineage | Causal history, evidence bindings, and recovery gates |
| v0.4 | Repair Coordination | Multi-agent dependencies, concurrency, conflicts, and reconciliation |
| v0.5 | Safe Recovery | Rollback, compensation, bounded recovery attempts, and recovery verification |

Each version introduces additional structural safeguards.

The purpose is not to create a more powerful autonomous repair agent.

The purpose is to define stronger boundaries around what repair agents may do, how they cooperate, and how their outcomes are evaluated.

---

## 5. Core Operations — v0.1

MARP v0.1 defines five operation types.

| Operation | Purpose |
|---|---|
| `diagnose` | Observe a bounded target without modifying it |
| `contain` | Restrict an affected component or interface |
| `repair` | Restore an authorized component condition |
| `verify` | Evaluate evidence of an operation |
| `replace` | Substitute an eligible component |

Only `diagnose` is classified as non-state-changing in the v0.1 repair record.

Other operations require explicit authorization when entering an active state.

The original repair record is defined in:

`schemas/repair-record.schema.json`

The specification also establishes:

- Operation identity
- Mini-agent identity
- Target identity
- Authorized scope
- Operation status
- Verification metadata
- Evidence references
- Timestamps

An executed operation is not automatically a verified operation.

---

## 6. Repair Lifecycle — v0.2

MARP v0.2 introduces a structured lifecycle for repair operations.

It includes:

- Authorization granted
- Operation held
- Containment applied
- Repair started
- Repair completed
- Verification passed
- Verification failed
- Release approved
- Containment released
- Authorization revoked
- Authorization expired
- Hold resolved

The lifecycle makes it possible to distinguish the execution of an operation from its authorization and verification state.

### Safety Rules

A state-changing operation must not continue under invalid authorization.

Containment must remain active while required safety conditions are unresolved.

A held operation cannot be treated as completed.

Authorization revocation and expiration must be represented explicitly.

### Schema

`schemas/repair-lifecycle-v0.2.schema.json`

---

## 7. Repair Lineage — v0.3

MARP v0.3 introduces causal history and evidence-based recovery decisions.

A repair event is no longer treated only as an isolated record.

Instead, events may be linked into a causal sequence.

```text
Observed Failure
       |
       v
Authorization
       |
       v
Containment
       |
       v
Repair
       |
       v
Verification
       |
       v
Recovery Gate
```

### Main Capabilities

- Event lineage
- Predecessor references
- Causal ordering
- Source-record references
- Evidence bindings
- Authorization bindings
- Hold tracking
- Recovery gate evaluation

### Recovery Gate

The recovery gate evaluates whether required safety conditions have been established.

Possible outcomes include:

- `allowed`
- `denied`
- `indeterminate`

The recovery gate does not grant new authority by itself.

It evaluates recorded conditions.

### Schemas

`schemas/repair-lineage-v0.3.schema.json`

`schemas/hold-resolution-v0.3.schema.json`

### Source Generation

MARP v0.3 includes generated source fixtures.

```bash
python scripts/generate_v0.3_sources.py
```

Check generated sources:

```bash
python scripts/generate_v0.3_sources.py --check
```

These generated records support lineage and source-reference validation.

---

## 8. Multi-Agent Repair Coordination — v0.4

MARP v0.4 extends the protocol from individual repair operations to coordinated work involving multiple mini-agents.

A coordinated repair may require several specialized agents.

For example:

```text
         External Controller
                 |
                 v
          Repair Coordination
                 |
       +---------+---------+
       |         |         |
       v         v         v
    Agent A   Agent B   Agent C
    Diagnose  Repair    Verify
       |         |         |
       +---------+---------+
                 |
                 v
          Reconciliation
```

### Main Capabilities

- Task assignment
- Agent authorization
- Task dependencies
- Concurrent execution limits
- Resource access restrictions
- Conflict detection
- External conflict resolution
- Independent verification
- Coordination reconciliation

### Dependency Safety

Task dependencies must not contain cycles.

A task must not execute before its required predecessors are completed.

### Concurrency Safety

Coordinated execution must remain within the authorized concurrency budget.

Conflicting operations must be blocked, serialized, or resolved under an explicitly defined policy.

### Verification Independence

The agent executing a repair must not independently verify that same repair as successful.

### Schema

`schemas/repair-coordination-v0.4.schema.json`

---

## 9. Safe Rollback and Recovery — v0.5

MARP v0.5 introduces an explicit recovery structure for failed or partially completed repairs.

The objective is to ensure that repair failure does not produce uncontrolled recovery behavior.

A failed repair must not automatically trigger unlimited retries or unrestricted rollback.

Recovery remains subject to external authority, scope restrictions, safety assessment, and independent verification.

### 9.1 Recovery Structure

```text
                Repair Failure
                       |
                       v
                Failure Assessment
                       |
                       v
               Recovery Authorization
                       |
                       v
                Recovery Planning
                       |
          +------------+------------+
          |            |            |
          v            v            v
       Rollback    Compensation  Containment
          |            |            |
          +------------+------------+
                       |
                       v
              Independent Verification
                       |
                       v
                  Reconciliation
                       |
             +---------+---------+
             |         |         |
             v         v         v
         Recovered  Contained  Rejected
                       |
                       v
              Containment Preserved
```

`indeterminate` is also a valid reconciliation decision.

### 9.2 Recovery Methods

MARP v0.5 defines four recovery methods.

| Method | Purpose |
|---|---|
| `rollback` | Restore an assessed compatible recovery point |
| `compensation` | Perform an authorized compensating operation |
| `containment_only` | Preserve containment without executing rollback or compensation |
| `no_action` | Record a decision not to perform a recovery action |

The method is selected according to recorded conditions and authorization.

### 9.3 Safe Rollback

A rollback requires a recovery point.

The recovery point includes:

- Recovery point identifier
- State reference
- State evidence references
- Compatibility assessment
- Rollback scope
- Optional assessment metadata

Compatibility assessments include:

- `compatible`
- `incompatible`
- `indeterminate`

An executed rollback must not rely on an incompatible or indeterminate recovery point.

The existence of an old snapshot does not establish that restoring it is safe.

### 9.4 Compensation

Not every operation can be reversed.

When a direct rollback is inappropriate, an explicitly authorized compensating operation may be used.

Compensation records include:

- Original operation reference
- Compensating operation
- Intended mitigation
- Residual risks
- Supporting evidence

Compensation is not equivalent to complete reversal.

Residual risks must not be concealed.

### 9.5 Bounded Recovery Attempts

Recovery attempts are limited by the authorization record.

A recovery action cannot exceed the authorized attempt budget.

The protocol also limits concurrent recovery execution.

Successful completion does not retroactively justify an unauthorized extra attempt.

### 9.6 Authorization and Revocation

Recovery authority is external to the executing mini-agent.

A recovery operation must remain within:

- Authorized operation types
- Authorized resource scopes
- Authorized target
- Authorized execution period
- Agent-specific authorization boundaries
- Attempt and concurrency limits

A revoked recovery agent must not dispatch or continue unauthorized recovery operations.

### 9.7 Independent Recovery Verification

Recovery completion and recovery verification are distinct.

A completed rollback is not automatically a recovered system.

An independent verifier evaluates the recovery result.

Verification statuses include:

- `passed`
- `failed`
- `indeterminate`

Self-verification does not satisfy the independent verification requirement.

### 9.8 Recovery Reconciliation

Recovery reconciliation evaluates the recorded recovery outcome.

Possible decisions are:

| Decision | Meaning |
|---|---|
| `recovered` | Required recovery actions have passed independent verification |
| `contained` | The affected state remains contained |
| `rejected` | The recovery result or plan is not accepted |
| `indeterminate` | Available evidence is insufficient for a conclusive decision |

A `recovered` decision requires successful independent verification of the applicable recovery actions.

Unresolved recovery actions must not be silently accepted.

### 9.9 Containment Preservation

MARP v0.5 separates recovery from containment release.

A rollback may complete while containment remains active.

A compensation operation may mitigate the failure without resolving every residual risk.

Containment release requires a separate authorized safety decision.

### Schema

`schemas/repair-recovery-v0.5.schema.json`

### Specification

`specs/marp-v0.5.md`

---

## 10. Repository Structure

```text
mini-agent-repair-protocol/
├── .github/
│   └── workflows/
│       └── validate.yml
│
├── schemas/
│   ├── repair-record.schema.json
│   ├── repair-lifecycle-v0.2.schema.json
│   ├── repair-lineage-v0.3.schema.json
│   ├── hold-resolution-v0.3.schema.json
│   ├── repair-coordination-v0.4.schema.json
│   └── repair-recovery-v0.5.schema.json
│
├── specs/
│   └── marp-v0.5.md
│
├── examples/
│   ├── v0.1/
│   │   ├── pass/
│   │   └── fail/
│   ├── v0.2/
│   │   ├── pass/
│   │   └── fail/
│   ├── v0.3/
│   │   ├── pass/
│   │   ├── fail/
│   │   └── sources/
│   ├── v0.4/
│   │   ├── pass/
│   │   └── fail/
│   └── v0.5/
│       ├── pass/
│       └── fail/
│
├── scripts/
│   ├── validate_examples.py
│   └── generate_v0.3_sources.py
│
├── requirements.txt
├── SPEC.md
├── README.md
├── CHANGELOG.md
└── LICENSE
```

Directory contents are summarized for readability.

The `examples/` directory contains version-specific positive and negative conformance fixtures.

---

## 11. Conformance Testing

MARP uses three primary validation layers.

### Layer 1: JSON Schema Validation

Validates:

- Required properties
- Data types
- Enumerations
- Structural constraints
- Conditional requirements
- Timestamp formats
- Record structure

JSON Schemas use Draft 2020-12.

### Layer 2: Semantic Validation

Validates relationships that cannot be established by JSON structure alone.

Examples include:

- Authorization boundaries
- Scope consistency
- Event chronology
- Causal lineage
- Task dependencies
- Resource conflicts
- Attempt and concurrency budgets
- Recovery point compatibility
- Authorization revocation
- Verification independence
- Reconciliation consistency

### Layer 3: Fixture Expectation Matching

Each synthetic fixture declares:

- `PASS`, for an accepted record
- `FAIL`, for an intentionally rejected record

The `expected_result` fixture metadata is removed before production-schema validation.

For selected versions, negative fixtures are also checked against expected error codes.

A correctly rejected FAIL fixture counts as a successful conformance test.

---

## 12. Validation Results

The integrated MARP v0.1-v0.5 suite contains 64 synthetic fixtures.

| Version | Expected PASS | Expected FAIL | Total |
|---|---:|---:|---:|
| v0.1 | 4 | 6 | 10 |
| v0.2 | 6 | 6 | 12 |
| v0.3 | 6 | 8 | 14 |
| v0.4 | 6 | 8 | 14 |
| v0.5 | 6 | 8 | 14 |
| **Total** | **28** | **36** | **64** |

The integrated GitHub Actions workflow has passed the configured conformance suite.

Expected summary:

```text
=== MARP Summary ===
Total: 64
Matched: 64
Mismatched: 0
[PASS] All MARP v0.1-v0.5 expectations matched
```

These results establish consistency with the implemented conformance checks and supplied synthetic examples.

They do not prove real-world repair effectiveness or system-wide safety.

---

## 13. Running Validation Locally

### Requirements

Python 3.10 or newer.

The GitHub Actions matrix tests Python 3.10 and Python 3.12.

### Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### Generate v0.3 Source Fixtures

```bash
python scripts/generate_v0.3_sources.py
```

### Check Generated Sources

```bash
python scripts/generate_v0.3_sources.py --check
```

### Run Integrated Validation

```bash
python scripts/validate_examples.py
```

The validator checks all supported protocol versions.

A nonzero exit code indicates a conformance mismatch or validation failure.

---

## 14. GitHub Actions

Automated validation is configured at:

`.github/workflows/validate.yml`

The workflow runs on:

- Push
- Pull request
- Manual workflow dispatch

### Workflow Checks

1. Required file and directory checks
2. Python syntax validation
3. JSON Schema validation
4. Fixture count verification
5. v0.3 source fixture generation
6. Generated source consistency checks
7. Integrated MARP conformance validation
8. Validation summary verification
9. GitHub Actions job summary publication

The workflow tests Python 3.10 and Python 3.12.

The current suite expects:

- 28 accepted fixtures
- 36 rejected fixtures
- 64 expectation matches
- Zero mismatches

A successful workflow does not authorize deployment into production environments.

---

## 15. Security Considerations

MARP is a specification and synthetic conformance-testing project.

It does not implement or guarantee:

- Cryptographic authorization verification
- Cryptographic evidence authenticity
- Secure execution sandboxing
- Production-grade runtime isolation
- Trusted rollback snapshot storage
- Actual rollback execution
- Transactional compensation guarantees
- Distributed consensus
- Runtime revocation enforcement
- Complete recovery from arbitrary failures
- System-wide safety certification

Authorization records are not equivalent to externally verified authorization.

Evidence references are not equivalent to authenticated evidence.

A compatible recovery point in a synthetic fixture is not proof that a real snapshot can safely be restored.

Implementations must provide trusted enforcement and independently validate these properties.

MARP must not be used as a substitute for operational safety controls.

---

## 16. Interoperability

MARP is designed to remain independent of specific AI vendors, foundation models, and runtime architectures.

Potential integration areas include:

- Trace and provenance systems
- External authorization controllers
- AI safety protocols
- Distributed AI immune networks
- Repair and containment services
- Multi-agent orchestration frameworks
- Recovery and rollback infrastructure

Potential companion architectures include:

- TACP
- Resilient AI Safety Principles
- SAIN
- Kazene-based orchestration systems

These are conceptual integration possibilities.

They are not claims of tested interoperability.

Interoperability must not implicitly expand an agent's authority.

---

## 17. Version Scope and Future Work

### Completed Specification Stages

**v0.1 — Foundation**

Bounded repair operations, authorization, and independent verification.

**v0.2 — Lifecycle**

State transitions, holds, containment, and authorization changes.

**v0.3 — Lineage**

Causal history, source references, evidence bindings, and recovery gates.

**v0.4 — Coordination**

Multi-agent task dependencies, concurrency, resource conflicts, and reconciliation.

**v0.5 — Safe Recovery**

Compatible rollback points, compensation plans, bounded attempts, independent recovery verification, and containment preservation.

### Potential Future Extensions

Possible future work includes:

- Signed authorization and evidence receipts
- Runtime enforcement interfaces
- Tamper-evident execution histories
- Recovery point integrity verification
- Cross-agent recovery coordination
- Recovery performance benchmarks
- Failure-injection testing
- Federated recovery knowledge sharing
- Interoperability tests with external safety protocols

These are research directions, not implemented features.

---

## 18. Project Scope

MARP focuses on structural safety rather than autonomous repair performance.

It separates:

1. What an agent is allowed to do
2. What an agent actually does
3. What evidence exists
4. Who verifies the result
5. Whether the outcome can be accepted
6. What happens when the repair fails

The protocol is intended to make these relationships explicit, inspectable, and testable.

It does not modify foundation-model weights.

It does not operate production infrastructure.

It does not grant agents independent authority.

---

## 19. Guiding Statement

> A capable repair agent is not necessarily
> an authorized repair agent.
>
> An executed repair is not necessarily
> a verified repair.
>
> A completed rollback is not necessarily
> a successful recovery.
>
> Recovery does not automatically authorize
> containment release.

**Repair locally. Verify independently. Recover safely. Preserve the whole.**

---

## 20. License

Licensed under the Apache License, Version 2.0.

See `LICENSE` for the complete license text.

