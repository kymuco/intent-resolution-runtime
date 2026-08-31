from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from intent_resolution_runtime import (
    AssumptionKind,
    AssumptionRecord,
    CandidateAttribution,
    CandidateResolution,
    ClarificationNeed,
    ClarificationProposal,
    InformationNeed,
    InformationNeedProposal,
    IntentExpression,
    IntentRequest,
    OriginAttribution,
    OriginKind,
    RecordIdentity,
    ResolutionAttribution,
    ResolutionIssue,
    ResolutionIssueImpact,
    ResolutionIssueKind,
    ResolvedIntent,
    SerializationError,
    StableRef,
    ValidationError,
)


def rid(ch: str) -> RecordIdentity:
    return RecordIdentity("sha256", ch * 64)


def candidate_attr() -> CandidateAttribution:
    return CandidateAttribution(
        provider_ref=StableRef("irr.provider", "llm-a"),
        invocation_ref=StableRef("irr.provider_invocation", "inv-001"),
    )


def admission_attr(event: str = "admit-001") -> ResolutionAttribution:
    return ResolutionAttribution(
        resolver_ref=StableRef("irr.resolver", "core"),
        admission_event_ref=StableRef("irr.resolution_event", event),
    )


def assumption() -> AssumptionRecord:
    return AssumptionRecord(
        kind=AssumptionKind.PRESENTATION,
        statement="Present candidates alphabetically.",
        scope="display ordering only; not semantic selection",
        rationale="presentation order does not choose a material referent",
    )


def ambiguity() -> ResolutionIssue:
    return ResolutionIssue(
        kind=ResolutionIssueKind.MATERIAL_AMBIGUITY,
        impact=ResolutionIssueImpact.BLOCKING,
        scope="launch target",
        description="The pronoun 'it' has two plausible admitted referents.",
        alternatives=("process:alpha", "process:beta"),
    )


def missing() -> ResolutionIssue:
    return ResolutionIssue(
        kind=ResolutionIssueKind.MISSING_INFORMATION,
        impact=ResolutionIssueImpact.BLOCKING,
        scope="report freshness",
        description="No attributable modification-time listing is admitted.",
    )


def conflict_nonblocking() -> ResolutionIssue:
    return ResolutionIssue(
        kind=ResolutionIssueKind.CONFLICT,
        impact=ResolutionIssueImpact.NON_BLOCKING,
        scope="non-material display label",
        description="Two sources disagree on a display-only label.",
        alternatives=("Report", "Report draft"),
    )


def candidate() -> CandidateResolution:
    return CandidateResolution(
        intent_request_identity=rid("1"),
        context_envelope_identity=rid("2"),
        attribution=candidate_attr(),
        proposed_semantics="The request asks IRR to launch a referenced target, but the target is unresolved.",
        assumptions=(assumption(),),
        issues=(ambiguity(),),
        clarification_proposals=(
            ClarificationProposal(
                question="Which target do you mean: alpha or beta?",
                scope="launch target identity",
                reason="Choosing either target would materially change the executable target.",
            ),
        ),
    )


def test_candidate_is_not_resolved_intent() -> None:
    value = candidate()
    assert type(value) is CandidateResolution
    assert not isinstance(value, ResolvedIntent)
    assert value.to_primitive()["schema"] == "irr.candidate_resolution.v1"


def test_candidate_attribution_is_provider_occurrence_not_authority() -> None:
    primitive = candidate().to_primitive()
    assert primitive["attribution"]["provider_ref"]["value"] == "llm-a"
    text = candidate().canonical_bytes().decode()
    assert "authorized" not in text
    assert "approved" not in text
    assert "verified" not in text


def test_candidate_identity_is_bound_to_request_context_and_provider_invocation() -> None:
    base = candidate()
    changed_context = CandidateResolution(
        intent_request_identity=base.intent_request_identity,
        context_envelope_identity=rid("3"),
        attribution=base.attribution,
        proposed_semantics=base.proposed_semantics,
        assumptions=base.assumptions,
        issues=base.issues,
        clarification_proposals=base.clarification_proposals,
    )
    changed_invocation = CandidateResolution(
        intent_request_identity=base.intent_request_identity,
        context_envelope_identity=base.context_envelope_identity,
        attribution=CandidateAttribution(
            base.attribution.provider_ref,
            StableRef("irr.provider_invocation", "inv-002"),
        ),
        proposed_semantics=base.proposed_semantics,
        assumptions=base.assumptions,
        issues=base.issues,
        clarification_proposals=base.clarification_proposals,
    )
    assert base.identity != changed_context.identity
    assert base.identity != changed_invocation.identity


def test_material_ambiguity_must_be_blocking_and_preserve_alternatives() -> None:
    with pytest.raises(ValidationError, match="must be blocking"):
        ResolutionIssue(
            kind=ResolutionIssueKind.MATERIAL_AMBIGUITY,
            impact=ResolutionIssueImpact.NON_BLOCKING,
            scope="recipient",
            description="two recipients",
            alternatives=("Ivan A", "Ivan B"),
        )
    with pytest.raises(ValidationError, match="at least two alternatives"):
        ResolutionIssue(
            kind=ResolutionIssueKind.MATERIAL_AMBIGUITY,
            impact=ResolutionIssueImpact.BLOCKING,
            scope="recipient",
            description="ambiguous recipient",
            alternatives=("Ivan A",),
        )


def test_conflict_alternatives_are_unordered_no_precedence() -> None:
    first = ResolutionIssue(
        kind=ResolutionIssueKind.CONFLICT,
        impact=ResolutionIssueImpact.BLOCKING,
        scope="recipient identity",
        description="sources disagree",
        alternatives=("Ivan B", "Ivan A"),
    )
    second = ResolutionIssue(
        kind=first.kind,
        impact=first.impact,
        scope=first.scope,
        description=first.description,
        alternatives=("Ivan A", "Ivan B"),
    )
    assert first.alternatives == ("Ivan A", "Ivan B")
    assert first.identity == second.identity


def test_assumption_is_explicit_non_material_and_identity_material() -> None:
    first = assumption()
    second = AssumptionRecord(
        kind=first.kind,
        statement="Use compact bullets.",
        scope=first.scope,
        rationale=first.rationale,
    )
    assert first.identity != second.identity
    assert first.to_primitive()["kind"] == "presentation"


def test_resolved_intent_rejects_blocking_issue() -> None:
    with pytest.raises(ValidationError, match="blocking"):
        ResolvedIntent(
            intent_request_identity=rid("1"),
            context_envelope_identity=rid("2"),
            admission_attribution=admission_attr(),
            semantics="Launch target alpha.",
            unresolved_issues=(ambiguity(),),
        )


def test_resolved_intent_allows_explicit_nonblocking_conflict_without_workplan() -> None:
    resolved = ResolvedIntent(
        intent_request_identity=rid("1"),
        context_envelope_identity=rid("2"),
        admission_attribution=admission_attr(),
        semantics="Explain the admitted result; no operational work is required.",
        assumptions=(assumption(),),
        unresolved_issues=(conflict_nonblocking(),),
        candidate_inputs=(candidate(),),
    )
    primitive = resolved.to_primitive()
    assert primitive["schema"] == "irr.resolved_intent.v1"
    assert "work_plan" not in primitive
    assert "authorization" not in primitive
    assert "effect" not in primitive


def test_clarification_need_is_pause_not_resolved_intent() -> None:
    need = ClarificationNeed(
        intent_request_identity=rid("1"),
        context_envelope_identity=rid("2"),
        admission_attribution=admission_attr(),
        question="Which target do you mean?",
        scope="launch target identity",
        blocking_issues=(ambiguity(),),
        candidate_inputs=(candidate(),),
    )
    assert type(need) is ClarificationNeed
    assert not isinstance(need, ResolvedIntent)
    assert need.to_primitive()["schema"] == "irr.clarification_need.v1"


def test_clarification_need_can_request_missing_information_from_continuation() -> None:
    need = ClarificationNeed(
        intent_request_identity=rid("1"),
        context_envelope_identity=rid("2"),
        admission_attribution=admission_attr(),
        question="Which report listing should be treated as the bounded source?",
        scope="report freshness",
        blocking_issues=(missing(),),
    )
    assert need.blocking_issues[0].kind is ResolutionIssueKind.MISSING_INFORMATION


def test_information_need_is_bounded_and_not_retrieval_authority() -> None:
    need = InformationNeed(
        intent_request_identity=rid("1"),
        context_envelope_identity=rid("2"),
        admission_attribution=admission_attr(),
        description="An attributable bounded listing of report modification times.",
        scope="reports visible in the admitted workspace report directory",
        reason="The term latest cannot be grounded from current Context.",
        blocking_issues=(missing(),),
        candidate_inputs=(candidate(),),
    )
    text = need.canonical_bytes().decode()
    assert "retrieval_authorized" not in text
    assert "observation_authorized" not in text
    assert "permission" not in text


def test_candidate_can_propose_info_need_without_acquisition_authority() -> None:
    value = CandidateResolution(
        intent_request_identity=rid("1"),
        context_envelope_identity=rid("2"),
        attribution=candidate_attr(),
        proposed_semantics="Latest report remains unresolved without attributable listing data.",
        issues=(missing(),),
        information_need_proposals=(
            InformationNeedProposal(
                description="bounded report listing with modification timestamps",
                scope="admitted reports directory",
                reason="needed to ground latest",
            ),
        ),
    )
    assert value.information_need_proposals
    assert "authorized" not in value.canonical_bytes().decode()


def test_collection_order_does_not_smuggle_candidate_precedence() -> None:
    a = ClarificationProposal("Which target?", "target", "material choice")
    b = ClarificationProposal("Which recipient?", "recipient", "material choice")
    first = CandidateResolution(
        intent_request_identity=rid("1"),
        context_envelope_identity=rid("2"),
        attribution=candidate_attr(),
        proposed_semantics="Two independent material choices remain.",
        clarification_proposals=(a, b),
    )
    second = CandidateResolution(
        intent_request_identity=first.intent_request_identity,
        context_envelope_identity=first.context_envelope_identity,
        attribution=first.attribution,
        proposed_semantics=first.proposed_semantics,
        clarification_proposals=(b, a),
    )
    assert first.identity == second.identity


def test_round_trip_preserves_candidate_and_outputs() -> None:
    cand = candidate()
    assert CandidateResolution.from_json_bytes(cand.canonical_bytes()) == cand

    resolved = ResolvedIntent(
        intent_request_identity=rid("1"),
        context_envelope_identity=rid("2"),
        admission_attribution=admission_attr(),
        semantics="Answer-only resolution.",
        candidate_inputs=(cand,),
    )
    assert ResolvedIntent.from_json_bytes(resolved.canonical_bytes()) == resolved

    clarification = ClarificationNeed(
        intent_request_identity=rid("1"),
        context_envelope_identity=rid("2"),
        admission_attribution=admission_attr(),
        question="Which target?",
        scope="target",
        blocking_issues=(ambiguity(),),
        candidate_inputs=(cand,),
    )
    assert ClarificationNeed.from_json_bytes(clarification.canonical_bytes()) == clarification

    info = InformationNeed(
        intent_request_identity=rid("1"),
        context_envelope_identity=rid("2"),
        admission_attribution=admission_attr(),
        description="bounded listing",
        scope="reports",
        reason="ground latest",
        blocking_issues=(missing(),),
    )
    assert InformationNeed.from_json_bytes(info.canonical_bytes()) == info


def test_authority_and_confidence_smuggling_is_fail_closed() -> None:
    cand = candidate()
    text = cand.canonical_bytes().decode()
    tampered = text[:-1] + ',"confidence":"high","authorized":"yes"}'
    with pytest.raises(SerializationError, match="invalid fields"):
        CandidateResolution.from_json_bytes(tampered.encode())

    resolved = ResolvedIntent(
        intent_request_identity=rid("1"),
        context_envelope_identity=rid("2"),
        admission_attribution=admission_attr(),
        semantics="Answer-only resolution.",
    )
    text = resolved.canonical_bytes().decode()
    tampered = text[:-1] + ',"approved":"yes"}'
    with pytest.raises(SerializationError, match="invalid fields"):
        ResolvedIntent.from_json_bytes(tampered.encode())


def test_records_are_immutable_and_slotted() -> None:
    issue = ambiguity()
    with pytest.raises(FrozenInstanceError):
        issue.description = "changed"  # type: ignore[misc]
    assert not hasattr(issue, "__dict__")
    assert not hasattr(candidate(), "__dict__")


def test_m11_golden_digest_is_preserved() -> None:
    request = IntentRequest(
        origin=OriginAttribution(
            kind=OriginKind.COMPANION,
            actor_ref=StableRef("character_os.actor", "kaguya"),
            source_event_ref=StableRef("hde.event", "evt-001"),
        ),
        principal_ref=StableRef("hde.principal", "user:self"),
        expression=IntentExpression("Стоит проверить последние логи."),
    )
    assert request.identity.digest == "bedad2f962490352db8d156a3e39cbd40c2cbc6071a0bfc64899607fdd2967e8"


def test_resolution_record_types_are_closed() -> None:
    closed = (
        CandidateAttribution,
        ResolutionAttribution,
        AssumptionRecord,
        ResolutionIssue,
        ClarificationProposal,
        InformationNeedProposal,
        CandidateResolution,
        ResolvedIntent,
        ClarificationNeed,
        InformationNeed,
    )
    for base in closed:
        with pytest.raises(TypeError, match="closed IR type"):
            type(f"Hidden{base.__name__}", (base,), {"__slots__": ("hidden",)})


def test_m13_candidate_and_resolved_golden_digests_are_frozen() -> None:
    cand = candidate()
    resolved = ResolvedIntent(
        intent_request_identity=rid("1"),
        context_envelope_identity=rid("2"),
        admission_attribution=admission_attr(),
        semantics="Explain the admitted result; no operational work is required.",
        assumptions=(assumption(),),
        unresolved_issues=(conflict_nonblocking(),),
        candidate_inputs=(cand,),
    )
    assert cand.identity.digest == "480e4745d996e82b9faa8bffff4a02be6bf79e04c8423008fb825842e0976e5d"
    assert resolved.identity.digest == "c47d45338347536d6ce576598dd17bd59c91ab82581c6fb11c631be1edbb161e"


def test_admitted_candidate_lineage_is_exact_candidate_not_bare_digest() -> None:
    with pytest.raises(ValidationError, match="candidate_inputs contains an unsupported record type"):
        ResolvedIntent(
            intent_request_identity=rid("1"),
            context_envelope_identity=rid("2"),
            admission_attribution=admission_attr(),
            semantics="Answer-only resolution.",
            candidate_inputs=(candidate().identity,),  # type: ignore[arg-type]
        )
