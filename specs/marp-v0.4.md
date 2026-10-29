# Mini-Agent Repair Protocol (MARP) v0.4

Version: 0.4.0
Status: Draft
Title: Distributed Repair Coordination and Conflict Control
Extends: MARP v0.1, v0.2, v0.3

## 1. Purpose

MARP v0.4 defines a bounded coordination
protocol for multiple specialized mini-agents
participating in the same repair operation.

It provides:

- Explicit task dependencies
- Scoped agent assignments
- Conflict detection
- Bounded concurrency
- Independent verification
- Controlled result reconciliation
- Safe suspension of unresolved work

MARP v0.4 does not grant agents autonomous
authority to expand repair scope or release
containment.

## 2. Design Principles

### 2.1 External Authority

All state-changing operations MUST be
authorized by an external authority.

The coordinator MUST NOT manufacture
authorization.

### 2.2 Locality

Each agent MUST act only within its
authorized target and resource scope.

### 2.3 Separation of Duties

Repair execution and independent verification
MUST remain distinct.

An agent MUST NOT be the sole independent
verifier of its own repair.

### 2.4 Explicit Dependencies

Every task dependency MUST reference an
existing task in the same coordination plan.

### 2.5 Conflict Before Execution

Conflicting state-changing tasks MUST NOT
execute concurrently unless an external,
explicitly authorized conflict-resolution
policy permits the specific combination.

### 2.6 Fail Closed

Unknown dependencies, unresolved conflicts,
expired grants, or invalid evidence MUST
block affected work.

### 2.7 No Implicit Recovery

Coordination completion MUST NOT imply
containment release.

Release remains subject to the MARP v0.3
recovery conditions and external approval.

## 3. Scope

The initial v0.4 profile supports:

- One coordination plan
- One primary recovery target
- Multiple specialized mini-agents
- A bounded set of local tasks
- Directed acyclic task dependencies
- Explicit resource access declarations
- A single reconciliation decision

Cross-target repair transactions and
distributed consensus are out of scope.

## 4. Coordination Plan

A coordination plan MUST contain:

- schema_version
- coordination_id
- target_id
- lineage_id
- policy_id
- authority
- agents
- tasks
- conflicts
- reconciliation
- evaluated_at

A coordination plan MUST reference the
relevant v0.3 repair lineage.

A valid coordination plan is not itself
evidence that the referenced repair occurred.

## 5. Agent Assignment

Each participating agent MUST have:

- agent_id
- role
- authorized_operations
- authorized_scopes
- assignment_status

Supported roles:

- diagnostic
- containment
- repair
- verification
- reconciliation

Assignment status:

- active
- held
- completed
- revoked

The agent assignment MUST NOT grant any
permission beyond the external authority.

The coordinator MUST check effective
authorization before task execution.

## 6. Repair Tasks

Each task MUST declare:

- task_id
- assigned_agent_id
- operation
- target_id
- resource_scope
- access_mode
- depends_on
- status
- authorization_id
- evidence_ids

Supported access modes:

- read
- write
- exclusive

Supported task statuses:

- pending
- ready
- running
- held
- completed
- failed
- cancelled

A completed task MUST have evidence.

Task completion MUST NOT automatically
mark dependent tasks as verified.

## 7. Dependency Graph

The task dependency graph MUST be acyclic.

Every dependency MUST reference a task
within the same coordination plan.

A task MUST NOT start until all required
predecessor tasks have successfully
completed.

An unresolved or failed predecessor MUST
block dependent tasks.

Dependency cycles MUST cause validation
failure.

## 8. Conflict Detection

Potential conflicts include:

- Concurrent writes to the same resource
- Read/write interference where consistent
  reads are required
- Exclusive access overlap
- Incompatible repair operations
- Containment and release overlap
- Conflicting authority scopes

The validator MUST evaluate conflicts
from the declared task resource scopes.

Overlapping writes MUST NOT be assumed safe
merely because the tasks belong to
different agents.

## 9. Conflict Handling

A detected conflict MUST have an explicit
disposition:

- blocked
- serialized
- externally_resolved

Blocked conflicts MUST prevent the affected
tasks from running concurrently.

Serialized conflicts MUST establish a
deterministic execution order.

Externally resolved conflicts MUST identify:

- The external resolving authority
- The applicable authorization
- The resolution policy
- Supporting evidence
- The affected tasks and resources

A conflict disposition MUST NOT override
a revoked or expired authorization.

## 10. Bounded Concurrency

The coordination plan MUST declare
a maximum concurrency budget.

The coordinator MUST NOT dispatch more
simultaneously running tasks than the
authorized budget.

A concurrency limit does not replace
resource conflict checking.

A task can be within the concurrency
budget and still be unsafe to run.

## 11. Independent Verification

Verification tasks MUST:

- Reference completed repair work
- Use a distinct verifying agent
- Identify verification evidence
- Preserve the repair lineage reference

A successful verification task MUST NOT
be inferred solely from a completed
repair task.

A verifier MUST NOT rewrite the repair
evidence it is responsible for verifying.

## 12. Reconciliation

A reconciliation record MUST contain:

- reconciliation_id
- coordination_id
- considered_task_ids
- verified_task_ids
- unresolved_task_ids
- conflict_ids
- decision
- evidence_ids
- evaluated_at

Decisions:

- accepted
- held
- rejected
- indeterminate

An accepted decision requires:

1. All required tasks completed.
2. Required independent verification passed.
3. No unresolved blocking conflicts.
4. No active unauthorized execution.
5. All mandatory evidence references resolve.
6. All required authority checks succeed.

A held decision preserves safe suspension
without treating unfinished repair as failure.

Rejected means a known safety or integrity
requirement has been violated.

Indeterminate means evidence is insufficient
to establish a final decision.

Neither held nor indeterminate authorizes
containment release.

## 13. Relationship to v0.3

MARP v0.4 coordination MUST preserve
the v0.3 lineage and recovery boundaries.

Each relevant task MUST be traceable to:

- A repair operation
- A responsible agent
- An authorization
- Supporting evidence
- A relevant lineage event or extension

An accepted coordination reconciliation
MUST NOT replace the v0.3 recovery gate.

The final release still requires explicit
external approval and valid authorization.

## 14. Revocation and Suspension

If an applicable authorization is revoked
or expires:

- Affected running work MUST be suspended.
- Dependent work MUST NOT be dispatched.
- Existing containment MUST be preserved.
- The event MUST be recorded.
- Resumption MUST require valid authorization.

Revocation MUST NOT silently erase
previously valid historical events.

## 15. Evidence and Trust

Evidence references MUST be scoped to
the corresponding task and target.

The validator MUST reject evidence that
is bound to a different operation or target.

Synthetic fixtures MAY use local logical
evidence references.

Real deployments MUST establish trusted
evidence resolution independently.

Generated test data MUST NOT be presented
as independent proof of actual execution.

## 16. Validation Requirements

A conforming v0.4 validator MUST detect:

- Duplicate task IDs
- Unknown dependencies
- Dependency cycles
- Unassigned tasks
- Unauthorized assignments
- Out-of-scope operations
- Unresolved write conflicts
- Unsafe overlapping execution
- Concurrency budget violations
- Self-verification
- Missing reconciliation evidence
- Reconciliation with active blockers
- Revoked authorization reuse
- Invalid lineage references

The validator MUST compare the claimed
reconciliation outcome with its own
computed decision.

## 17. Security Boundaries

MARP v0.4 MUST NOT:

- Automatically elevate agent privileges
- Use reconciliation as an authorization
- Allow a coordinator to self-authorize
- Permit unverified repair release
- Treat missing conflict information as safe
- Let a failed task silently disappear
- Replace human or external review where
  such review is required

## 18. Non-Goals

MARP v0.4 does not define:

- Autonomous model self-modification
- Distributed consensus
- Unbounded agent spawning
- Cross-organization control
- Automatic production deployment
- Automatic containment release
- Cryptographic identity issuance
- Multi-target atomic transactions

## 19. Future Extensions

Potential later versions may support:

- Signed cross-agent receipts
- Repair rollback and compensation
- Federated repair coordination
- Distributed task scheduling
- Adaptive resource budgets
- Multi-target recovery transactions
- Long-running repair orchestration

## 20. Design Statement

Repair locally.
Coordinate explicitly.
Contain conflicts.
Verify independently.
Reconcile safely.
Release only with authority.
