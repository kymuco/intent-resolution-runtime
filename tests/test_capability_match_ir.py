from __future__ import annotations

from dataclasses import replace

import pytest

from intent_resolution_runtime import (
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityEffect,
    CapabilityEffectMatch,
    CapabilityEffectRequirement,
    CapabilityExecutionBoundary,
    CapabilityExecutionBoundaryKind,
    CapabilityExecutionBoundaryRequirement,
    CapabilityInputContract,
    CapabilityInputMatch,
    CapabilityMatch,
    CapabilityMatchAttribution,
    CapabilityOutputContract,
    CapabilityOutputMatch,
    CapabilityRequestedEffect,
    CapabilityRequestedScope,
    CapabilityRequirement,
    CapabilityScopeMatch,
    CapabilityScopeRequirement,
    RecordIdentity,
    SerializationError,
    StableRef,
    SymbolicReference,
    ValidationError,
    WorkContinuationMode,
    WorkLiteralInput,
    WorkOutput,
    WorkPlan,
    WorkStep,
)


RESOLVED = RecordIdentity("sha256", "1" * 64)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _fixture() -> tuple[
    CapabilityRequirement,
    CapabilityDescriptor,
    CapabilityCatalogSnapshot,
    CapabilityMatch,
]:
    plan_ref = _ref("irr.work_plan", "extract-001")
    step_ref = _ref("irr.work_step", "extract")
    completion = (
        "Return an extraction receipt and the bounded resulting path set "
        "after extraction completes."
    )
    step = WorkStep(
        resolved_intent_identity=RESOLVED,
        work_plan_ref=plan_ref,
        step_ref=step_ref,
        operation="archive.extract",
        scope="workspace:project",
        inputs=(
            WorkLiteralInput("archive", "archive.path", "workspace:project/archive.zip"),
            WorkLiteralInput("destination", "filesystem.path", "workspace:out"),
        ),
        outputs=(
            WorkOutput(
                "receipt",
                SymbolicReference(
                    RESOLVED,
                    _ref("irr.symbolic_slot", "receipt"),
                    "archive.extraction_receipt",
                    "workspace:out",
                    "Extraction receipt.",
                ),
            ),
            WorkOutput(
                "files",
                SymbolicReference(
                    RESOLVED,
                    _ref("irr.symbolic_slot", "files"),
                    "filesystem.path_set",
                    "workspace:out",
                    "Extracted paths.",
                ),
            ),
        ),
        depends_on=(),
        continuation=WorkContinuationMode.NONE,
        completion_contract=completion,
        description="Extract one bounded archive.",
    )
    plan = WorkPlan(
        RESOLVED,
        plan_ref,
        (step,),
        "Complete the bounded archive extraction plan.",
        "One-step extraction plan.",
    )

    req_workspace = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", "workspace"),
        "filesystem.path_scope",
        "workspace:project",
        "Bounded source workspace.",
    )
    req_destination = CapabilityRequestedScope(
        _ref("irr.capability_requested_scope", "destination"),
        "filesystem.path_scope",
        "workspace:out",
        "Bounded destination.",
    )
    req_read = CapabilityRequestedEffect(
        _ref("irr.capability_requested_effect", "read"),
        "filesystem.read",
        (req_workspace.scope_ref,),
        "Read the selected archive.",
    )
    req_write = CapabilityRequestedEffect(
        _ref("irr.capability_requested_effect", "write"),
        "filesystem.write",
        (req_destination.scope_ref,),
        "Write extracted files.",
    )
    requirement = CapabilityRequirement(
        plan,
        step_ref,
        req_workspace.scope_ref,
        (req_destination, req_workspace),
        (req_write, req_read),
        (
            CapabilityExecutionBoundaryRequirement(
                CapabilityExecutionBoundaryKind.PROVIDER,
                _ref("irr.provider", "local-archive-adapter"),
                "Require the admitted local provider.",
            ),
        ),
        "Exact capability requirement for the selected WorkStep.",
    )

    cap_workspace = CapabilityScopeRequirement(
        _ref("irr.capability_scope_requirement", "workspace"),
        "filesystem.path_scope",
        "Invocation must provide bounded workspace source scope.",
    )
    cap_destination = CapabilityScopeRequirement(
        _ref("irr.capability_scope_requirement", "destination"),
        "filesystem.path_scope",
        "Invocation must provide bounded extraction destination scope.",
    )
    cap_archive = CapabilityInputContract(
        _ref("irr.capability_input", "archive"),
        "archive.path",
        (cap_workspace.requirement_ref,),
        "Archive input.",
    )
    cap_destination_input = CapabilityInputContract(
        _ref("irr.capability_input", "destination"),
        "filesystem.path",
        (cap_destination.requirement_ref,),
        "Destination input.",
    )
    cap_receipt = CapabilityOutputContract(
        _ref("irr.capability_output", "receipt"),
        "archive.extraction_receipt",
        (cap_destination.requirement_ref,),
        "Extraction receipt.",
    )
    cap_files = CapabilityOutputContract(
        _ref("irr.capability_output", "files"),
        "filesystem.path_set",
        (cap_destination.requirement_ref,),
        "Extracted path set.",
    )
    cap_read = CapabilityEffect(
        _ref("irr.capability_effect", "read"),
        "filesystem.read",
        CapabilityEffectRequirement.UNAVOIDABLE,
        (cap_workspace.requirement_ref,),
        "Archive read is unavoidable.",
    )
    cap_write = CapabilityEffect(
        _ref("irr.capability_effect", "write"),
        "filesystem.write",
        CapabilityEffectRequirement.UNAVOIDABLE,
        (cap_destination.requirement_ref,),
        "Destination write is unavoidable.",
    )
    descriptor = CapabilityDescriptor(
        _ref("irr.capability", "archive.extract"),
        "archive.extract",
        (cap_destination_input, cap_archive),
        (cap_receipt, cap_files),
        (cap_workspace, cap_destination),
        (cap_write, cap_read),
        (
            CapabilityExecutionBoundary(
                _ref("irr.provider", "local-archive-adapter"),
                CapabilityExecutionBoundaryKind.PROVIDER,
                "Local archive provider.",
            ),
            CapabilityExecutionBoundary(
                _ref("irr.executor", "archive-runtime-v2"),
                CapabilityExecutionBoundaryKind.EXECUTOR,
                "Archive executor.",
            ),
        ),
        completion,
        "Bounded local archive extraction capability.",
    )
    snapshot = CapabilityCatalogSnapshot(
        _ref("irr.capability_catalog", "host-default"),
        CapabilityCatalogAttribution(
            _ref("irr.host", "hde-shell"),
            _ref("irr.event", "catalog-001"),
        ),
        "Capabilities explicitly supplied for this planning surface only.",
        (descriptor,),
        "Exact host capability snapshot.",
    )
    match = CapabilityMatch(
        CapabilityMatchAttribution(
            _ref("irr.matcher", "semantic-match-v1"),
            _ref("irr.event", "match-001"),
        ),
        requirement,
        snapshot,
        descriptor.capability_ref,
        descriptor.identity,
        (
            CapabilityScopeMatch(req_workspace.scope_ref, cap_workspace.requirement_ref),
            CapabilityScopeMatch(
                req_destination.scope_ref, cap_destination.requirement_ref
            ),
        ),
        (
            CapabilityInputMatch(
                "archive", cap_archive.input_ref, (req_workspace.scope_ref,)
            ),
            CapabilityInputMatch(
                "destination",
                cap_destination_input.input_ref,
                (req_destination.scope_ref,),
            ),
        ),
        (
            CapabilityOutputMatch(
                "receipt", cap_receipt.output_ref, (req_destination.scope_ref,)
            ),
            CapabilityOutputMatch(
                "files", cap_files.output_ref, (req_destination.scope_ref,)
            ),
        ),
        (
            CapabilityEffectMatch(req_read.effect_ref, cap_read.effect_ref),
            CapabilityEffectMatch(req_write.effect_ref, cap_write.effect_ref),
        ),
        "Exact admitted semantic capability match.",
    )
    return requirement, descriptor, snapshot, match


def _with_descriptor(
    match: CapabilityMatch, descriptor: CapabilityDescriptor
) -> CapabilityMatch:
    snapshot = replace(match.catalog_snapshot, descriptors=(descriptor,))
    return replace(
        match,
        catalog_snapshot=snapshot,
        capability_ref=descriptor.capability_ref,
        capability_contract_identity=descriptor.identity,
    )


def test_round_trip_and_order_independence() -> None:
    requirement, _, _, match = _fixture()
    assert CapabilityRequirement.from_json_bytes(
        requirement.canonical_bytes()
    ).identity == requirement.identity
    assert CapabilityMatch.from_json_bytes(match.canonical_bytes()).identity == match.identity

    reordered_requirement = replace(
        requirement,
        requested_scopes=tuple(reversed(requirement.requested_scopes)),
        requested_effects=tuple(reversed(requirement.requested_effects)),
    )
    reordered_match = replace(
        match,
        requirement=reordered_requirement,
        scope_matches=tuple(reversed(match.scope_matches)),
        input_matches=tuple(reversed(match.input_matches)),
        output_matches=tuple(reversed(match.output_matches)),
        effect_matches=tuple(reversed(match.effect_matches)),
    )
    assert reordered_requirement.identity == requirement.identity
    assert reordered_match.identity == match.identity


def test_requirement_is_bound_to_exact_plan_and_primary_scope() -> None:
    requirement, _, _, _ = _fixture()
    changed_plan = replace(requirement.work_plan, description="Different exact plan.")
    assert replace(requirement, work_plan=changed_plan).identity != requirement.identity

    primary = next(
        item
        for item in requirement.requested_scopes
        if item.scope_ref == requirement.primary_scope_ref
    )
    changed_primary = replace(primary, value="workspace:other")
    with pytest.raises(ValidationError):
        replace(
            requirement,
            requested_scopes=tuple(
                changed_primary if item.scope_ref == primary.scope_ref else item
                for item in requirement.requested_scopes
            ),
        )


def test_exact_catalog_membership_operation_contract_and_completion_are_required() -> None:
    _, descriptor, _, match = _fixture()

    with pytest.raises(ValidationError):
        replace(match, catalog_snapshot=replace(match.catalog_snapshot, descriptors=()))
    with pytest.raises(ValidationError):
        replace(
            match,
            capability_contract_identity=RecordIdentity("sha256", "f" * 64),
        )
    with pytest.raises(ValidationError):
        _with_descriptor(match, replace(descriptor, operation="archive.inspect"))
    with pytest.raises(ValidationError):
        _with_descriptor(
            match,
            replace(descriptor, completion_contract="Return acceptance only."),
        )


def test_scope_and_input_mappings_are_bijective_and_semantically_exact() -> None:
    _, descriptor, _, match = _fixture()
    with pytest.raises(ValidationError):
        replace(match, scope_matches=match.scope_matches[:1])
    with pytest.raises(ValidationError):
        replace(match, input_matches=match.input_matches[:1])

    extra_input = CapabilityInputContract(
        _ref("irr.capability_input", "mode"),
        "archive.mode",
        (),
        "Additional required input.",
    )
    with pytest.raises(ValidationError):
        _with_descriptor(
            match,
            replace(descriptor, input_contracts=descriptor.input_contracts + (extra_input,)),
        )

    archive_contract = next(
        item for item in descriptor.input_contracts if item.input_ref.value == "archive"
    )
    changed_archive = replace(archive_contract, semantic_type="text")
    with pytest.raises(ValidationError):
        _with_descriptor(
            match,
            replace(
                descriptor,
                input_contracts=tuple(
                    changed_archive if item.input_ref == archive_contract.input_ref else item
                    for item in descriptor.input_contracts
                ),
            ),
        )


def test_every_work_output_is_mapped_but_unused_descriptor_output_is_allowed() -> None:
    _, descriptor, _, match = _fixture()
    with pytest.raises(ValidationError):
        replace(match, output_matches=match.output_matches[:1])

    extra_output = CapabilityOutputContract(
        _ref("irr.capability_output", "diagnostic"),
        "text.note",
        (),
        "Optional returned diagnostic.",
    )
    changed = _with_descriptor(
        match,
        replace(descriptor, output_contracts=descriptor.output_contracts + (extra_output,)),
    )
    assert changed.descriptor.output_contracts[-1] == extra_output


def test_unavoidable_effect_cannot_be_hidden_but_possible_extra_effect_can_remain_unmapped() -> None:
    _, descriptor, _, match = _fixture()
    unavoidable = CapabilityEffect(
        _ref("irr.capability_effect", "external"),
        "network.external_disclosure",
        CapabilityEffectRequirement.UNAVOIDABLE,
        (),
        "Unexpected unavoidable disclosure.",
    )
    with pytest.raises(ValidationError):
        _with_descriptor(match, replace(descriptor, effects=descriptor.effects + (unavoidable,)))

    possible = replace(
        unavoidable,
        effect_ref=_ref("irr.capability_effect", "diagnostic"),
        semantic_type="local.diagnostic_log",
        requirement=CapabilityEffectRequirement.POSSIBLE,
        description="Optional diagnostic effect.",
    )
    changed = _with_descriptor(match, replace(descriptor, effects=descriptor.effects + (possible,)))
    assert possible.effect_ref not in {item.descriptor_effect_ref for item in changed.effect_matches}


def test_boundary_requirement_and_catalog_occurrence_are_material() -> None:
    requirement, _, _, match = _fixture()
    missing = CapabilityExecutionBoundaryRequirement(
        CapabilityExecutionBoundaryKind.PROVIDER,
        _ref("irr.provider", "remote-service"),
        "Require another provider.",
    )
    with pytest.raises(ValidationError):
        replace(match, requirement=replace(requirement, execution_boundary_requirements=(missing,)))

    changed_snapshot = replace(
        match.catalog_snapshot,
        attribution=replace(
            match.catalog_snapshot.attribution,
            snapshot_event_ref=_ref("irr.event", "catalog-002"),
        ),
    )
    changed_match = replace(match, catalog_snapshot=changed_snapshot)
    assert changed_match.descriptor.identity == match.descriptor.identity
    assert changed_match.identity != match.identity


def test_authority_and_availability_cannot_be_smuggled_into_match_wire() -> None:
    _, _, _, match = _fixture()
    for field in ("authorized", "available"):
        primitive = match.to_primitive()
        primitive[field] = "true"
        with pytest.raises(SerializationError):
            CapabilityMatch.from_primitive(primitive)


def test_public_records_are_closed() -> None:
    with pytest.raises(TypeError):
        class _BadMatch(CapabilityMatch):
            pass

    with pytest.raises(TypeError):
        class _BadRequirement(CapabilityRequirement):
            pass
