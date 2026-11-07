# G7A.1 — Dynamic candidate planning surface (read-only)

## Target

IRR must discover *planning affordances* from an exact current Host-projected
capability catalog, not from hard-coded Runplane effect names. Adding another
plugin may introduce a new operation and structural composition edge **without
changing planner code**. Discovery is not plugin trust or execution permission.

## Boundary

1. Trusted HDE Host captures Runplane G1 inventory/G2 provider bindings,
   establishes independently reviewed semantic mappings and effective policy,
   and produces a G3 `CandidateCapabilityCatalogSnapshot`.
2. Host supplies `HostPlanningVisibility` containing actor, exact candidate
   identity, policy revision and explicit visible capability refs. This typed
   object is **not** cryptographic Host authentication; callers must establish
   that evidence through their trusted channel before invoking IRR.
3. `build_candidate_planning_surface` validates exact candidate identity
   and permitted refs, exposes only those typed descriptors, and derives
   potential output/input semantic-type links.
4. `find_structural_plan_candidates` suggests bounded chains of available
   capabilities whose declared **input semantic types** can be supplied by
   available input types or preceding output types. No equivalence inference,
   implicit argument values, fabricated bindings or best-option claim.

## Explicitly NOT achieved

- No Runplane import, manifest validation, dynamic plugin installation,
  loading or `execute_effect` in IRR. These belong to Runplane and the Host.
- No actual WorkPlan is minted; the output is `CandidatePlanSketch` only.
  The existing original HUMAN/WorkStep → M33.3 catalog admission →
  mechanical match → Governance → Authorization → Attempt boundaries
  **remain mandatory** for any eventual execution.
- No scope feasibility, real data identity, downstream symbolic binding,
  dependency ordering, outcome guarantee or effect permission is inferred
  from matching semantic type labels alone.
- No self-authorized policy, plugin-supplied policy grant or automatic
  admission. A plugin may be discovered automatically, but must not become
  visible in planning until the trusted Host policy includes its exact ref.
- This is not yet complete user-goal-to-WorkPlan planning. It is the first
  reusable typed, generically extensible planning surface prior to WorkStep.

## Acceptance tests

- Two arbitrary plugin operations `dynamic.collect` and `dynamic.summarize`
  compose by exact input/output types. Adding `dynamic.sign` makes a new
  two-step path available with **no modification to the algorithm**.
- Not-visible capabilities do not enter candidate planning; a stale
  candidate/policy identity is rejected, not silently refreshed.
- Type mismatch and unprovided input types yield no path; excess depth
  and invalid inputs fail closed.
- Sketches are immutable, carry exact candidate/policy lineage and
  never expose execution/authorization privileges.

## Next reviewed slices

- **G7A.2 — Host integration**: capture real current Runplane snapshots,
  trusted semantic/policy registry updates, visibility policy evaluation
  and live candidate-refresh; prove with a newly installed test plugin.
- **G7A.3 — WorkPlan candidate**: select a goal-driven path and require
  explicit values, scopes, symbolic references and effect envelopes, then
  route through original IRR work-plan admission and match boundaries.
- **G7B — governed dispatch**: only after separate durable, revocation,
  authorization-use and provider isolation gates. No dispatch from G7A.
