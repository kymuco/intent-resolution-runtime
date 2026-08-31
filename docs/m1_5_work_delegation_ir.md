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

Core invariants:

```text
work description != execution
work description != authorization
WorkStep lineage includes parent WorkPlan ref
step completion != plan completion
plan completion != intent satisfaction by default
```

Part A deliberately does **not** introduce `DelegatedWork`, `WorkerResult`, Capability/Governance references, execution handoffs, Observation/Outcome, retry/recovery, transport, persistence, or arbitrary plan control flow. Those remain later sub-slices/milestones.

## 1. WorkPlan

```text
WorkPlan
├─ schema = irr.work_plan.v1
├─ resolved_intent_identity
├─ plan_ref
├─ steps[]
├─ completion_contract
└─ description
```

`resolved_intent_identity` binds the plan to the exact admitted `ResolvedIntent` lineage.

`plan_ref` is an opaque Host-supplied `StableRef`. Its namespace does not confer trust, capability, authority, persistence, or executor ownership.

A WorkPlan MUST contain at least one WorkStep. Every contained WorkStep MUST carry the same exact `plan_ref` as its `work_plan_ref` and the same exact `resolved_intent_identity`.

This keeps a serialized standalone WorkStep attributable to its semantic parent plan reference rather than allowing the same step identity to be silently transplanted between differently referenced plans.

```text
ResolvedIntent != WorkPlan requirement
WorkStep parent plan lineage != inferred containment only
plan_ref != plan authentication
valid WorkPlan != executable WorkPlan
valid WorkPlan != authorized WorkPlan
```

The complete WorkPlan content still determines its own canonical record identity. Reusing a Host-supplied `plan_ref` does not make two different WorkPlan records identical.

`completion_contract` is a required non-empty semantic statement of the bounded completion meaning for the **operational plan as a whole**. It is distinct from every child WorkStep completion contract and from satisfaction of the parent intent.

```text
step completion != plan completion
all steps completed != plan completion proof by default
plan completion != parent intent satisfaction by default
```

M1.5 only preserves that semantic distinction. M1.7 owns Attempt / Outcome / Continuation evidence and later runtime determination of whether a completion contract has actually been met.

M1.5 Part A does not manufacture a WorkPlan for non-operational resolution paths. It only defines the work representation once operational work has already been admitted by the upstream resolution boundary.

## 2. WorkStep

```text
WorkStep
├─ schema = irr.work_step.v1
├─ resolved_intent_identity
├─ work_plan_ref
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

`work_plan_ref` preserves explicit derivation from the parent WorkPlan reference. `step_ref` identifies the step inside that plan. Neither reference is authority or proof that a Host-supplied association is authentic.

```text
WorkStep != free-floating executable task
work_plan_ref != Authorization
step_ref != execution handle
```

## 3. Semantic operation identifier

`operation` names **what** operation is requested. It is not shell syntax, source code, a URL to execute, a tool invocation, or a Capability identifier.

M1.5 v1 freezes only a narrow cross-language identifier syntax, not a universal operation vocabulary:

```text
segment.segment[.segment...]
segment := [a-z][a-z0-9_]*
```

Examples:

```text
filesystem.search
artifact.inspect
archive.extract
workspace.inspect
```

Therefore command-shaped strings such as `rm -rf /`, `powershell -Command ...`, URLs, single undotted words, whitespace-bearing strings, and arbitrary source snippets are not valid `operation` identifiers.

The vocabulary remains open to later domain contracts; syntactic validity alone does not establish semantic boundedness or Capability compatibility.

```text
semantic operation != implementation command
operation syntax validity != semantic admission
operation token != Capability Match
operation token != authority
```

IRR admission must still reject a syntactically valid identifier whose admitted meaning is actually an open-ended autonomous lifecycle.

## 4. Explicit scope

`scope` records the bounded semantic surface of the step as admitted at planning time.

M1.5 does not interpret path containment, account ownership, resource reachability, disclosure permission, or authority from the scope string.

```text
scope != permission
scope != verified resource ownership
scope != capability availability
```

Concrete Capability and Governance compatibility belong to M1.6.

## 5. Step completion contract

Every WorkStep carries a non-empty `completion_contract` describing the bounded semantic condition that would make that **step** complete.

It is data for later lifecycle/evaluation boundaries; it is not executable code or a hidden predicate language.

```text
step completion contract != loop condition
step completion contract != executor code
step completion contract != proof of completion
```

The field exists because an ordinary WorkStep must not mean only:

```text
keep working until the goal is achieved
```

without an inspectable bounded completion meaning.

The WorkPlan's separate completion contract prevents child step completion from silently becoming plan completion semantics.

## 6. Literal input

```text
WorkLiteralInput
├─ schema = irr.work_literal_input.v1
├─ name
├─ semantic_type
└─ value
```

A literal input is caller/admission-supplied semantic string data already represented at planning time.

`value` may be any Unicode-scalar string, including the empty string or whitespace-only text, because emptiness can itself be material input data. This is distinct from identifiers, scope, descriptions, and completion contracts, which have stronger non-empty requirements.

Executable-looking literal text remains data.

```text
"rm -rf /" as literal value != WorkPlan control flow
"powershell ..." as literal value != automatic execution
source code text != authority
URL text != retrieval authority
```

M1.5 does not parse, interpolate, evaluate, execute, or lower literal input values into commands.

## 7. Symbolic input

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

A symbolic input may be produced by another WorkStep in the same WorkPlan or supplied/bound outside that plan under the already frozen M1.4 Binding boundary. M1.5 does not duplicate or weaken BindingRule semantics.

## 8. WorkOutput

```text
WorkOutput
├─ schema = irr.work_output.v1
├─ name
└─ reference -> SymbolicReference
```

A WorkOutput declares the semantic slot expected from one WorkStep. The SymbolicReference MUST belong to the same ResolvedIntent identity. Within one WorkPlan, one symbolic output slot has exactly one producer.

```text
same output slot + two producers != implicit merge
```

M1.5 v1 does not invent value merging, conflict resolution, or hidden precedence.

## 9. Symbol semantics are stable inside one plan

If the same `slot_ref` appears multiple times in a WorkPlan, every occurrence MUST carry the same complete `SymbolicReference` identity.

```text
same slot_ref + different semantic_type != same symbol
same slot_ref + different selection_scope != same symbol
same slot_ref + different ResolvedIntent != same symbol
```

The WorkPlan rejects conflicting symbolic meaning instead of selecting one definition by presentation order.

## 10. Finite dependency DAG

`depends_on` is an explicit tuple of WorkStep refs. Every dependency MUST refer to another WorkStep inside the same WorkPlan. The graph MUST be finite and acyclic.

```text
dependency != arbitrary branch
dependency != retry
dependency != exception handler
dependency != loop
```

Acyclicity is validated with an iterative graph algorithm; valid finite plans therefore do not acquire a CPython recursion-depth ceiling merely because a dependency chain is long.

The input tuple order of WorkSteps is not semantic plan ordering. WorkPlan canonicalizes steps by `step_ref`.

```text
presentation order != execution dependency
```

Independent WorkSteps therefore remain independent.

## 11. Internal symbolic dataflow follows dependency order

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

A transitive dependency is sufficient; a redundant direct edge is not required. Reachability validation is iterative and does not use Python call-stack recursion as part of the IR semantic domain.

An external SymbolicReference that is not produced by the plan does not require an internal dependency. Its eventual value remains subject to M1.4 Binding semantics.

## 12. Explicit continuation mode

M1.5 Part A freezes only two continuation markers:

```text
none
return_to_irr
```

`return_to_irr` means the plan identifies a bounded point after which later attributable information/semantics must return to IRR before further **dependent** semantic work is admitted.

A `return_to_irr` WorkStep therefore MUST be terminal with respect to the WorkPlan dependency graph: no other WorkStep may depend on it. Independent work with no dependency path from that continuation step may coexist in the same finite plan because no semantic successor relation is asserted.

```text
return_to_irr -> no pre-admitted dependent successor
return_to_irr != embedded planner loop
return_to_irr != successor plan
return_to_irr != authorization request
```

Generic Continuation and successor lifecycle belong to M1.7.

## 13. No scripting language

The M1.5 v1 schema contains no representation for arbitrary loops, runtime `if` / `else`, exception handlers, hidden retries, eval / exec, embedded shell control flow, self-modifying plans, or arbitrary recursive WorkPlan generation.

A finite tuple plus DAG dependencies is the entire structural control surface of ordinary WorkPlan v1.

This structural restriction does not magically prove that an operation is semantically bounded.

```text
finite schema != permission to hide unbounded semantics in one token
```

Long-form subordinate autonomy belongs to the distinct M0.8 Worker delegation boundary and the later M1.5 Part B records.

## 14. WorkStep is not Worker delegation

Part A intentionally does not introduce a generic `worker.do_work` escape hatch.

```text
DelegatedWork != ordinary WorkStep
Worker != Executor by default
worker subplan != parent WorkPlan mutation
```

When long-form research, coding, analysis, or artifact production requires a Worker-owned subordinate lifecycle, M1.5 Part B will encode `DelegatedWork` explicitly instead of hiding it behind one WorkStep.

## 15. Authority boundary

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

M1.5 does not claim that a semantic operation has a matching Capability, is currently available, is invocation-ready, is authorized, or will succeed.

## 16. Canonical serialization and identity

All Work records use the existing M1 canonical JSON rules.

Identity remains:

```text
sha256(canonical_json_bytes(record))
```

Work inputs, outputs, dependencies, and plan steps are normalized into deterministic canonical order where their order is not itself semantic.

`WorkStep.identity` includes `work_plan_ref`, so changing the parent plan reference is a material identity change. `WorkPlan.identity` includes its plan completion contract and the complete canonicalized WorkStep records.

Material semantic changes therefore change identity while presentation-only tuple order does not.

Representative v1 identities are frozen by executable golden tests before Part A merge.

## 17. Closed public IR types

Public M1.5 records are immutable frozen slot dataclasses and are sealed from subclass extension through the public package surface. Unknown wire fields are rejected.

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

## 18. Explicit deferrals

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
- universal semantic-operation vocabulary;
- semantic boundedness inference from operation identifiers.

## 19. Acceptance

M1.5 Part A is correct when executable tests prove at least:

```text
WorkPlan and WorkStep are immutable and round-trippable
WorkPlan is bound to one ResolvedIntent identity
WorkPlan carries an explicit identity-covered plan completion contract
WorkStep carries and revalidates parent WorkPlan ref lineage
WorkStep symbolic inputs/outputs preserve the same ResolvedIntent lineage
WorkStep tuple presentation order does not create precedence
dependencies refer only to steps in the same plan
dependency graph is acyclic
large finite dependency chains do not depend on Python recursion depth
internal symbolic dataflow requires a producer dependency path
transitive producer dependency is sufficient
external symbolic input does not require an internal producer
same symbolic slot cannot carry conflicting semantics
same symbolic output slot cannot have multiple producers
return_to_irr has no dependent successor inside the same WorkPlan
independent work may coexist with a terminal return_to_irr step
operation is a lowercase dotted semantic identifier rather than command text
literal executable-looking text remains inert data
empty/whitespace literal string values remain representable data
step completion != plan completion remains representable
plan completion != intent satisfaction remains explicit
representative v1 canonical identities are frozen
unknown wire fields fail closed
public M1.5 records are closed against subclass state
no authority fields are introduced
```

## 20. Next M1.5 sub-slice

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
