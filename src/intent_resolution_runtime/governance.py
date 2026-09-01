from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, cast

from .canonical import canonical_json_bytes, parse_json_object
from .errors import SerializationError, ValidationError
from .identity import RecordIdentity, identity_for_bytes
from .intent import StableRef
from .work_proposal import WorkProposal


def _reject_surrogates(value: str, *, field: str) -> None:
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise ValidationError(f"{field} must contain only Unicode scalar values")


def _require_string(value: object, *, field: str) -> str:
    if type(value) is not str:
        raise ValidationError(f"{field} must be a string")
    _reject_surrogates(value, field=field)
    return value


def _require_text(value: object, *, field: str) -> str:
    value = _require_string(value, field=field)
    if not value.strip():
        raise ValidationError(f"{field} must contain non-whitespace text")
    return value


def _require_token(value: object, *, field: str) -> str:
    value = _require_string(value, field=field)
    if not value:
        raise ValidationError(f"{field} must not be empty")
    if value != value.strip():
        raise ValidationError(f"{field} must not contain leading or trailing whitespace")
    return value


def _expect_object(value: object, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SerializationError(f"{field} must be a JSON object")
    return value


def _expect_array(value: object, *, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise SerializationError(f"{field} must be a JSON array")
    return value


def _expect_exact_keys(value: dict[str, Any], expected: set[str], *, field: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        detail: list[str] = []
        if missing:
            detail.append(f"missing={missing}")
        if extra:
            detail.append(f"extra={extra}")
        raise SerializationError(f"{field} has invalid fields ({', '.join(detail)})")


def _ref_key(value: StableRef) -> tuple[str, str]:
    return value.namespace, value.value


class _CanonicalGovernanceRecord:
    __slots__ = ()

    def to_primitive(self) -> dict[str, object]:
        raise NotImplementedError

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_primitive())

    @property
    def identity(self) -> RecordIdentity:
        return identity_for_bytes(self.canonical_bytes())


class GovernanceDecisionKind(str, Enum):
    AUTHORIZE = "authorize"
    DENY = "deny"
    CONSTRAIN = "constrain"
    REQUIRE_REVIEW = "require_review"


@dataclass(frozen=True, slots=True)
class GovernanceDecisionAttribution(_CanonicalGovernanceRecord):
    SCHEMA: ClassVar[str] = "irr.governance_decision_attribution.v1"

    governance_ref: StableRef
    decision_event_ref: StableRef
    authority_context_ref: StableRef
    authority_context_identity: RecordIdentity

    def __post_init__(self) -> None:
        if type(self.governance_ref) is not StableRef:
            raise ValidationError(
                "GovernanceDecisionAttribution.governance_ref must be a StableRef"
            )
        if type(self.decision_event_ref) is not StableRef:
            raise ValidationError(
                "GovernanceDecisionAttribution.decision_event_ref must be a StableRef"
            )
        if type(self.authority_context_ref) is not StableRef:
            raise ValidationError(
                "GovernanceDecisionAttribution.authority_context_ref must be a StableRef"
            )
        if type(self.authority_context_identity) is not RecordIdentity:
            raise ValidationError(
                "GovernanceDecisionAttribution.authority_context_identity must be a RecordIdentity"
            )

    def to_primitive(self) -> dict[str, object]:
        return {
            "authority_context_identity": self.authority_context_identity.to_primitive(),
            "authority_context_ref": self.authority_context_ref.to_primitive(),
            "decision_event_ref": self.decision_event_ref.to_primitive(),
            "governance_ref": self.governance_ref.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "GovernanceDecisionAttribution"
    ) -> "GovernanceDecisionAttribution":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {
                "schema",
                "governance_ref",
                "decision_event_ref",
                "authority_context_ref",
                "authority_context_identity",
            },
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                governance_ref=StableRef.from_primitive(
                    obj["governance_ref"], field=f"{field}.governance_ref"
                ),
                decision_event_ref=StableRef.from_primitive(
                    obj["decision_event_ref"], field=f"{field}.decision_event_ref"
                ),
                authority_context_ref=StableRef.from_primitive(
                    obj["authority_context_ref"], field=f"{field}.authority_context_ref"
                ),
                authority_context_identity=RecordIdentity.from_primitive(
                    obj["authority_context_identity"],
                    field=f"{field}.authority_context_identity",
                ),
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "GovernanceDecisionAttribution":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class GovernanceDirective(_CanonicalGovernanceRecord):
    SCHEMA: ClassVar[str] = "irr.governance_directive.v1"

    directive_ref: StableRef
    semantic_type: str
    scope: str
    statement: str

    def __post_init__(self) -> None:
        if type(self.directive_ref) is not StableRef:
            raise ValidationError("GovernanceDirective.directive_ref must be a StableRef")
        _require_token(self.semantic_type, field="GovernanceDirective.semantic_type")
        _require_text(self.scope, field="GovernanceDirective.scope")
        _require_text(self.statement, field="GovernanceDirective.statement")

    def to_primitive(self) -> dict[str, object]:
        return {
            "directive_ref": self.directive_ref.to_primitive(),
            "schema": self.SCHEMA,
            "scope": self.scope,
            "semantic_type": self.semantic_type,
            "statement": self.statement,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "GovernanceDirective"
    ) -> "GovernanceDirective":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "directive_ref", "semantic_type", "scope", "statement"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                directive_ref=StableRef.from_primitive(
                    obj["directive_ref"], field=f"{field}.directive_ref"
                ),
                semantic_type=obj["semantic_type"],
                scope=obj["scope"],
                statement=obj["statement"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "GovernanceDirective":
        return cls.from_primitive(parse_json_object(data))


def _normalize_step_refs(value: object, *, field: str) -> tuple[StableRef, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not value:
        raise ValidationError(f"{field} must not be empty")
    if not all(type(item) is StableRef for item in value):
        raise ValidationError(f"{field} must contain StableRef values")
    items = cast(tuple[StableRef, ...], value)
    if len(set(items)) != len(items):
        raise ValidationError(f"{field} must not contain duplicates")
    return tuple(sorted(items, key=_ref_key))


def _normalize_directives(
    value: object, *, field: str
) -> tuple[GovernanceDirective, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not all(type(item) is GovernanceDirective for item in value):
        raise ValidationError(f"{field} must contain GovernanceDirective values")
    items = cast(tuple[GovernanceDirective, ...], value)
    refs = [item.directive_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(f"{field} must not contain duplicate directive_ref values")
    return tuple(sorted(items, key=lambda item: _ref_key(item.directive_ref)))


@dataclass(frozen=True, slots=True)
class GovernanceDecisionComponent(_CanonicalGovernanceRecord):
    SCHEMA: ClassVar[str] = "irr.governance_decision_component.v1"

    component_ref: StableRef
    kind: GovernanceDecisionKind
    step_refs: tuple[StableRef, ...]
    directives: tuple[GovernanceDirective, ...]
    rationale: str

    def __post_init__(self) -> None:
        if type(self.component_ref) is not StableRef:
            raise ValidationError(
                "GovernanceDecisionComponent.component_ref must be a StableRef"
            )
        if type(self.kind) is not GovernanceDecisionKind:
            raise ValidationError(
                "GovernanceDecisionComponent.kind must be a GovernanceDecisionKind"
            )
        object.__setattr__(
            self,
            "step_refs",
            _normalize_step_refs(
                self.step_refs, field="GovernanceDecisionComponent.step_refs"
            ),
        )
        directives = _normalize_directives(
            self.directives, field="GovernanceDecisionComponent.directives"
        )
        if self.kind in (
            GovernanceDecisionKind.CONSTRAIN,
            GovernanceDecisionKind.REQUIRE_REVIEW,
        ) and not directives:
            raise ValidationError(
                "constrain and require_review components must contain at least one directive"
            )
        if self.kind is GovernanceDecisionKind.DENY and directives:
            raise ValidationError(
                "deny component directives are not admitted in v1; use rationale"
            )
        object.__setattr__(self, "directives", directives)
        _require_text(self.rationale, field="GovernanceDecisionComponent.rationale")

    def to_primitive(self) -> dict[str, object]:
        return {
            "component_ref": self.component_ref.to_primitive(),
            "directives": [item.to_primitive() for item in self.directives],
            "kind": self.kind.value,
            "rationale": self.rationale,
            "schema": self.SCHEMA,
            "step_refs": [item.to_primitive() for item in self.step_refs],
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "GovernanceDecisionComponent"
    ) -> "GovernanceDecisionComponent":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "component_ref", "kind", "step_refs", "directives", "rationale"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        if type(obj["kind"]) is not str:
            raise SerializationError(f"{field}.kind must be a string")
        try:
            kind = GovernanceDecisionKind(obj["kind"])
        except ValueError as exc:
            raise SerializationError(f"unsupported {field}.kind") from exc
        step_refs = _expect_array(obj["step_refs"], field=f"{field}.step_refs")
        directives = _expect_array(obj["directives"], field=f"{field}.directives")
        try:
            return cls(
                component_ref=StableRef.from_primitive(
                    obj["component_ref"], field=f"{field}.component_ref"
                ),
                kind=kind,
                step_refs=tuple(
                    StableRef.from_primitive(
                        item, field=f"{field}.step_refs[{index}]"
                    )
                    for index, item in enumerate(step_refs)
                ),
                directives=tuple(
                    GovernanceDirective.from_primitive(
                        item, field=f"{field}.directives[{index}]"
                    )
                    for index, item in enumerate(directives)
                ),
                rationale=obj["rationale"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "GovernanceDecisionComponent":
        return cls.from_primitive(parse_json_object(data))


def _normalize_components(
    value: object, *, field: str
) -> tuple[GovernanceDecisionComponent, ...]:
    if type(value) is not tuple:
        raise ValidationError(f"{field} must be a tuple")
    if not value:
        raise ValidationError(f"{field} must not be empty")
    if not all(type(item) is GovernanceDecisionComponent for item in value):
        raise ValidationError(f"{field} must contain GovernanceDecisionComponent values")
    items = cast(tuple[GovernanceDecisionComponent, ...], value)
    refs = [item.component_ref for item in items]
    if len(set(refs)) != len(refs):
        raise ValidationError(f"{field} must not contain duplicate component_ref values")
    return tuple(sorted(items, key=lambda item: _ref_key(item.component_ref)))


@dataclass(frozen=True, slots=True)
class GovernanceDecision(_CanonicalGovernanceRecord):
    SCHEMA: ClassVar[str] = "irr.governance_decision.v1"

    attribution: GovernanceDecisionAttribution
    proposal: WorkProposal
    components: tuple[GovernanceDecisionComponent, ...]
    description: str

    def __post_init__(self) -> None:
        if type(self.attribution) is not GovernanceDecisionAttribution:
            raise ValidationError(
                "GovernanceDecision.attribution must be a GovernanceDecisionAttribution"
            )
        if type(self.proposal) is not WorkProposal:
            raise ValidationError("GovernanceDecision.proposal must be a WorkProposal")
        if (
            self.attribution.decision_event_ref
            == self.proposal.attribution.proposal_event_ref
        ):
            raise ValidationError(
                "GovernanceDecision decision occurrence must differ from proposal occurrence"
            )

        components = _normalize_components(
            self.components, field="GovernanceDecision.components"
        )
        proposal_step_refs = {item.step_ref for item in self.proposal.proposed_steps}
        covered: set[StableRef] = set()
        for component in components:
            component_steps = set(component.step_refs)
            if not component_steps.issubset(proposal_step_refs):
                raise ValidationError(
                    "GovernanceDecision components may reference only proposed WorkSteps"
                )
            overlap = covered.intersection(component_steps)
            if overlap:
                raise ValidationError(
                    "GovernanceDecision v1 does not allow one WorkStep in multiple decision components"
                )
            covered.update(component_steps)
        object.__setattr__(self, "components", components)
        _require_text(self.description, field="GovernanceDecision.description")

    def to_primitive(self) -> dict[str, object]:
        return {
            "attribution": self.attribution.to_primitive(),
            "components": [item.to_primitive() for item in self.components],
            "description": self.description,
            "proposal": self.proposal.to_primitive(),
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "GovernanceDecision"
    ) -> "GovernanceDecision":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "attribution", "proposal", "components", "description"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        components = _expect_array(obj["components"], field=f"{field}.components")
        try:
            return cls(
                attribution=GovernanceDecisionAttribution.from_primitive(
                    obj["attribution"], field=f"{field}.attribution"
                ),
                proposal=WorkProposal.from_primitive(
                    obj["proposal"], field=f"{field}.proposal"
                ),
                components=tuple(
                    GovernanceDecisionComponent.from_primitive(
                        item, field=f"{field}.components[{index}]"
                    )
                    for index, item in enumerate(components)
                ),
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "GovernanceDecision":
        return cls.from_primitive(parse_json_object(data))


@dataclass(frozen=True, slots=True)
class Authorization(_CanonicalGovernanceRecord):
    SCHEMA: ClassVar[str] = "irr.authorization.v1"

    authorization_ref: StableRef
    decision: GovernanceDecision
    component_ref: StableRef
    description: str

    def __post_init__(self) -> None:
        if type(self.authorization_ref) is not StableRef:
            raise ValidationError("Authorization.authorization_ref must be a StableRef")
        if type(self.decision) is not GovernanceDecision:
            raise ValidationError("Authorization.decision must be a GovernanceDecision")
        if type(self.component_ref) is not StableRef:
            raise ValidationError("Authorization.component_ref must be a StableRef")
        component_map = {
            component.component_ref: component for component in self.decision.components
        }
        if self.component_ref not in component_map:
            raise ValidationError(
                "Authorization.component_ref must identify a component of the exact GovernanceDecision"
            )
        if component_map[self.component_ref].kind is not GovernanceDecisionKind.AUTHORIZE:
            raise ValidationError(
                "Authorization may materialize only an authorize GovernanceDecision component"
            )
        _require_text(self.description, field="Authorization.description")

    @property
    def component(self) -> GovernanceDecisionComponent:
        for component in self.decision.components:
            if component.component_ref == self.component_ref:
                return component
        raise AssertionError("validated Authorization lost its Governance component")

    @property
    def authorized_step_refs(self) -> tuple[StableRef, ...]:
        return self.component.step_refs

    @property
    def conditions(self) -> tuple[GovernanceDirective, ...]:
        return self.component.directives

    def to_primitive(self) -> dict[str, object]:
        return {
            "authorization_ref": self.authorization_ref.to_primitive(),
            "component_ref": self.component_ref.to_primitive(),
            "decision": self.decision.to_primitive(),
            "description": self.description,
            "schema": self.SCHEMA,
        }

    @classmethod
    def from_primitive(
        cls, value: object, *, field: str = "Authorization"
    ) -> "Authorization":
        obj = _expect_object(value, field=field)
        _expect_exact_keys(
            obj,
            {"schema", "authorization_ref", "decision", "component_ref", "description"},
            field=field,
        )
        if obj["schema"] != cls.SCHEMA:
            raise SerializationError(f"unsupported {field} schema: {obj['schema']!r}")
        try:
            return cls(
                authorization_ref=StableRef.from_primitive(
                    obj["authorization_ref"], field=f"{field}.authorization_ref"
                ),
                decision=GovernanceDecision.from_primitive(
                    obj["decision"], field=f"{field}.decision"
                ),
                component_ref=StableRef.from_primitive(
                    obj["component_ref"], field=f"{field}.component_ref"
                ),
                description=obj["description"],
            )
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc

    @classmethod
    def from_json_bytes(
        cls, data: bytes | bytearray | memoryview
    ) -> "Authorization":
        return cls.from_primitive(parse_json_object(data))
