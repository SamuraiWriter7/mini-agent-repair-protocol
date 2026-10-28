# Mini-Agent Repair Protocol (MARP) v0.3

Version: 0.3.0
Status: Draft
Title: Repair Lineage and Causal Verification
Extends: MARP v0.1 and v0.2

## 1. Purpose

MARP v0.3 defines a repair-lineage verification
layer for auditable AI maintenance workflows.

It connects repair and lifecycle records into
a bounded, verifiable event history.

The purpose is to prevent a system from
accepting an isolated success claim as proof
that the necessary preceding operations
actually occurred in the recorded history.

## 2. Compatibility

MARP v0.3 MUST preserve the normative safety
constraints of v0.1 and v0.2.

Existing records and schemas remain unchanged.

Version 0.3 introduces a separate Repair
Lineage Bundle that references earlier records.

A v0.1 or v0.2 record MUST NOT be assumed
to contain information it does not provide.

## 3. Core Principles

### 3.1 Explicit Lineage

Every event in a repair lineage MUST have
a unique event identity.

### 3.2 Causal Precedence

A required predecessor event MUST be
established before its dependent event.

### 3.3 Evidence Binding

Evidence references MUST identify their
associated event, operation, and target.

### 3.4 Independent Verification

A repairing agent MUST NOT serve as the
sole independent verifier of its own repair.

### 3.5 No Implicit Release

Repair completion and verification success
MUST NOT automatically release containment.

### 3.6 Fail-Closed History

Missing, conflicting, incomplete, or
unresolvable histories MUST NOT authorize
a release decision.

### 3.7 No Implicit Authority

A lineage reference MUST NOT be interpreted
as an authorization grant.

## 4. Repair Lineage Bundle

The v0.3 bundle MUST contain:

- schema_version
- lineage_id
- target_id
- containment_id
- records
- evidence_bindings
- recovery_gate
- evaluated_at

Each record entry MUST contain:

- event_id
- source_version
- record_reference
- operation_id
- target_id
- actor_id
- event_type
- previous_state
- next_state
- timestamp
- previous_event_id

The first record MUST use a null
previous_event_id.

Subsequent records MUST reference the
immediately preceding event.

The initial v0.3 profile supports one
linear history for one target and one
containment lifecycle.

Branching and merged histories are
outside the scope of v0.3.

## 5. Source Records

Each event entry MUST reference an existing
MARP record or a defined v0.3 extension event.

The validator MUST resolve source records
from an explicitly supplied trusted dataset.

A reference that cannot be resolved MUST
cause validation failure.

The validator MUST confirm that event
metadata matches its referenced source.

Untrusted inline descriptions MUST NOT
replace source record validation.

## 6. Lineage Integrity

A conforming bundle MUST satisfy:

1. Event IDs are unique.
2. Source references resolve.
3. Target IDs are consistent.
4. Containment IDs are consistent.
5. Every non-root predecessor exists.
6. References contain no cycles.
7. History ordering is deterministic.
8. State transitions are continuous.
9. Required event types are present.
10. Referenced source records are valid.

Timestamps MUST be parsed as timezone-aware
instants.

For a strictly ordered lineage:

event[i].timestamp <= event[i+1].timestamp

Equal timestamps do not establish
causal precedence by themselves.

The explicit predecessor relationship
determines the declared event order.

## 7. Repair Causality

A normal successful repair lineage follows
the conceptual sequence:

authorization_granted
    ->
containment_applied
    ->
repair_started
    ->
repair_completed
    ->
verification_passed
    ->
release_approved
    ->
containment_released

The sequence represents required logical
dependencies for a successful release.

Other events MAY intervene where permitted.

A state-changing action MUST have an
applicable valid authorization.

Verification MUST follow the repair being
verified.

Release approval MUST follow successful
independent verification.

Containment release MUST follow explicit
release approval.

## 8. Authorization Continuity

Every state-changing operation MUST be
covered by an applicable authorization.

The validator MUST check:

- Authorized operation type
- Authorized scope
- Grant identity
- Issuance time
- Expiration time, when applicable
- Revocation state
- Applicable external policy references

An expired or revoked grant MUST NOT
authorize subsequent operations.

A grant covering repair MUST NOT
implicitly authorize release.

A later grant MUST NOT silently erase
an earlier safety hold.

## 9. Hold Handling

An active safety hold blocks a release.

A lineage with an unresolved hold MUST
NOT pass the release recovery gate.

Version 0.3 introduces the logical event:

hold_resolved

A hold resolution MUST reference:

- The original hold identity
- The resolving external authority
- An explicit resolution decision
- Supporting resolution evidence
- The effective resolution timestamp

A hold MUST NOT be considered resolved
only because a new authorization exists.

The hold_resolved event is defined by
the v0.3 extension profile and MUST NOT
be inserted into a v0.2 record using
an unmodified v0.2 schema.

## 10. Independent Verification

A verification event MUST be linked
to the relevant repair operation.

The validator MUST identify the
repairing agent from the source history.

The verifier identity MUST differ from
the repairing agent identity.

A verification decision MUST have
supporting evidence bindings.

A distinct identifier alone does not
prove organizational independence.

External identity and trust checks
remain necessary.

## 11. Evidence Binding

Each evidence binding MUST contain:

- evidence_id
- event_id
- operation_id
- target_id
- evidence_type
- evidence_reference

The evidence ID MUST be referenced by
the associated source record.

The referenced event and operation MUST
exist in the lineage.

The target MUST match the lineage target.

A verification evidence binding MUST be
associated with the relevant verification
event.

An evidence reference alone MUST NOT
be treated as proof of authenticity.

Cryptographic validation is outside
the initial v0.3 conformance profile.

## 12. Recovery Gate

The recovery gate evaluates whether
a recorded containment release satisfies
the protocol's prerequisites.

The gate MUST examine:

1. Valid lineage continuity.
2. Existing containment application.
3. Valid repair authorization.
4. Recorded repair completion.
5. Successful independent verification.
6. Matching verification evidence.
7. Explicit release approval.
8. Valid release authorization.
9. No unresolved safety hold.
10. No blocking revocation or expiry.

The gate result MUST be one of:

- allowed
- denied
- indeterminate

An allowed result requires all mandatory
conditions to be established.

A denied result indicates a known violation.

An indeterminate result indicates missing
or insufficient information.

Indeterminate MUST NOT grant release
permission.

## 13. Decision Semantics

The recovery gate MUST report:

- decision
- evaluated_at
- evaluated_event_id
- satisfied_conditions
- blocking_conditions
- evidence_references

A gate evaluation MUST be tied to an
explicit historical cutoff.

Records occurring after the cutoff
MUST NOT be used to justify the earlier
release decision.

The gate is an assessment of the recorded
conditions, not an actuator.

Even an allowed decision MUST NOT by
itself trigger a production release.

## 14. Source and Event Validation

For each linked record, the validator MUST:

1. Resolve the referenced source.
2. Validate the source against its
   declared version schema.
3. Verify identifiers and metadata.
4. Validate event-specific requirements.
5. Evaluate causal dependencies.
6. Check authorization boundaries.
7. Check evidence references.
8. Reconcile the resulting lifecycle state.

The validator MUST NOT trust a
precomputed gate decision without
re-evaluating the supporting records.

## 15. Conformance

A conforming MARP v0.3 validator MUST reject:

- Missing predecessor
- Circular event references
- Duplicate event IDs
- Cross-target lineage references
- Inconsistent state continuity
- Verification before repair completion
- Self-verification of a repair
- Release without prior approval
- Release under an unresolved hold
- Invalid evidence binding
- Authorization reuse after revocation
- Authorization use after expiration

A valid but incomplete history MAY
produce an indeterminate recovery gate
decision rather than a malformed-record
error.

## 16. Non-Goals

MARP v0.3 does not define:

- Automatic AI model modification
- Autonomous privilege escalation
- Production repair execution
- Cryptographic signature infrastructure
- Distributed consensus
- Global event ordering
- Multi-target transaction atomicity
- Automatic rollback
- Cross-network settlement
- Autonomous containment release

## 17. Security Considerations

A syntactically correct event history
is not proof that the recorded events
occurred in the real world.

A conforming implementation MUST distinguish:

- Structural validity
- Referential integrity
- Historical consistency
- External evidence authenticity
- Runtime enforcement

MARP v0.3 primarily addresses the first
three layers.

Trusted evidence and actual runtime
enforcement require external systems.

## 18. Future Extensions

Potential future versions may introduce:

- Branching repair histories
- Cross-agent repair coordination
- Signed event chains
- Rollback and compensation records
- Federated verification
- Distributed maintenance scheduling
- Multi-target recovery bundles

## 19. Design Statement

Repair locally.
Hold safely.
Verify independently.
Trace causally.
Release explicitly.
