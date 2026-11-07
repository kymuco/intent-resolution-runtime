"""G7A.4: HUMAN-origin IRR identity -> dynamic WorkPlan -> pending M32."""

from __future__ import annotations

from dataclasses import replace

import pytest

from intent_resolution_runtime import (
    ContextEnvelope,
    IntentExpression,
    IntentRequest,
    OriginAttribution,
    OriginKind,
    ResolutionAttribution,
    ResolvedIntent,
    SourceAttribution,
    StableRef,
)
from intent_resolution_runtime.bound_work_plan import (
    materialize_unadmitted_work_plan,
)
from intent_resolution_runtime.candidate_planning_surface import (
    HostPlanningVisibility,
    build_candidate_planning_surface,
)
from intent_resolution_runtime.dynamic_human_work_candidate import (
    DynamicHumanWorkCandidateError,
    assert_current_dynamic_human_work_candidate,
    prepare_dynamic_human_work_candidate,
)
from intent_resolution_runtime.identity import RecordIdentity
from intent_resolution_runtime.work_disposition import (
    CandidateWorkDisposition,
    WorkDispositionFrontierKind,
    WorkDispositionProposalAttribution,
    orchestrate_work_disposition,
)
from tests.test_g7a1_dynamic_candidate_planning import candidate, ref
from tests.test_g7a3_bound_work_plan import _material, _setup


def _lineage(*, origin=OriginKind.HUMAN, principal=None):
    first, second, surface, sketch = _setup()
    actor = surface.actor_ref
    request = IntentRequest(
        origin=OriginAttribution(
            kind=origin,
            actor_ref=actor,
            source_event_ref=ref("hde.human_event", "actual-ui-gesture"),
        ),
        principal_ref=principal or actor,
        expression=IntentExpression("Собери метаданные документа и краткое резюме."),
    )
    context = ContextEnvelope(
        intent_request_identity=request.identity,
        boundary_attribution=SourceAttribution(
            source_ref=ref("hde.core", "trusted-context"),
            source_event_ref=ref("hde.core_event", "original-human"),
        ),
        records=(),
    )
    resolved = ResolvedIntent(
        intent_request_identity=request.identity,
        context_envelope_identity=context.identity,
        admission_attribution=ResolutionAttribution(
            resolver_ref=ref("hde.resolver", "original-human"),
            admission_event_ref=ref("hde.m31", "explicit-human"),
        ),
        semantics="Produce a document summary.",
    )
    material = replace(
        _material(first, second),
        resolved_intent_identity=resolved.identity,
    )
    bound = materialize_unadmitted_work_plan(
        surface=surface, sketch=sketch, material=material
    )
    attribution = WorkDispositionProposalAttribution(
        proposer_ref=ref("hde.host", "trusted-preview-only"),
        proposal_event_ref=ref("hde.g7a4", "candidate-record"),
    )
    return request, context, resolved, bound, surface, attribution


def _prepare(*, overridden=None):
    request, context, resolved, bound, surface, attribution = (
        _lineage() if overridden is None else overridden
    )
    return prepare_dynamic_human_work_candidate(
        intent_request=request,
        context_envelope=context,
        resolved_intent=resolved,
        bound_work=bound,
        current_surface=surface,
        attribution=attribution,
        rationale="Explicit reviewed candidate; never grant from a model response.",
    )


def test_real_workplan_enters_existing_m32_frontier_as_pending_only():
    request, context, resolved, bound, surface, attribution = _lineage()
    pending = _prepare(
        overridden=(request, context, resolved, bound, surface, attribution)
    )
    assert type(pending.candidate) is CandidateWorkDisposition
    assert pending.candidate.work_plan == bound.work_plan
    assert pending.candidate.resolved_intent_identity == resolved.identity
    assert not pending.admitted and not pending.execution_authorized
    assert_current_dynamic_human_work_candidate(pending, surface)
    frontier = orchestrate_work_disposition(
        resolved, candidate_inputs=(pending.candidate,)
    )
    assert frontier.kind is WorkDispositionFrontierKind.ADMISSION_REQUIRED
    assert frontier.disposition_output is None


def test_nonhuman_origin_never_enters_m32_candidate():
    material = _lineage(origin=OriginKind.WORKER)
    with pytest.raises(DynamicHumanWorkCandidateError, match="non-HUMAN"):
        _prepare(overridden=material)


def test_actor_principal_and_policy_actor_must_be_exact():
    mismatch = _lineage(principal=ref("hde.principal", "another-user"))
    with pytest.raises(DynamicHumanWorkCandidateError, match="actor/principal"):
        _prepare(overridden=mismatch)
    request, context, resolved, bound, surface, attribution = _lineage()
    with pytest.raises(DynamicHumanWorkCandidateError, match="policy actor"):
        _prepare(
            overridden=(
                request,
                context,
                resolved,
                bound,
                replace(surface, actor_ref=ref("hde.actor", "imposter")),
                attribution,
            )
        )


def test_foreign_original_intent_and_context_rejected():
    request, context, resolved, bound, surface, attribution = _lineage()
    fake_request = replace(
        request, expression=IntentExpression("Different HUMAN intent")
    )
    with pytest.raises(DynamicHumanWorkCandidateError, match="exact original"):
        _prepare(
            overridden=(fake_request, context, resolved, bound, surface, attribution)
        )
    fake_context = replace(
        context,
        boundary_attribution=replace(
            context.boundary_attribution,
            source_event_ref=ref("hde.other", "foreign-context"),
        ),
    )
    with pytest.raises(DynamicHumanWorkCandidateError, match="exact original"):
        _prepare(
            overridden=(request, fake_context, resolved, bound, surface, attribution)
        )


def test_foreign_m31_identity_rejected_without_admission():
    request, context, resolved, bound, surface, attribution = _lineage()
    altered = replace(resolved, semantics="A different resolved goal")
    with pytest.raises(DynamicHumanWorkCandidateError, match="differs"):
        _prepare(overridden=(request, context, altered, bound, surface, attribution))


def test_new_catalog_or_revoked_policy_invalidates_original_candidate():
    request, context, resolved, bound, surface, attribution = _lineage()
    pending = _prepare(
        overridden=(request, context, resolved, bound, surface, attribution)
    )
    revised = build_candidate_planning_surface(
        candidate=candidate(
            *[option.descriptor for option in surface.options],
            event="revoked-or-replaced",
        ),
        visibility=HostPlanningVisibility(
            actor_ref=surface.actor_ref,
            policy_ref=surface.policy_ref,
            policy_revision_identity=RecordIdentity("sha256", "f" * 64),
            candidate_identity=candidate(
                *[option.descriptor for option in surface.options],
                event="revoked-or-replaced",
            ).identity,
            visible_capability_refs=tuple(x.capability_ref for x in surface.options),
        ),
    )
    with pytest.raises(DynamicHumanWorkCandidateError, match="stale"):
        assert_current_dynamic_human_work_candidate(pending, revised)


def test_foreign_proposer_and_empty_rationale_fail_closed():
    request, context, resolved, bound, surface, attribution = _lineage()
    with pytest.raises(DynamicHumanWorkCandidateError, match="proposer"):
        _prepare(
            overridden=(
                request,
                context,
                resolved,
                bound,
                surface,
                None,
            )
        )
    with pytest.raises(DynamicHumanWorkCandidateError, match="rationale"):
        prepare_dynamic_human_work_candidate(
            intent_request=request,
            context_envelope=context,
            resolved_intent=resolved,
            bound_work=bound,
            current_surface=surface,
            attribution=attribution,
            rationale="",
        )
