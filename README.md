
# Mini-Agent Repair Protocol (MARP)

**A lightweight protocol for modular AI diagnosis, containment, repair, verification, and component replacement.**

**Version:** v0.1.0  
**Status:** Experimental Specification  
**License:** Apache-2.0

> Repair locally. Verify independently. Preserve the whole.

---

## 1. Overview

The Mini-Agent Repair Protocol (MARP) defines a
structured approach to maintaining AI systems through
small, modular, and replaceable repair agents.

Instead of modifying or replacing an entire AI system,
MARP focuses on bounded interventions at explicitly
authorized interfaces and components.

Mini-agents may diagnose abnormalities, contain
affected components, perform authorized repairs,
verify outcomes, or replace eligible components.

Every operation is represented by an auditable record.

MARP is model-agnostic and does not require
modification of foundation-model weights.

## 2. Design Philosophy

MARP is built around seven principles.

1. **External Operation**  
   Operate through explicitly authorized interfaces.

2. **Locality**  
   Restrict interventions to bounded components.

3. **Least Privilege**  
   Never allow mini-agents to grant themselves authority.

4. **Independent Verification**  
   Separate repair execution from verification.

5. **Replaceability**  
   Support controlled replacement of eligible components.

6. **Traceability**  
   Preserve records of operations, failures, and decisions.

7. **Safe Inaction**  
   Prevent state-changing actions when required
   authorization or evidence is unavailable.

## 3. Conceptual Architecture

```text
          AI System / Agent Network
                    |
                    v
            Observable Boundary
                    |
                    v
             Mini-Agent Layer
                    |
          +---------+---------+
          |         |         |
          v         v         v
       Diagnose   Contain   Repair
                              |
                              v
                            Verify
                              |
                              v
                            Replace
                    |
                    v
              Repair Record
                    |
                    v
           Conformance Validation
```

The diagram illustrates protocol capabilities,
not a mandatory execution sequence.

Each MARP v0.1 record represents one operation.

Multi-step workflow orchestration is reserved
for future versions.

## 4. Core Operations

MARP v0.1 defines five operation types.

| Operation | Purpose |
|---|---|
| `diagnose` | Observe a bounded target without modification |
| `contain` | Restrict an affected component or interface |
| `repair` | Restore an authorized component condition |
| `verify` | Evaluate operation evidence |
| `replace` | Substitute an eligible component |

Only `diagnose` is classified as non-state-changing
in the v0.1 record schema.

Other operations require explicit authorization
when they enter an active state.

## 5. Operation Lifecycle

MARP defines the following record statuses:

- `proposed`
- `authorized`
- `executed`
- `verified`
- `rejected`
- `failed`
- `held`

A state-changing operation MUST NOT enter an
active execution state without granted authorization.

A verified operation MUST contain a successful
verification decision and supporting evidence references.

An executed operation is not automatically verified.

A verified operation does not imply that the
entire AI system is safe.

## 6. Trust and Authorization Boundaries

MARP separates four responsibilities:

**Mini-Agent**

Performs a bounded operation.

**Target**

Identifies the affected component or interface.

**Authority Controller**

Provides external authorization for state-changing
operations.

**Independent Verifier**

Evaluates evidence without relying solely on the
repairing agent's own success claim.

The following conditions are prohibited:

- Self-authorization
- Self-verification of completed operations
- Intervention outside recorded permitted scope
- Unauthorized component replacement
- Execution under pending or denied authorization
- Verified completion without verification evidence

A record containing an authorization identifier
does not independently prove authorization authenticity.

Production systems must establish trust in the
external authority and evidence sources.

## 7. Repair Record

MARP v0.1 uses a JSON-based repair record.

The schema defines:

- Protocol version
- Record and operation identifiers
- Operation type and status
- Mini-agent identity and role
- Target identity and authorized scope
- Authorization metadata
- Verification metadata
- Evidence references
- Timestamp

Schema:

`schemas/repair-record.schema.json`

JSON Schema version:

Draft 2020-12

## 8. Repository Structure

```text
mini-agent-repair-protocol/
├── .github/
│   └── workflows/
│       └── validate.yml
├── schemas/
│   └── repair-record.schema.json
├── examples/
│   └── v0.1/
│       ├── pass/
│       │   ├── diagnose-observation.json
│       │   ├── authorized-local-containment.json
│       │   ├── independently-verified-repair.json
│       │   └── authorized-component-replacement.json
│       └── fail/
│           ├── missing-authorization.json
│           ├── self-authorization.json
│           ├── self-verification.json
│           ├── out-of-scope-intervention.json
│           ├── missing-verification-evidence.json
│           └── execution-while-held.json
├── scripts/
│   └── validate_examples.py
├── requirements.txt
├── SPEC.md
├── README.md
└── CHANGELOG.md
```

## 9. Conformance Testing

MARP uses three validation layers.

### Layer 1: Schema Validation

Validates JSON structure, required fields,
types, enumerations, and conditional constraints.

### Layer 2: Semantic Validation

Evaluates cross-field invariants, including:

- Operation-role consistency
- Self-authorization prohibition
- Self-verification prohibition
- Exact scope matching
- Operation authorization
- Component replaceability
- Verification evidence consistency

### Layer 3: Expectation Matching

Compares the actual validation result with the
test fixture's expected result.

Fixtures contain an `expected_result` field.

This field is removed before validating the
production repair record.

A correctly rejected FAIL fixture counts as
a successful conformance test.

## 10. Validation

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the validator:

```bash
python scripts/validate_examples.py
```

Expected summary:

```text
=== MARP v0.1 Summary ===
Total examples : 10
Matched        : 10
Mismatched     : 0
[PASS] All MARP v0.1 expectations matched
```

MARP v0.1 includes:

| Test Category | Count |
|---|---:|
| Expected PASS | 4 |
| Expected FAIL | 6 |
| Total | 10 |

## 11. GitHub Actions

The repository includes automated conformance
validation at:

`.github/workflows/validate.yml`

The workflow runs on:

- Push
- Pull request
- Manual workflow dispatch

The validator is tested using Python 3.10
and Python 3.12.

A successful workflow indicates that the
configured examples match their expected outcomes.

It does not demonstrate production repair
effectiveness or establish system-wide safety.

## 12. Security Considerations

MARP v0.1 enforces record-level invariants.

It does not provide:

- Cryptographic authorization verification
- Evidence authenticity verification
- Secure execution sandboxing
- Runtime containment enforcement
- Distributed consensus
- Automatic rollback
- Production deployment authorization

Implementations MUST NOT treat a passing
conformance test as permission to execute
operations against production systems.

External enforcement mechanisms remain necessary.

## 13. Interoperability

MARP is designed to remain independent of
specific AI providers and model architectures.

Potential integration areas include:

- Trace and provenance systems
- External authorization controllers
- AI safety protocols
- Distributed AI immune networks
- Recovery and containment systems

Possible companion architectures include:

- TACP (Angel-Devil Coordination Protocol)
- Resilient AI Safety Principles
- SAIN (AI Immune Network)
- Kazene-based orchestration systems

These are conceptual integration targets.

MARP v0.1 does not claim verified interoperability
with these systems.

External integrations MUST NOT implicitly
expand a mini-agent's authority.

## 14. Version Scope

### v0.1 — Foundation

Defines:

- Five core operations
- Repair record schema
- Authorization boundaries
- Independent verification rules
- Basic semantic conformance
- Positive and negative test fixtures
- Automated GitHub Actions validation

### Future Extensions

Potential future work includes:

- Richer lifecycle transitions
- Authorization revocation and expiry
- Explicit containment state
- Multi-step repair workflows
- Replacement lineage
- Rollback and recovery records
- Federated mini-agent coordination
- Signed evidence and authorization references

These features are not normative in v0.1.

## 15. Project Scope

MARP is a protocol specification and
conformance-testing project.

It does not provide an autonomous production
repair agent or modify any AI model.

The purpose is to establish a reusable,
auditable, and testable structure for
bounded AI maintenance operations.

## 16. Guiding Statement

> A capable repair agent is not necessarily
> an authorized repair agent.
>
> An executed repair is not necessarily
> a verified repair.
>
> A verified repair is not necessarily
> proof of system-wide safety.

**Repair locally. Verify independently. Preserve the whole.**

## 17. License

Apache License 2.0.

See `LICENSE` for the complete license text.
