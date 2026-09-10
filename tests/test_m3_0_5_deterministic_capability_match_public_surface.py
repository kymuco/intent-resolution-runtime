from __future__ import annotations

import inspect

from intent_resolution_runtime import (
    IRR_CAPABILITY_MATCH_ENGINE_CONTRACT_VERSION,
    build_capability_match_evaluation,
    mechanical_capability_evaluator_ref,
    mechanical_capability_matcher_ref,
)


def test_m3_0_5_public_surface_is_narrow_and_top_level_exported() -> None:
    assert IRR_CAPABILITY_MATCH_ENGINE_CONTRACT_VERSION == "1"
    assert tuple(inspect.signature(build_capability_match_evaluation).parameters) == (
        "requirement",
        "catalog_snapshot",
        "evaluation_event_ref",
    )
    assert (
        tuple(inspect.signature(mechanical_capability_evaluator_ref).parameters) == ()
    )
    assert tuple(inspect.signature(mechanical_capability_matcher_ref).parameters) == ()

    parameters = inspect.signature(build_capability_match_evaluation).parameters
    for forbidden in (
        "descriptor",
        "provider",
        "discovery",
        "ranker",
        "selector",
        "governance",
        "authorization",
        "executor",
        "retry",
        "fallback",
    ):
        assert forbidden not in parameters
