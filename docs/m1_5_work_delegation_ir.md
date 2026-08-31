# M1.5 — Work / Delegation IR

Status: **implementation slice — Part A: bounded WorkPlan / WorkStep core**.

M1.5 encodes the frozen M0.3 Intent → Work boundary and, in its later Part B, the M0.8 Worker Delegation boundary as immutable, inspectable Python contracts.

This first M1.5 slice answers one implementation question:

> How can an admitted `ResolvedIntent` describe finite operational work without becoming executable code, a hidden planner loop, a Worker delegation, or an authority grant?

The answer is an immutable semantic `WorkPlan` containing a finite acyclic set of bounded `WorkStep` records.

```text
ResolvedIntent identity
        |
        v
     WorkPlan
        |
        +------------------------+
        |                        |
        v                        v
    WorkStep                 WorkStep
 bounded semantic          bounded semantic
   operation                 operation
        |                        |
        +---- finite DAG --------+
                 |
                 v
       downstream boundaries
       (later M1.6 / M1.7)
```

Core invariant:

```text
work description != execution
work description != authorization
```

Part A deliberately does **not** introduce `DelegatedWork`, `WorkerResult`, Capability/Governance references, execution handoffs, Observation/Outcome, retry/recovery, transport, persistence, or arbitrary plan control flow. Those remain later sub-slices/milestones.

## 1. WorkPlan

```text
WorkPlan
├─ schema = irr.work_plan.v1
├─ resolved_intent_identity
├─ plan_ref
├─ steps[]
└─ description
```

`resolved_intent_identity` binds the plan to the exact admitted `ResolvedIntent` lineage.

`plan_ref` is an opaque Host-supplied `StableRef`. Its namespace does not confer trust, capability, authority, persistence, or executor ownership.

A WorkPlan MUST contain at least one WorkStep.

```text
ResolvedIntent != WorkPlan requirement
valid WorkPlan != executable WorkPlan
valid WorkPlan != authorized WorkPlan
```

M1.5 Part A does not manufacture a WorkPlan for non-operational resolution paths. It only defines the work representation once operational work has already been admitted by the upstream resolution boundary.

## 2. WorkStep

```text
WorkStep
├─ schema = irr.work_step.v1
├─ resolved_intent_identity
├─ step_ref
├─ operation
├─ scope
├─ inputs[]
├─ outputs[]
├─ depends_on[]
├─ continuation
├─ completion_contract
└─ description
```

A WorkStep is one bounded semantic unit of requested work.

`operation` is an opaque semantic operation token. It names **what** operation is requested; it is not shell syntax, source code, a URL to execute, a tool invocation, or a capability identifier.

Conceptual examples remain:

```text
filesystem.search
artifact.inspect
archive.extract
workspace.inspect
```

The exact operation vocabulary remains open to later domain contracts. M1.5 v1 does not ship a universal operation catalog.

```text
semantic operation != implementation command
operation token != capability match
operation token != authority
```

## 3. Explicit scope

`scope` records the bounded semantic surface of the step as admitted at planning time.

M1.5 does not interpret path containment, account ownership, resource reachability, disclosure permission, or authority from the scope string.

```text
scope != permission
scope != verified resource ownership
scope != capability availability
```

Concrete capability and Governance compatibility belong to M1.6.

## 4. Explicit completion contract

Every WorkStep carries a non-empty `completion_contract`.

The completion contract states the bounded semantic condition that would make this planned unit complete. It is data for later lifecycle/evaluation boundaries; it is not executable code or a hidden predicate language.

```text
completion contract != loop condition
completion contract != executor code
completion contract != proof of completion
```

M1.7 owns Attempt / Outcome / Continuation semantics and therefore owns later runtime treatment of actual completion evidence.

The explicit field exists in M1.5 because an ordinary WorkStep must not mean only:

```text
keep working until the goal is achieved
```

without an inspectable bounded completion meaning.

## 5. Literal input

```text
WorkLiteralInput
├─ schema = irr.work_literal_input.v1
├─ name
├─ semantic_type
└─ value
```

A literal input is caller/admission-supplied semantic data already represented at planning time.

Executable-looking text remains data.

```text
"rm -rf /" != WorkPlan control flow
"powershell ..." != automatic execution
source code text != authority
URL text != retrieval authority
```

M1.5 does not parse, interpolate, evaluate, execute, or lower literal input values into commands.

## 6. Symbolic input

```text
WorkSymbolicInput
├─ schema = irr.work_symbolic_input.v1
├─ name
└─ reference -> SymbolicReference
```

A symbolic WorkStep input reuses the exact M1.4 `SymbolicReference` contract.

The reference MUST belong to the same `ResolvedIntent` identity as the WorkStep.

```text
symbolic input != known value
symbolic input != ambient retrieval
symbolic input != Observation by default
symbolic input != authority
```

A symbolic input may be:

- produced by another WorkStep in the same WorkPlan; or
- supplied/bound outside that plan under the already frozen M1.4 Binding boundary.

M1.5 does not duplicate or weaken BindingRule semantics.

## 7. WorkOutput

```text
WorkOutput
├─ schema = irr.work_output.v1
├─ name
└─ reference -> SymbolicReference
```

A WorkOutput declares the semantic slot expected from one WorkStep.

The SymbolicReference MUST belong to the same ResolvedIntent identity.

Within one WorkPlan, one symbolic output slot has exactly one producer.

```text
same output slot + two producers != implicit merge
```

M1.5 v1 does not invent value merging, conflict resolution, or hidden precedence.

## 8. Symbol semantics are stable inside one plan

If the same `slot_ref` appears multiple times in a WorkPlan, every occurrence MUST carry the same complete `SymbolicReference` identity.

Therefore:

```text
same slot_ref + different semantic_type != same symbol
same slot_ref + different selection_scope != same symbol
same slot_ref + different ResolvedIntent != same symbol
```

The WorkPlan rejects conflicting symbolic meaning instead of selecting one definition by presentation order.

## 9. Finite dependency DAG

`depends_on` is an explicit tuple of WorkStep refs.

Every dependency MUST refer to another WorkStep inside the same WorkPlan.

The graph MUST be finite and acyclic.

```text
dependency != arbitrary branch
dependency != retry
dependency != exception handler
dependency != loop
```

Acyclicity is validated structurally.

The input tuple order of WorkSteps is not semantic plan ordering. WorkPlan canonicalizes steps by `step_ref`.

```text
presentation order != execution dependency
```

Independent WorkSteps therefore remain independent.

## 10. Internal symbolic dataflow follows dependency order

If a `WorkSymbolicInput` references a symbolic slot produced by another WorkStep in the same plan, the consuming WorkStep MUST transitively depend on that producer.

```text
producer
   |
   v
dependency path
   |
   v
consumer
```

A transitive dependency is sufficient; a redundant direct edge is not required.

This prevents a WorkPlan from declaring internal dataflow while simultaneously claiming no semantic ordering relation between producer and consumer.

An external SymbolicReference that is not produced by the plan does not require an internal dependency. Its eventual value remains subject to M1.4 Binding semantics.

## 11. Explicit continuation mode

M1.5 Part A freezes only two continuation markers:

```text
none
return_to_irr
```

`return_to_irr` means the plan identifies a bounded point after which later attributable information/semantics must return to IRR before further semantic work is admitted.

It does not define the later Continuation record or branch logic.

```text
return_to_irr != embedded planner loop
return_to_irr != successor plan
return_to_irr != authorization request
```

Generic Continuation belongs to M1.7.

## 12. No scripting language

The M1.5 v1 schema contains no representation for:

- arbitrary loops;
- runtime `if` / `else`;
- exception handlers;
- hidden retries;
- eval / exec;
- embedded shell control flow;
- self-modifying plans;
- arbitrary recursive WorkPlan generation.

A finite tuple plus DAG dependencies is the entire structural control surface of ordinary WorkPlan v1.

This structural restriction does not magically prove that an opaque operation token is semantically bounded. IRR admission must still reject an operation whose real meaning is an open-ended autonomous lifecycle.

```text
finite schema != permission to hide unbounded semantics in one token
```

Long-form subordinate autonomy belongs to the distinct M0.8 Worker delegation boundary and the later M1.5 Part B records.

## 13. WorkStep is not Worker delegation

Part A intentionally does not introduce a generic `worker.do_work` escape hatch.

```text
DelegatedWork != ordinary WorkStep
Worker != Executor by default
worker subplan != parent WorkPlan mutation
```

When long-form research, coding, analysis, or artifact production requires a Worker-owned subordinate lifecycle, M1.5 Part B will encode `DelegatedWork` explicitly instead of hiding it behind one WorkStep.

## 14. Authority boundary

M1.5 Part A contains no authority field.

```text
WorkPlan != Authorization
WorkStep != Authorization
scope != Authorization
literal input != Authorization
symbolic input != Authorization
completion contract != Authorization
return_to_irr != Authorization
```

M1.6 owns Capability / Governance references.

M1.5 does not claim that a semantic operation:

- has a matching Capability;
- is currently available;
- is invocation-ready;
- is authorized;
- will succeed.

## 15. Canonical serialization and identity

All Work records use the existing M1 canonical JSON rules.

Identity remains:

```text
sha256(canonical_json_bytes(record))
```

Work inputs, outputs, dependencies, and plan steps are normalized into deterministic canonical order where their order is not itself semantic.

Material semantic changes therefore change identity while presentation-only tuple order does not.

## 16. Closed public IR types

Public M1.5 records are immutable frozen slot dataclasses and are sealed from subclass extension through the public package surface.

Unknown wire fields are rejected.

A producer therefore cannot smuggle fields such as:

```text
approved
authorized
safe
permission_granted
retry_until_success
shell_command
```

into a v1 WorkPlan/WorkStep record.

## 17. Explicit deferrals

M1.5 Part A does not freeze:

- DelegatedWork / DelegatedWorkHandoff;
- WorkerResult / Worker escalation;
- worker context-surface schemas;
- worker capability ceilings or forbidden-effect schemas;
- capability catalog / capability match;
- WorkProposal / Governance / Authorization;
- executable CapabilityHandoff;
- Attempt / Outcome / generic Continuation;
- successor-plan lifecycle;
- retry / fallback / compensation;
- Observation schemas;
- executor scheduling;
- transport / persistence;
- generic typed numeric/boolean/null Work inputs;
- operation-specific parameter schemas;
- semantic boundedness inference from operation text.

## 18. Acceptance

M1.5 Part A is correct when executable tests prove at least:

```text
WorkPlan and WorkStep are immutable and round-trippable
WorkPlan is bound to one ResolvedIntent identity
WorkStep symbolic inputs/outputs preserve the same ResolvedIntent lineage
WorkStep tuple presentation order does not create precedence
dependencies refer only to steps in the same plan
dependency graph is acyclic
internal symbolic dataflow requires a producer dependency path
transitive producer dependency is sufficient
external symbolic input does not require an internal producer
same symbolic slot cannot carry conflicting semantics
same symbolic output slot cannot have multiple producers
literal executable-looking text remains inert data
explicit return_to_irr continuation is representable
unknown wire fields fail closed
public M1.5 records are closed against subclass state
no authority fields are introduced
```

## 19. Next M1.5 sub-slice

Part B will encode the M0.8 Worker Delegation boundary separately.

The next records should preserve at least:

```text
DelegatedWork
explicit objective
delegated scope
bounded context surface
allowed capability ceiling
forbidden effects
expected deliverables
completion contract
material constraints
parent intent/work lineage

DelegatedWork != ordinary WorkStep
DelegatedWork != Authorization
WorkerResult != parent completion
```

The Part B design must not reuse WorkStep as an opaque Worker escape hatch.
