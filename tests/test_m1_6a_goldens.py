from __future__ import annotations

from intent_resolution_runtime import (
    CapabilityCatalogAttribution,
    CapabilityCatalogSnapshot,
    CapabilityDescriptor,
    CapabilityEffect,
    CapabilityEffectRequirement,
    CapabilityExecutionBoundary,
    CapabilityExecutionBoundaryKind,
    CapabilityInputContract,
    CapabilityOutputContract,
    CapabilityScopeRequirement,
    StableRef,
)


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _fixture() -> tuple[
    CapabilityCatalogAttribution,
    CapabilityScopeRequirement,
    CapabilityScopeRequirement,
    CapabilityInputContract,
    CapabilityInputContract,
    CapabilityOutputContract,
    CapabilityOutputContract,
    CapabilityEffect,
    CapabilityEffect,
    CapabilityExecutionBoundary,
    CapabilityExecutionBoundary,
    CapabilityDescriptor,
    CapabilityCatalogSnapshot,
]:
    workspace_scope = CapabilityScopeRequirement(
        requirement_ref=_ref("irr.capability_scope_requirement", "workspace"),
        semantic_type="filesystem.path_scope",
        statement="Invocation must provide bounded workspace source scope.",
    )
    destination_scope = CapabilityScopeRequirement(
        requirement_ref=_ref("irr.capability_scope_requirement", "destination"),
        semantic_type="filesystem.path_scope",
        statement="Invocation must provide bounded extraction destination scope.",
    )

    archive_input = CapabilityInputContract(
        input_ref=_ref("irr.capability_input", "archive"),
        semantic_type="archive.path",
        scope_requirement_refs=(workspace_scope.requirement_ref,),
        description="Archive input inside the bounded workspace scope.",
    )
    destination_input = CapabilityInputContract(
        input_ref=_ref("irr.capability_input", "destination"),
        semantic_type="filesystem.path",
        scope_requirement_refs=(destination_scope.requirement_ref,),
        description="Extraction destination inside the bounded destination scope.",
    )

    receipt_output = CapabilityOutputContract(
        output_ref=_ref("irr.capability_output", "receipt"),
        semantic_type="archive.extraction_receipt",
        scope_requirement_refs=(destination_scope.requirement_ref,),
        description="Receipt describing the bounded extraction result.",
    )
    files_output = CapabilityOutputContract(
        output_ref=_ref("irr.capability_output", "files"),
        semantic_type="filesystem.path_set",
        scope_requirement_refs=(destination_scope.requirement_ref,),
        description="Paths produced inside the bounded destination scope.",
    )

    read_effect = CapabilityEffect(
        effect_ref=_ref("irr.capability_effect", "read-archive"),
        semantic_type="filesystem.read",
        requirement=CapabilityEffectRequirement.UNAVOIDABLE,
        scope_requirement_refs=(workspace_scope.requirement_ref,),
        description="Reading the selected archive is unavoidable.",
    )
    write_effect = CapabilityEffect(
        effect_ref=_ref("irr.capability_effect", "write-destination"),
        semantic_type="filesystem.write",
        requirement=CapabilityEffectRequirement.UNAVOIDABLE,
        scope_requirement_refs=(destination_scope.requirement_ref,),
        description="Writing extracted files to the destination is unavoidable.",
    )

    provider_boundary = CapabilityExecutionBoundary(
        boundary_ref=_ref("irr.provider", "local-archive-adapter"),
        kind=CapabilityExecutionBoundaryKind.PROVIDER,
        description="Local archive capability provider boundary.",
    )
    executor_boundary = CapabilityExecutionBoundary(
        boundary_ref=_ref("irr.executor", "archive-runtime-v2"),
        kind=CapabilityExecutionBoundaryKind.EXECUTOR,
        description="Archive runtime executor boundary.",
    )

    descriptor = CapabilityDescriptor(
        capability_ref=_ref("irr.capability", "archive.extract"),
        operation="archive.extract",
        input_contracts=(destination_input, archive_input),
        output_contracts=(receipt_output, files_output),
        scope_requirements=(workspace_scope, destination_scope),
        effects=(write_effect, read_effect),
        execution_boundaries=(provider_boundary, executor_boundary),
        completion_contract=(
            "Return an extraction receipt and the bounded resulting path set "
            "after extraction completes."
        ),
        description="Bounded local archive extraction capability.",
    )

    attribution = CapabilityCatalogAttribution(
        supplier_ref=_ref("irr.host", "hde-shell"),
        snapshot_event_ref=_ref("irr.event", "catalog-001"),
    )
    snapshot = CapabilityCatalogSnapshot(
        catalog_ref=_ref("irr.capability_catalog", "host-default"),
        attribution=attribution,
        scope_statement="Capabilities explicitly supplied for this planning surface only.",
        descriptors=(descriptor,),
        description="Exact bounded host capability catalog snapshot.",
    )

    return (
        attribution,
        workspace_scope,
        destination_scope,
        archive_input,
        destination_input,
        receipt_output,
        files_output,
        read_effect,
        write_effect,
        provider_boundary,
        executor_boundary,
        descriptor,
        snapshot,
    )


def test_m16a_capability_catalog_golden_digests_are_frozen() -> None:
    (
        attribution,
        workspace_scope,
        destination_scope,
        archive_input,
        destination_input,
        receipt_output,
        files_output,
        read_effect,
        write_effect,
        provider_boundary,
        executor_boundary,
        descriptor,
        snapshot,
    ) = _fixture()

    expected = {
        "attribution": "291f2b6107d7a42a6bedd754f5fd61eb2e497afc5ade3a6769c6bf8bc3b44a97",
        "workspace_scope": "a7074b81b712e1cabc71df4566736d1f84f987657ba25ea896aaf83e97a42658",
        "destination_scope": "d02b5e5077cb7bf99b2930f11c2cdaa488de4f07b758658bc2f09b631ad00204",
        "archive_input": "70a735edd257c8d62278b3916f92d5ae539826dd2ac42defcd9d7f95aca40cd7",
        "destination_input": "40577ac9e154db239261726a3361575e20e14c07956a90307d8458830b61fa6d",
        "receipt_output": "8624907ca5470a94ab5b26ee046df6de13626523f01b9ec54a188c8c8c70ee06",
        "files_output": "ade720e2a160cccdbfb692519a458d62321b36ff788dedb10a614b44aa344fbb",
        "read_effect": "c61b83c7e431eb9f18dd4d6e8305e7899e153cfddce6cb80bacc4aa08248f4ef",
        "write_effect": "640b4411a8aa569e2d55cd1c81cffd3fbcfc82cfcf9ba46ef8326033f4991d5d",
        "provider_boundary": "99fbb17e0d744569599b26102c5b6b4d5785c2380c6402f70f0c68f338667a80",
        "executor_boundary": "7f0c74f4aa6e249e9cc587d38687b7a59dd5be5d68d4907a15b6b88cd12c8ba3",
        "descriptor": "65e8db5cfdcc8475f8765023e8fda873cc763d5d3c86db18862c266bac4b2e74",
        "snapshot": "7c0e6629db0588c1d65d0c07b653f14b232d84f0cd29bd0ca974df753b132468",
    }
    actual = {
        "attribution": attribution.identity.digest,
        "workspace_scope": workspace_scope.identity.digest,
        "destination_scope": destination_scope.identity.digest,
        "archive_input": archive_input.identity.digest,
        "destination_input": destination_input.identity.digest,
        "receipt_output": receipt_output.identity.digest,
        "files_output": files_output.identity.digest,
        "read_effect": read_effect.identity.digest,
        "write_effect": write_effect.identity.digest,
        "provider_boundary": provider_boundary.identity.digest,
        "executor_boundary": executor_boundary.identity.digest,
        "descriptor": descriptor.identity.digest,
        "snapshot": snapshot.identity.digest,
    }

    assert actual == expected


def test_m16a_golden_descriptor_and_snapshot_round_trip_preserve_identity() -> None:
    *_, descriptor, snapshot = _fixture()

    decoded_descriptor = CapabilityDescriptor.from_json_bytes(
        descriptor.canonical_bytes()
    )
    decoded_snapshot = CapabilityCatalogSnapshot.from_json_bytes(
        snapshot.canonical_bytes()
    )

    assert decoded_descriptor == descriptor
    assert decoded_descriptor.identity == descriptor.identity
    assert decoded_snapshot == snapshot
    assert decoded_snapshot.identity == snapshot.identity
