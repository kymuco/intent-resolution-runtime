from __future__ import annotations

import json

import pytest

from intent_resolution_runtime import (
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityEffect,
    CapabilityEffectRequirement,
    CapabilityInputContract,
    CapabilityOutputContract,
    CapabilityScopeRequirement,
    SerializationError,
    StableRef,
    ValidationError,
)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _scope(name: str = "workspace") -> CapabilityScopeRequirement:
    return CapabilityScopeRequirement(
        requirement_ref=_ref("irr.capability_scope_requirement", name),
        semantic_type="filesystem.path_scope",
        statement=f"Invocation must provide bounded {name} scope.",
    )


def _input(
    name: str,
    *scope_refs: StableRef,
    semantic_type: str = "filesystem.path",
) -> CapabilityInputContract:
    return CapabilityInputContract(
        input_ref=_ref("irr.capability_input", name),
        semantic_type=semantic_type,
        scope_requirement_refs=tuple(scope_refs),
        description=f"Capability input {name}.",
    )


def _output(
    name: str,
    *,
    semantic_type: str = "artifact.metadata",
) -> CapabilityOutputContract:
    return CapabilityOutputContract(
        output_ref=_ref("irr.capability_output", name),
        semantic_type=semantic_type,
        description=f"Capability output {name}.",
    )


def _effect(
    name: str,
    *scope_refs: StableRef,
    requirement: CapabilityEffectRequirement = CapabilityEffectRequirement.POSSIBLE,
    semantic_type: str = "filesystem.read",
) -> CapabilityEffect:
    return CapabilityEffect(
        effect_ref=_ref("irr.capability_effect", name),
        semantic_type=semantic_type,
        requirement=requirement,
        scope_requirement_refs=tuple(scope_refs),
        description=f"Capability effect {name}.",
    )


def _descriptor(
    *,
    capability: str = "archive.inspect",
    operation: str = "archive.inspect",
    completion_contract: str = "Return inspectable archive metadata after the bounded inspection.",
    execution_boundary_refs: tuple[StableRef, ...] = (
        StableRef("irr.executor", "archive-runtime-v1"),
    ),
) -> CapabilityDescriptor:
    workspace = _scope("workspace")
    return CapabilityDescriptor(
        capability_ref=_ref("irr.capability", capability),
        operation=operation,
        input_contracts=(
            _input("archive", workspace.requirement_ref, semantic_type="archive.path"),
        ),
        output_contracts=(
            _output("metadata", semantic_type="archive.metadata"),
        ),
        scope_requirements=(workspace,),
        effects=(
            _effect(
                "read-archive",
                workspace.requirement_ref,
                requirement=CapabilityEffectRequirement.UNAVOIDABLE,
                semantic_type="filesystem.read",
            ),
        ),
        execution_boundary_refs=execution_boundary_refs,
        completion_contract=completion_contract,
        description="Bounded archive inspection capability.",
    )


def _catalog(
    *descriptors: CapabilityDescriptor,
    event: str = "catalog-001",
) -> CapabilityCatalogSnapshot:
    return CapabilityCatalogSnapshot(
        catalog_ref=_ref("irr.capability_catalog", "host-default"),
        attribution=CapabilityCatalogAttribution(
            supplier_ref=_ref("irr.host", "hde-shell"),
            snapshot_event_ref=_ref("irr.event", event),
        ),
        scope_statement="Capabilities explicitly supplied for this planning surface only.",
        descriptors=tuple(descriptors),
        description="Exact bounded host capability catalog snapshot.",
    )


def test_descriptor_round_trip_and_set_like_surfaces_are_canonical() -> None:
    workspace = _scope("workspace")
    destination = _scope("destination")
    input_archive = _input(
        "archive", workspace.requirement_ref, semantic_type="archive.path"
    )
    input_destination = _input(
        "destination", destination.requirement_ref, semantic_type="filesystem.path"
    )
    out_receipt = _output("receipt", semantic_type="archive.extraction_receipt")
    out_files = _output("files", semantic_type="filesystem.path_set")
    effect_read = _effect(
        "read",
        workspace.requirement_ref,
        requirement=CapabilityEffectRequirement.UNAVOIDABLE,
        semantic_type="filesystem.read",
    )
    effect_write = _effect(
        "write",
        destination.requirement_ref,
        requirement=CapabilityEffectRequirement.UNAVOIDABLE,
        semantic_type="filesystem.write",
    )
    executor = _ref("irr.executor", "archive-runtime-v2")
    provider = _ref("irr.provider", "local-archive-adapter")

    first = CapabilityDescriptor(
        capability_ref=_ref("irr.capability", "archive.extract"),
        operation="archive.extract",
        input_contracts=(input_destination, input_archive),
        output_contracts=(out_receipt, out_files),
        scope_requirements=(destination, workspace),
        effects=(effect_write, effect_read),
        execution_boundary_refs=(provider, executor),
        completion_contract="Return extraction receipt and resulting bounded path set.",
        description="Bounded archive extraction.",
    )
    second = CapabilityDescriptor(
        capability_ref=_ref("irr.capability", "archive.extract"),
        operation="archive.extract",
        input_contracts=(input_archive, input_destination),
        output_contracts=(out_files, out_receipt),
        scope_requirements=(workspace, destination),
        effects=(effect_read, effect_write),
        execution_boundary_refs=(executor, provider),
        completion_contract="Return extraction receipt and resulting bounded path set.",
        description="Bounded archive extraction.",
    )

    assert first == second
    assert first.canonical_bytes() == second.canonical_bytes()
    assert first.identity == second.identity
    assert CapabilityDescriptor.from_json_bytes(first.canonical_bytes()) == first


def test_catalog_snapshot_order_is_canonical_and_empty_snapshot_is_valid() -> None:
    inspect = _descriptor()
    search = _descriptor(
        capability="filesystem.search",
        operation="filesystem.search",
        completion_contract="Return the bounded matching path set.",
    )
    first = _catalog(search, inspect)
    second = _catalog(inspect, search)

    assert first == second
    assert first.identity == second.identity
    assert CapabilityCatalogSnapshot.from_json_bytes(first.canonical_bytes()) == first

    empty = _catalog()
    assert empty.descriptors == ()
    assert empty.to_primitive()["descriptors"] == []


def test_same_logical_capability_ref_with_changed_contract_changes_identity() -> None:
    original = _descriptor()
    changed_completion = _descriptor(
        completion_contract="Return only an acknowledgement that inspection was scheduled."
    )
    changed_executor = _descriptor(
        execution_boundary_refs=(
            _ref("irr.executor", "remote-archive-service"),
        )
    )

    assert original.capability_ref == changed_completion.capability_ref
    assert original.identity != changed_completion.identity
    assert original.identity != changed_executor.identity

    assert _catalog(original).identity != _catalog(changed_completion).identity


def test_catalog_rejects_duplicate_logical_capability_refs_even_if_contracts_differ() -> None:
    first = _descriptor()
    second = _descriptor(
        completion_contract="Return weaker acknowledgement semantics."
    )
    with pytest.raises(ValidationError, match="duplicate capability_ref"):
        _catalog(first, second)


def test_input_and_effect_scope_links_must_reference_descriptor_requirements() -> None:
    admitted = _scope("workspace")
    foreign = _scope("foreign")

    with pytest.raises(ValidationError, match="input contracts"):
        CapabilityDescriptor(
            capability_ref=_ref("irr.capability", "filesystem.inspect"),
            operation="filesystem.inspect",
            input_contracts=(
                _input("path", foreign.requirement_ref),
            ),
            output_contracts=(),
            scope_requirements=(admitted,),
            effects=(),
            execution_boundary_refs=(),
            completion_contract="Return bounded inspection material.",
            description="Invalid foreign input scope relation.",
        )

    with pytest.raises(ValidationError, match="effects"):
        CapabilityDescriptor(
            capability_ref=_ref("irr.capability", "filesystem.inspect"),
            operation="filesystem.inspect",
            input_contracts=(),
            output_contracts=(),
            scope_requirements=(admitted,),
            effects=(
                _effect(
                    "read",
                    foreign.requirement_ref,
                    requirement=CapabilityEffectRequirement.UNAVOIDABLE,
                ),
            ),
            execution_boundary_refs=(),
            completion_contract="Return bounded inspection material.",
            description="Invalid foreign effect scope relation.",
        )


def test_possible_and_unavoidable_effects_are_distinct_contract_semantics() -> None:
    scope = _scope()
    possible = CapabilityDescriptor(
        capability_ref=_ref("irr.capability", "artifact.inspect"),
        operation="artifact.inspect",
        input_contracts=(),
        output_contracts=(),
        scope_requirements=(scope,),
        effects=(
            _effect(
                "network",
                scope.requirement_ref,
                requirement=CapabilityEffectRequirement.POSSIBLE,
                semantic_type="network.interaction",
            ),
        ),
        execution_boundary_refs=(),
        completion_contract="Return bounded inspection material.",
        description="Capability with conditional network effect envelope.",
    )
    unavoidable = CapabilityDescriptor(
        capability_ref=possible.capability_ref,
        operation=possible.operation,
        input_contracts=possible.input_contracts,
        output_contracts=possible.output_contracts,
        scope_requirements=possible.scope_requirements,
        effects=(
            _effect(
                "network",
                scope.requirement_ref,
                requirement=CapabilityEffectRequirement.UNAVOIDABLE,
                semantic_type="network.interaction",
            ),
        ),
        execution_boundary_refs=possible.execution_boundary_refs,
        completion_contract=possible.completion_contract,
        description=possible.description,
    )

    assert possible.identity != unavoidable.identity


def test_operation_uses_same_closed_semantic_identifier_shape_as_work_ir() -> None:
    with pytest.raises(ValidationError, match="lowercase dotted"):
        _descriptor(operation="rm -rf /")
    with pytest.raises(ValidationError, match="lowercase dotted"):
        _descriptor(operation="Archive.Extract")
    assert _descriptor(operation="archive.extract").operation == "archive.extract"


def test_catalog_attribution_occurrence_is_identity_material_but_not_authority() -> None:
    descriptor = _descriptor()
    first = _catalog(descriptor, event="catalog-001")
    second = _catalog(descriptor, event="catalog-002")

    assert first.identity != second.identity
    primitive_text = first.canonical_bytes().decode("utf-8")
    assert "authorization" not in primitive_text.lower()
    assert "approved" not in primitive_text.lower()
    assert "available" not in primitive_text.lower()


def test_descriptor_wire_has_no_availability_or_authority_fields() -> None:
    primitive = _descriptor().to_primitive()
    assert "availability" not in primitive
    assert "authorized" not in primitive
    assert "authorization" not in primitive
    assert "safe" not in primitive
    assert "permission" not in primitive


def test_strict_wire_rejects_unknown_authority_like_fields() -> None:
    descriptor = _descriptor()
    obj = json.loads(descriptor.canonical_bytes())
    obj["authorized"] = "true"
    with pytest.raises(SerializationError, match="invalid fields"):
        CapabilityDescriptor.from_json_bytes(
            json.dumps(obj, separators=(",", ":")).encode("utf-8")
        )

    snapshot = _catalog(descriptor)
    snap_obj = json.loads(snapshot.canonical_bytes())
    snap_obj["availability"] = "online"
    with pytest.raises(SerializationError, match="invalid fields"):
        CapabilityCatalogSnapshot.from_json_bytes(
            json.dumps(snap_obj, separators=(",", ":")).encode("utf-8")
        )


def test_duplicate_semantic_refs_fail_closed() -> None:
    scope = _scope()
    duplicate_scope = CapabilityScopeRequirement(
        requirement_ref=scope.requirement_ref,
        semantic_type="other.scope",
        statement="Conflicting duplicate requirement.",
    )
    with pytest.raises(ValidationError, match="duplicate requirement_ref"):
        CapabilityDescriptor(
            capability_ref=_ref("irr.capability", "archive.inspect"),
            operation="archive.inspect",
            input_contracts=(),
            output_contracts=(),
            scope_requirements=(scope, duplicate_scope),
            effects=(),
            execution_boundary_refs=(),
            completion_contract="Return bounded result.",
            description="Invalid duplicate scope descriptor.",
        )

    with pytest.raises(ValidationError, match="duplicates"):
        CapabilityDescriptor(
            capability_ref=_ref("irr.capability", "archive.inspect"),
            operation="archive.inspect",
            input_contracts=(),
            output_contracts=(),
            scope_requirements=(),
            effects=(),
            execution_boundary_refs=(
                _ref("irr.executor", "archive-runtime"),
                _ref("irr.executor", "archive-runtime"),
            ),
            completion_contract="Return bounded result.",
            description="Invalid duplicate execution boundary.",
        )


def test_records_reject_subclassing_through_public_ir_surface() -> None:
    with pytest.raises(TypeError, match="closed IR type"):
        class ExtendedCapabilityDescriptor(CapabilityDescriptor):
            pass
