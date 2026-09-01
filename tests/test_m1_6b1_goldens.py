from __future__ import annotations

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
    StableRef,
    SymbolicReference,
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
    CapabilityRequestedScope,
    CapabilityRequestedScope,
    CapabilityRequestedEffect,
    CapabilityRequestedEffect,
    CapabilityExecutionBoundaryRequirement,
    CapabilityRequirement,
    CapabilityScopeMatch,
    CapabilityScopeMatch,
    CapabilityInputMatch,
    CapabilityInputMatch,
    CapabilityOutputMatch,
    CapabilityOutputMatch,
    CapabilityEffectMatch,
    CapabilityEffectMatch,
    CapabilityMatchAttribution,
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
    boundary_requirement = CapabilityExecutionBoundaryRequirement(
        CapabilityExecutionBoundaryKind.PROVIDER,
        _ref("irr.provider", "local-archive-adapter"),
        "Require the admitted local provider.",
    )
    requirement = CapabilityRequirement(
        plan,
        step_ref,
        req_workspace.scope_ref,
        (req_destination, req_workspace),
        (req_write, req_read),
        (boundary_requirement,),
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

    scope_workspace_match = CapabilityScopeMatch(
        req_workspace.scope_ref, cap_workspace.requirement_ref
    )
    scope_destination_match = CapabilityScopeMatch(
        req_destination.scope_ref, cap_destination.requirement_ref
    )
    input_archive_match = CapabilityInputMatch(
        "archive", cap_archive.input_ref, (req_workspace.scope_ref,)
    )
    input_destination_match = CapabilityInputMatch(
        "destination", cap_destination_input.input_ref, (req_destination.scope_ref,)
    )
    output_receipt_match = CapabilityOutputMatch(
        "receipt", cap_receipt.output_ref, (req_destination.scope_ref,)
    )
    output_files_match = CapabilityOutputMatch(
        "files", cap_files.output_ref, (req_destination.scope_ref,)
    )
    effect_read_match = CapabilityEffectMatch(req_read.effect_ref, cap_read.effect_ref)
    effect_write_match = CapabilityEffectMatch(req_write.effect_ref, cap_write.effect_ref)
    attribution = CapabilityMatchAttribution(
        _ref("irr.matcher", "semantic-match-v1"),
        _ref("irr.event", "match-001"),
    )
    match = CapabilityMatch(
        attribution,
        requirement,
        snapshot,
        descriptor.capability_ref,
        descriptor.identity,
        (scope_workspace_match, scope_destination_match),
        (input_archive_match, input_destination_match),
        (output_receipt_match, output_files_match),
        (effect_read_match, effect_write_match),
        "Exact admitted semantic capability match.",
    )

    return (
        req_workspace,
        req_destination,
        req_read,
        req_write,
        boundary_requirement,
        requirement,
        scope_workspace_match,
        scope_destination_match,
        input_archive_match,
        input_destination_match,
        output_receipt_match,
        output_files_match,
        effect_read_match,
        effect_write_match,
        attribution,
        match,
    )


def test_m16b1_capability_match_golden_digests_are_frozen() -> None:
    (
        req_workspace,
        req_destination,
        req_read,
        req_write,
        boundary_requirement,
        requirement,
        scope_workspace_match,
        scope_destination_match,
        input_archive_match,
        input_destination_match,
        output_receipt_match,
        output_files_match,
        effect_read_match,
        effect_write_match,
        attribution,
        match,
    ) = _fixture()

    expected = {
        "req_workspace": "bdebb0a9848606f367014d632b15b5c162c983601d7b04f167ad6122257a6917",
        "req_destination": "9b8966b9014bac9f3ab58161b15a6d0b0758517a7b3dbd0b505cab07e31409a0",
        "req_read": "5cdda1abe180c41fb2c11403bbe284facc37276c613a368cc0ca97d967b72d4f",
        "req_write": "41eda419a084b4af3120bb6dde3f66cc7b2f13a0e78e6d793ff3461ee94c01e9",
        "boundary_requirement": "c4617df4659c05408f1115e1318f379f328b81aee76aec5affdc7ab6efb74a3c",
        "requirement": "18371a898016175121bf14ba625a8c7dc74d5e0605e7d373cd692adc78baef9f",
        "scope_workspace_match": "89416ba26534db2b38b8cd8f9dfa677df71910819010acb0d418fb26f12369c1",
        "scope_destination_match": "ac6d2c050321b49063dc4378ee6d23e56a48ac78287aaacd83910c0e21bbec91",
        "input_archive_match": "cb85ce73c75b261ea8bdd99a9c1fdbbee2f579ebfa7912bc13cc2629d9432cde",
        "input_destination_match": "71c343fd408ad28f1119502d6bf475cc58720680776ff848a3aab3d0aef51e9d",
        "output_receipt_match": "bec887f9c75ed122900c0c336feb0dcc17eb13d83c840b512bca8c25c68af927",
        "output_files_match": "1ec8befe2e86c6eaa3af244564cc9cd1f2b4c1aaf973c34b4004e32a137a5d25",
        "effect_read_match": "6d74b1a3662046bbcb2c9eebfa5246d4d6a4957b326ea4f42c4fe2e735331fa3",
        "effect_write_match": "2a1fb075f50d67e1e7e365b0a037c4a44476438c1991e6b61b2691e8811bdf54",
        "attribution": "8432ce46901ccfee36857d750ef35fbddaad4ce07d7a3136a9e8da0ba0f26d4d",
        "match": "e9bb4ae9ca89df181c165881ca65d6acc9adc8cd75a91145992b54fd9ae7179c",
    }
    actual = {
        "req_workspace": req_workspace.identity.digest,
        "req_destination": req_destination.identity.digest,
        "req_read": req_read.identity.digest,
        "req_write": req_write.identity.digest,
        "boundary_requirement": boundary_requirement.identity.digest,
        "requirement": requirement.identity.digest,
        "scope_workspace_match": scope_workspace_match.identity.digest,
        "scope_destination_match": scope_destination_match.identity.digest,
        "input_archive_match": input_archive_match.identity.digest,
        "input_destination_match": input_destination_match.identity.digest,
        "output_receipt_match": output_receipt_match.identity.digest,
        "output_files_match": output_files_match.identity.digest,
        "effect_read_match": effect_read_match.identity.digest,
        "effect_write_match": effect_write_match.identity.digest,
        "attribution": attribution.identity.digest,
        "match": match.identity.digest,
    }
    assert actual == expected


def test_m16b1_golden_requirement_and_match_round_trip_preserve_identity() -> None:
    *_, requirement, _, _, _, _, _, _, _, _, attribution, match = _fixture()
    assert attribution.identity.digest == (
        "8432ce46901ccfee36857d750ef35fbddaad4ce07d7a3136a9e8da0ba0f26d4d"
    )

    decoded_requirement = CapabilityRequirement.from_json_bytes(
        requirement.canonical_bytes()
    )
    decoded_match = CapabilityMatch.from_json_bytes(match.canonical_bytes())

    assert decoded_requirement == requirement
    assert decoded_requirement.identity == requirement.identity
    assert decoded_match == match
    assert decoded_match.identity == match.identity
