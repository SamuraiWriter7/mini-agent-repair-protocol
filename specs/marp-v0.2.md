
# Mini-Agent Repair Protocol (MARP) v0.2

Version: 0.2.0
Status: Draft
Extension of: MARP v0.1

## 1. Purpose

MARP v0.2 extends the initial repair-record
protocol with explicit safety lifecycle controls.

The extension defines how repair operations
are held, how authorization expires or is
revoked, how containment states are recorded,
and how controlled release is permitted.

The primary objective is to prevent unsafe
execution or restoration when operational
authority or verification is insufficient.

## 2. Compatibility

MARP v0.2 preserves all normative safety
invariants introduced in v0.1.

The v0.1 repair-record schema remains unchanged.

Version 0.2 introduces a separate lifecycle
record linked to an existing repair operation.

A v0.1 record MUST NOT be interpreted as
containing lifecycle evidence that it does
not explicitly provide.

## 3. Core Principles

### 3.1 Explicit State

Safety states MUST be represented explicitly.

A system MUST NOT infer containment release
solely from successful repair execution.

### 3.2 Authority Continuity

State-changing actions MUST have valid external
authorization at the time of execution.

Authorization validity MUST be evaluated
against the applicable authority policy.

### 3.3 Fail-Closed Behavior

Unknown, expired, revoked, or insufficient
authorization MUST prevent further
state-changing operations.

### 3.4 Independent Release Verification

An affected component MUST NOT be released
from containment solely because the repairing
mini-agent reports successful repair.

### 3.5 No Self-Escalation

Mini-agents MUST NOT extend their own
authorization, lift their own restrictions,
or grant themselves release permission.

### 3.6 Trace Preservation

Every lifecycle transition MUST be recorded.

Rejected transitions MUST remain auditable.

## 4. Lifecycle Record

A MARP v0.2 lifecycle record MUST contain:

- schema_version
- lifecycle_id
- operation_id
- target_id
- actor_id
- event_type
- previous_state
- next_state
- authority
- verification
- evidence
- timestamp

The lifecycle record references an operation
defined by MARP v0.1 or a compatible version.

## 5. Lifecycle States

MARP v0.2 defines the following states:

- observed
- authorized
- held
- contained
- repairing
- verification_pending
- verified
- released
- failed

Lifecycle states are separate from the
operation statuses defined in v0.1.

They MUST NOT be treated as interchangeable.

## 6. Lifecycle Events

The following event types are defined:

- authorization_granted
- authorization_revoked
- authorization_expired
- operation_held
- containment_applied
- repair_started
- repair_completed
- verification_passed
- verification_failed
- release_approved
- containment_released

Each event represents one requested or
completed lifecycle transition.

## 7. Hold

A hold restricts further state-changing
operations within its declared scope.

An active hold MUST NOT be bypassed by
the repairing mini-agent.

A hold MUST NOT automatically expire
unless an external policy explicitly
defines its expiration and release rules.

Authorization changes alone MUST NOT
silently clear a hold.

## 8. Authorization Revocation

Revocation invalidates the referenced
authorization for future actions.

A revoked authorization MUST NOT be used
to initiate or continue additional
state-changing operations.

Revocation MUST NOT be treated as
retroactive proof that earlier operations
were unauthorized.

Any subsequent action requires a valid
authorization under the applicable policy.

A lifecycle record MUST preserve the
authorization reference and revocation
event evidence.

## 9. Authorization Expiration

Authorization MAY contain an expiration time.

When an expiration time exists,
operations performed after expiration
MUST NOT be accepted under that grant.

An expired authorization MUST NOT be
automatically renewed.

A new authorization decision is required.

If expiration information cannot be
verified, the system MUST fail closed
for state-changing operations.

## 10. Containment

Containment restricts a specified component
or operational boundary.

Containment records MUST identify:

- Target
- Scope
- Authority reference
- Transition event
- Evidence reference

Containment MUST remain bounded to the
authorized scope.

An unrelated component MUST NOT be modified
solely because another component is contained.

## 11. Repair Under Containment

A component MAY remain contained while
an authorized repair is performed.

Repair execution MUST NOT implicitly
release containment.

A repair operation MUST remain within
its separately granted authorization.

Containment authority alone MUST NOT
grant unrestricted repair authority.

## 12. Independent Verification

Successful repair execution and successful
verification are separate events.

The verifier MUST have an identity distinct
from the repairing mini-agent.

A verification-passed event MUST reference
supporting verification evidence.

Failed or inconclusive verification MUST NOT
authorize release.

Verifier identity separation alone does not
establish cryptographic or organizational
independence.

## 13. Controlled Release

Containment release MUST require:

1. An existing containment record.
2. Successful independent verification.
3. Explicit external release authorization.
4. Valid release scope.
5. Supporting evidence references.
6. No unresolved active hold or blocking
   authorization condition.

Release authorization MUST be separate
from repair authorization.

A repair mini-agent MUST NOT authorize
its own release operation.

Release MUST NOT be inferred from a
verification-passed event alone.

## 14. Allowed Transitions

The baseline lifecycle model permits
the following transitions:

observed -> authorized
observed -> held
authorized -> held
authorized -> contained
contained -> repairing
contained -> held
repairing -> verification_pending
repairing -> held
repairing -> failed
verification_pending -> verified
verification_pending -> held
verification_pending -> failed
verified -> released

The transition from verified to released
requires an explicit containment_released
event with valid release authorization.

Hold recovery and reauthorization require
external review.

Additional recovery transitions are reserved
for future specification versions.

## 15. Invalid Transitions

The following transitions MUST be rejected:

- held -> repairing without review
- held -> released
- contained -> released without verification
- repairing -> released
- verification_pending -> released
- failed -> released
- observed -> released

A system MUST NOT invent intermediate
transitions to justify an invalid operation.

## 16. Evidence Requirements

Lifecycle records MUST preserve evidence
references for state-changing transitions.

Verification events MUST reference
independent verification evidence.

Release events MUST reference authorization
and verification evidence.

An evidence identifier alone does not prove
authenticity.

Production implementations require trusted
evidence validation mechanisms.

## 17. Conformance

A conforming MARP v0.2 validator MUST:

1. Validate lifecycle record structure.
2. Enforce permitted state transitions.
3. Reject unauthorized state changes.
4. Reject execution under unresolved holds.
5. Reject expired authorization use.
6. Reject revoked authorization use.
7. Reject premature containment release.
8. Reject self-authorized release.
9. Require independent verification evidence.
10. Preserve v0.1 compatibility.

Validation MAY use linked records and
external authority information.

A single event record alone is insufficient
to establish complete lifecycle history.

## 18. Security Limitations

MARP v0.2 does not implement:

- Runtime execution enforcement
- Cryptographic identity validation
- Trusted clock synchronization
- Distributed consensus
- Automatic rollback
- Production recovery orchestration
- Autonomous authorization renewal

Conformance validates declared records
against implemented protocol rules.

It does not establish production safety.

## 19. Future Extensions

Potential future versions may define:

- Explicit recovery from held states
- Multi-stage repair workflows
- Rollback authorization
- Replacement lineage
- Cross-agent repair coordination
- Federated repair evidence
- Signed lifecycle records

## 20. Design Statement

Repair locally.
Hold safely.
Verify independently.
Release explicitly.
