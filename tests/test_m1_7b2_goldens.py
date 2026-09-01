from __future__ import annotations

from intent_resolution_runtime import (
    BindingAttribution,
    BindingInputRole,
    BindingIssue,
    BindingRule,
    BindingSelectionMode,
    BindingSelectionPolicy,
    ContinuationInput,
    ContinuationInputAttribution,
    ContinuationSourceKind,
    InterchangeableChoicePolicy,
    RecordIdentity,
    ResolutionAttribution,
    ResolvedIntent,
    StableRef,
    SuccessorResolutionKind,
    SuccessorResolutionLineage,
    SymbolicReference,
    evaluate_binding,
)


REQUEST = RecordIdentity("sha256", "1" * 64)
CONTEXT_A = RecordIdentity("sha256", "2" * 64)
CONTEXT_B = RecordIdentity("sha256", "3" * 64)
SOURCE_ID = RecordIdentity("sha256", "4" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _predecessor() -> ResolvedIntent:
    return ResolvedIntent(
        REQUEST,
        CONTEXT_A,
        ResolutionAttribution(
            _ref("irr.resolver", "semantic-v1"),
            _ref("irr.event", "resolve-predecessor-001"),
        ),
        "Inspect bounded workspace.",
        (),
        (),
        (),
    )


def _binding_issue(predecessor: ResolvedIntent) -> BindingIssue:
    scope = "workspace:primary"
    symbolic = SymbolicReference(
        predecessor.identity,
        _ref("irr.slot", "selected-primary"),
        "artifact.path",
        scope,
        "Select one exact path for primary.",
    )
    rule = BindingRule(
        predecessor.identity,
        _ref("irr.binding_rule", "select-primary"),
        symbolic,
        (BindingInputRole.PLAN_LOCAL_OUTPUT,),
        (_ref("host.source", "filesystem-primary"),),
        (SOURCE_ID,),
        "artifact.path",
        scope,
        (),
        BindingSelectionPolicy(
            BindingSelectionMode.REQUIRE_UNIQUE,
            (),
            (),
            InterchangeableChoicePolicy.NONE,
        ),
        "Require one exact admitted path for primary.",
        (),
        (),
        (),
    )
    issue = evaluate_binding(
        rule,
        (),
        attribution=BindingAttribution(
            _ref("irr.evaluator", "mechanical-binding-v1"),
            _ref("irr.event", "binding-primary-001"),
        ),
    )
    assert type(issue) is BindingIssue
    return issue


def _continuation(predecessor: ResolvedIntent) -> ContinuationInput:
    return ContinuationInput(
        ContinuationInputAttribution(
            _ref("irr.host", "continuation-test"),
            _ref("irr.event", "reentry-primary-001"),
        ),
        ContinuationSourceKind.BINDING_ISSUE,
        _binding_issue(predecessor),
    )


def _successor(predecessor: ResolvedIntent) -> ResolvedIntent:
    return ResolvedIntent(
        predecessor.intent_request_identity,
        CONTEXT_B,
        ResolutionAttribution(
            _ref("irr.resolver", "semantic-v1"),
            _ref("irr.event", "resolve-successor-001"),
        ),
        "Successor semantics after exact continuation material.",
        (),
        (),
        (),
    )


def test_m17b2_successor_resolution_lineage_golden_is_frozen() -> None:
    predecessor = _predecessor()
    issue = _binding_issue(predecessor)
    continuation = ContinuationInput(
        ContinuationInputAttribution(
            _ref("irr.host", "continuation-test"),
            _ref("irr.event", "reentry-primary-001"),
        ),
        ContinuationSourceKind.BINDING_ISSUE,
        issue,
    )
    successor = _successor(predecessor)
    lineage = SuccessorResolutionLineage(
        predecessor,
        (continuation,),
        SuccessorResolutionKind.RESOLVED_INTENT,
        successor,
    )

    assert predecessor.identity.digest == (
        "6b6dc4d65e6954657b13d0fc93038baa2a83399ae81dc48f5e34019e6612919b"
    )
    assert issue.identity.digest == (
        "4ecaa5cae8cac4b13c6546ec5dd8bcf0306be479627ca62a879881991b77ba8f"
    )
    assert continuation.attribution.identity.digest == (
        "57ec30aee7fd82b72aef6b352ed39c56551c3479fcbfa44674857e88acdf31ce"
    )
    assert continuation.identity.digest == (
        "99a3efdccfe00a721db11d24b01d37c898c17ce984ed27ade2e735e717ac4046"
    )
    assert successor.identity.digest == (
        "ae49c4e3c6f58186cf8c77a6b9bcf497a01cb24828e76260764077bf345aa83f"
    )
    assert lineage.identity.digest == (
        "d747c722833e1ef1a19af5dc4a30ac5d6b9dddca710ea2aa98ae3ca1d44196a9"
    )


def test_m17b2_successor_resolution_lineage_golden_round_trips() -> None:
    predecessor = _predecessor()
    lineage = SuccessorResolutionLineage(
        predecessor,
        (_continuation(predecessor),),
        SuccessorResolutionKind.RESOLVED_INTENT,
        _successor(predecessor),
    )
    decoded = SuccessorResolutionLineage.from_json_bytes(lineage.canonical_bytes())
    assert decoded == lineage
    assert decoded.identity == lineage.identity
