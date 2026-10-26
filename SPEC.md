
# Mini-Agent Repair Protocol (MARP) v0.1

Status: Draft  
Version: 0.1.0

## 1. Purpose

MARP defines a lightweight, interoperable protocol for
diagnosing, containing, proposing repairs, independently
verifying, and replacing components in AI systems through
modular, least-privilege mini-agents.

MARP does not require modification of foundation-model
weights or internal architecture.

## 2. Core Principles

### 2.1 External Operation
Mini-agents operate through explicitly authorized
interfaces and observable system boundaries.

### 2.2 Locality
Interventions MUST be limited to the smallest
reasonably identifiable affected scope.

### 2.3 Least Privilege
Mini-agents MUST NOT acquire, delegate, or expand
their own authority.

### 2.4 Independent Verification
A repair MUST NOT be considered verified solely
because the repairing agent claims success.

### 2.5 Replaceability
Mini-agents and eligible target components SHOULD
support controlled replacement without requiring
replacement of the whole AI system.

### 2.6 Traceability
Every attempted operation MUST produce an auditable
record, including rejected or unsuccessful attempts.

### 2.7 Safe Inaction
When necessary authority or safety evidence is absent,
the mini-agent MUST NOT perform a state-changing action.

## 3. Roles

### Target
The bounded component, service, or interface under
inspection or repair.

### Mini-Agent
An independently identifiable agent assigned to
perform a specific authorized operation.

### Authority Controller
An external authority responsible for authorizing
state-changing operations.

### Independent Verifier
A separate verification identity that evaluates the
outcome without relying solely on the repairer's claim.

## 4. Operation Types

MARP v0.1 defines five operations:

- diagnose
- contain
- repair
- verify
- replace

Diagnosis is observational.

Containment restricts a specified component or interface.

Repair modifies an authorized target to restore an
expected condition.

Verification evaluates evidence of the reported outcome.

Replacement substitutes an authorized, replaceable
component.

A single record represents one operation. Multi-step
workflows require multiple linked records in future
versions.

## 5. Lifecycle

The following statuses are defined:

- proposed
- authorized
- executed
- verified
- rejected
- failed
- held

An operation MUST NOT be executed before applicable
authorization has been established.

Status `verified` is permitted only after an independent
verification decision.

Rejected, failed, and held operations MUST NOT be
represented as successful repairs.

A verified status does not imply that the entire
AI system is safe.

## 6. Authorization Requirements

Every operation MUST identify:

- operation_id
- mini_agent_id
- target_id
- operation_type
- status
- authority reference when state-changing
- evidence references
- timestamp

A state-changing operation MUST reference an explicitly
granted authorization covering its target and operation.

Absence of authorization MUST result in no execution.

Self-authorization MUST NOT be accepted.

## 7. Verification Requirements

For a successful state-changing operation:

- An independent verifier MUST be identified.
- The verifier MUST NOT have the same identity as the
  repairing mini-agent.
- A verification decision MUST be recorded.
- Supporting evidence MUST be referenced.

Verification MUST NOT silently expand the authorized
target scope.

## 8. Failure Handling

The following conditions MUST prevent successful
completion:

- missing authorization
- self-authorization
- out-of-scope intervention
- self-verification
- missing verification evidence
- unauthorized replacement
- execution while held or rejected

If verification fails, the affected operation MUST
remain unverified.

Rollback and recovery orchestration are outside the
normative scope of v0.1.

## 9. Security Boundaries

MARP MUST NOT interpret observations, model outputs,
or diagnostic recommendations as authority grants.

An agent MUST NOT change its own privilege level.

Untrusted diagnostic content MUST NOT be executed as
instructions.

No operation may bypass an external authority controller
merely because the agent identifies an emergency.

## 10. Interoperability

MARP MAY integrate with external systems providing:

- trace provenance
- authorization records
- containment records
- independent verification
- recovery coordination

Potential integrations include TACP, SAIN, and
other trace or safety protocols.

Such integrations are optional and MUST NOT create
implicit authorization.

## 11. Conformance

A MARP v0.1 implementation MUST:

1. Validate the required record structure.
2. Reject unauthorized state-changing operations.
3. Reject self-authorized execution.
4. Reject self-verified completion.
5. Enforce target scope boundaries.
6. Preserve records of failed and rejected operations.
7. Require independent verification evidence for
   verified state-changing operations.

Conformance testing MUST distinguish schema validation
from semantic validation.

## 12. Non-Goals

MARP v0.1 does not define:

- autonomous model-weight modification
- unlimited self-replication
- cross-domain privilege escalation
- automatic release from containment
- universal repair effectiveness
- autonomous production deployment
- distributed consensus
- financial settlement

## 13. Design Statement

Repair locally.
Verify independently.
Preserve the whole.
