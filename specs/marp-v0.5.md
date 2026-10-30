# Mini-Agent Repair Protocol (MARP) v0.5

Version: 0.5.0
Status: Draft
Title: Safe Rollback, Compensation and Recovery
Extends: MARP v0.1-v0.4

## 1. Purpose

MARP v0.5 defines bounded recovery operations
for failed or partially completed coordinated
repairs.

It introduces:

- Recovery assessment
- Rollback eligibility
- Compensation planning
- Recovery dependency ordering
- External recovery authorization
- Independent recovery verification
- Recovery reconciliation
- Fail-closed containment preservation

MARP v0.5 does not authorize automatic
production recovery or containment release.

## 2. Core Principles

### 2.1 Recovery Is Not Repetition

A failed repair MUST NOT be retried
automatically without checking the cause
of failure and applicable authorization.

### 2.2 No Assumed Reversibility

An executed operation MUST NOT be treated
as reversible unless supported by evidence.

### 2.3 External Authorization

Every state-changing rollback or
compensation action MUST require valid
external authorization.

The recovering agent MUST NOT issue
authorization to itself.

### 2.4 Bounded Recovery

Every recovery plan MUST specify:

- Authorized target
- Permitted resource scopes
- Maximum recovery attempts
- Maximum concurrent recovery tasks
- Applicable authorization
- Termination conditions

Exceeding any bound MUST suspend
the affected recovery plan.

### 2.5 Independent Verification

A recovery action MUST NOT be independently
verified by the same agent that executed it.

### 2.6 Containment Preservation

Failed, incomplete, or indeterminate
recovery MUST NOT implicitly release
existing containment.

### 2.7 Trace Preservation

Recovery MUST append evidence and events
without erasing earlier repair history.

Historical records MUST remain distinguishable
from later recovery records.

## 3. Scope

The initial v0.5 profile supports:

- One primary recovery target
- One associated v0.4 coordination plan
- One associated v0.3 lineage
- Multiple bounded recovery actions
- Explicit rollback or compensation methods
- Independent verification
- One final reconciliation decision

Cross-organization recovery transactions
and distributed consensus are out of scope.

## 4. Recovery Bundle

A recovery bundle MUST contain:

- schema_version
- recovery_id
- target_id
- coordination_id
- lineage_id
- authority
- failure_assessment
- recovery_actions
- recovery_verifications
- reconciliation
- evaluated_at

A bundle MUST NOT be considered trusted
merely because its JSON is schema-valid.

## 5. Failure Assessment

A failure assessment MUST identify:

- failure_id
- failed_task_ids
- failure_type
- observed_at
- evidence_ids
- affected_scopes
- containment_status

Supported failure types:

- repair_failed
- verification_failed
- partial_completion
- state_divergence
- authorization_revoked
- resource_conflict
- unknown

An unknown failure MUST NOT justify
an unrestricted recovery operation.

## 6. Recovery Methods

Supported recovery methods:

- rollback
- compensation
- containment_only
- no_action

### 6.1 Rollback

Rollback restores an explicitly identified
previous state.

Rollback MUST require:

- A known recovery point
- Evidence of the previous state
- Current-state compatibility assessment
- Authorized rollback scope
- A verification plan

Rollback MUST NOT be accepted if a required
recovery point is unknown or untrusted.

### 6.2 Compensation

Compensation is a separately authorized
operation intended to mitigate consequences
that cannot be safely reversed.

A compensation action MUST identify:

- The original affected operation
- The compensating operation
- The intended mitigation
- Residual risks
- Supporting evidence

Compensation MUST NOT claim that the original
operation was erased or undone.

### 6.3 Containment Only

Containment-only recovery preserves or
strengthens isolation without claiming
that repair has succeeded.

This is a valid safe outcome when
rollback or compensation cannot proceed.

### 6.4 No Action

No-action MUST have an explicit reason.

It MUST NOT be interpreted as a
successful recovery.

## 7. Recovery Actions

Each recovery action MUST identify:

- action_id
- source_task_id
- method
- assigned_agent_id
- target_id
- resource_scope
- authorization_id
- depends_on
- status
- evidence_ids

Action statuses:

- planned
- authorized
- running
- held
- completed
- failed
- cancelled

Completed state-changing actions MUST
include execution evidence.

## 8. Recovery Dependency Graph

Recovery actions MUST form an acyclic
dependency graph.

A recovery action MUST NOT start until
its required predecessors have completed
successfully.

Where rollback order matters, the order
MUST be explicit.

The coordinator MUST NOT assume that
the reverse of the original execution order
is always safe.

## 9. Authorization and Limits

A recovery plan MUST define:

- External controller identity
- Recovery authorization ID
- Authorized operations and scopes
- Issuance and expiration timestamps
- Revocation status
- Maximum attempts
- Maximum concurrency

State-changing actions MUST remain inside
their applicable limits.

Revoked or expired authorization MUST
prevent further dispatch.

Previously completed authorized work
MUST retain its historical record.

## 10. Recovery Verification

A recovery verification MUST reference:

- The recovery action
- The verifier identity
- Verification evidence
- Verification outcome
- Verification timestamp

Outcomes:

- passed
- failed
- indeterminate

The verifier MUST be different from
the recovery executor.

Verification of one action MUST NOT imply
verification of unrelated actions.

## 11. Recovery Reconciliation

Supported decisions:

- recovered
- contained
- rejected
- indeterminate

### 11.1 Recovered

A recovered decision requires:

- All required recovery actions completed
- Independent verification passed
- Required evidence resolved
- No unresolved blocking conflict
- No unauthorized action
- Recovery limits respected

Recovered means recovery objectives
were satisfied.

It does not mean containment has
automatically been released.

### 11.2 Contained

Contained means that the system remains
in a bounded safe suspension state.

Repair or full recovery may remain
incomplete.

### 11.3 Rejected

Rejected means that a definite safety
or integrity violation was detected.

### 11.4 Indeterminate

Indeterminate means the available evidence
is insufficient to establish the outcome.

Neither rejected nor indeterminate
authorizes containment release.

## 12. Relationship to Existing Versions

MARP v0.5 MUST preserve:

- v0.1 least-privilege repair boundaries
- v0.2 lifecycle and containment rules
- v0.3 causal lineage and recovery gate
- v0.4 task coordination and conflict rules

Recovery completion MUST NOT override
the v0.3 external release requirements.

A v0.5 recovery bundle MUST identify
its parent coordination and lineage.

## 13. Required Validation

A conforming validator MUST detect:

- Missing recovery point
- Unsafe rollback eligibility
- Unauthorized recovery scope
- Recovery dependency cycles
- Unknown recovery dependencies
- Recovery concurrency violations
- Recovery attempt budget violations
- Revoked authorization reuse
- Self-verification
- Missing verification evidence
- Unresolved recovery accepted as complete
- Premature containment release
- Invalid recovery references

A validator MUST recompute the outcome
rather than trusting a declared decision.

## 14. Non-Goals

MARP v0.5 does not define:

- Automatic unrestricted retry
- Automatic production deployment
- Autonomous privilege elevation
- Distributed consensus
- Universal reversible operations
- Deletion of immutable history
- Automatic containment release
- Guaranteed reversal of external effects

## 15. Design Statement

Do not repeat blindly.
Do not assume reversibility.
Restore only what is safe.
Compensate only with authority.
Preserve containment when uncertain.
Verify independently.
Keep the full causal trace.
