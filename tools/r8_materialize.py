from __future__ import annotations

from pathlib import Path
import json
import os
import urllib.request


binding_path = Path("src/intent_resolution_runtime/binding.py")
text = binding_path.read_text(encoding="utf-8")
text = text.replace("from datetime import date\n", "")
text = text.replace("from fractions import Fraction\n", "")
text = text.replace(
    '    r"^(?P<year>\\d{4})-(?P<month>\\d{2})-(?P<day>\\d{2})T"\n'
    '    r"(?P<hour>\\d{2}):(?P<minute>\\d{2}):(?P<second>\\d{2})"\n'
    '    r"(?P<fraction>\\.\\d+)?(?P<zone>Z|[+-]\\d{2}:\\d{2})$"\n',
    '    r"^(?P<year>\\d{4})-(?P<month>\\d{2})-(?P<day>\\d{2})[Tt]"\n'
    '    r"(?P<hour>\\d{2}):(?P<minute>\\d{2}):(?P<second>\\d{2})"\n'
    '    r"(?P<fraction>\\.\\d+)?(?P<zone>[Zz]|[+-]\\d{2}:\\d{2})$"\n',
)

old_parser = '''def _parse_rfc3339(value: str, *, field: str) -> Fraction:
    match = _RFC3339_PATTERN.fullmatch(value)
    if match is None:
        raise ValidationError(f"{field} must be an RFC3339 timestamp with an explicit known offset")

    year = int(match.group("year"))
    month = int(match.group("month"))
    day = int(match.group("day"))
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    second = int(match.group("second"))
    fraction = match.group("fraction")
    zone = match.group("zone")

    if hour > 23 or minute > 59:
        raise ValidationError(f"{field} has an invalid clock time")
    if second > 59:
        raise ValidationError(f"{field} leap-second notation is not supported by M1.4 v1")
    try:
        calendar_day = date(year, month, day)
    except ValueError as exc:
        raise ValidationError(f"{field} has an invalid calendar date") from exc

    if zone == "-00:00":
        raise ValidationError(f"{field} uses RFC3339 unknown-offset form -00:00")
    if zone == "Z":
        offset_seconds = 0
    else:
        sign = 1 if zone[0] == "+" else -1
        offset_hour = int(zone[1:3])
        offset_minute = int(zone[4:6])
        if offset_hour > 23 or offset_minute > 59:
            raise ValidationError(f"{field} has an invalid timezone offset")
        offset_seconds = sign * (offset_hour * 3600 + offset_minute * 60)

    whole_seconds = (
        calendar_day.toordinal() * 86400
        + hour * 3600
        + minute * 60
        + second
        - offset_seconds
    )
    instant = Fraction(whole_seconds, 1)
    if fraction is not None:
        digits = fraction[1:]
        instant += Fraction(int(digits), 10 ** len(digits))
    return instant
'''
new_parser = '''def _is_gregorian_leap_year(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _days_from_civil(year: int, month: int, day: int) -> int:
    if not 1 <= month <= 12:
        raise ValueError("invalid month")
    month_lengths = (
        31,
        29 if _is_gregorian_leap_year(year) else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    )
    if not 1 <= day <= month_lengths[month - 1]:
        raise ValueError("invalid day")

    adjusted_year = year - (1 if month <= 2 else 0)
    era = adjusted_year // 400
    year_of_era = adjusted_year - era * 400
    adjusted_month = month + (-3 if month > 2 else 9)
    day_of_year = (153 * adjusted_month + 2) // 5 + day - 1
    day_of_era = year_of_era * 365 + year_of_era // 4 - year_of_era // 100 + day_of_year
    return era * 146097 + day_of_era


def _parse_rfc3339(value: str, *, field: str) -> tuple[int, str]:
    match = _RFC3339_PATTERN.fullmatch(value)
    if match is None:
        raise ValidationError(f"{field} must be an RFC3339 timestamp with an explicit known offset")

    year = int(match.group("year"))
    month = int(match.group("month"))
    day = int(match.group("day"))
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    second = int(match.group("second"))
    fraction = match.group("fraction")
    zone = match.group("zone")

    if hour > 23 or minute > 59:
        raise ValidationError(f"{field} has an invalid clock time")
    if second > 59:
        raise ValidationError(f"{field} leap-second notation is not supported by M1.4 v1")
    try:
        civil_day = _days_from_civil(year, month, day)
    except ValueError as exc:
        raise ValidationError(f"{field} has an invalid calendar date") from exc

    if zone == "-00:00":
        raise ValidationError(f"{field} uses RFC3339 unknown-offset form -00:00")
    if zone in ("Z", "z"):
        offset_seconds = 0
    else:
        sign = 1 if zone[0] == "+" else -1
        offset_hour = int(zone[1:3])
        offset_minute = int(zone[4:6])
        if offset_hour > 23 or offset_minute > 59:
            raise ValidationError(f"{field} has an invalid timezone offset")
        offset_seconds = sign * (offset_hour * 3600 + offset_minute * 60)

    whole_seconds = civil_day * 86400 + hour * 3600 + minute * 60 + second - offset_seconds
    fraction_digits = "" if fraction is None else fraction[1:].rstrip("0")
    return whole_seconds, fraction_digits
'''
if old_parser not in text:
    raise SystemExit("expected RFC3339 parser block not found")
text = text.replace(old_parser, new_parser)

old_validation = '''        if self.mode in (BindingSelectionMode.MAX_ATTRIBUTE, BindingSelectionMode.MIN_ATTRIBUTE):
            if len(self.selector_attributes) != 1 or len(self.selector_kinds) != 1:
                raise ValidationError(
                    "max_attribute/min_attribute selection requires exactly one selector attribute and kind"
                )
            if self.interchangeable_choice is not InterchangeableChoicePolicy.NONE:
                raise ValidationError("extremum selection cannot define an interchangeable choice policy")
'''
new_validation = '''        if self.mode in (BindingSelectionMode.MAX_ATTRIBUTE, BindingSelectionMode.MIN_ATTRIBUTE):
            if len(self.selector_attributes) != 1 or len(self.selector_kinds) != 1:
                raise ValidationError(
                    "max_attribute/min_attribute selection requires exactly one selector attribute and kind"
                )
            if self.selector_kinds[0] is not BindingAttributeKind.RFC3339_TIMESTAMP:
                raise ValidationError(
                    "max_attribute/min_attribute selection requires rfc3339_timestamp selector kind in M1.4 v1"
                )
            if self.interchangeable_choice is not InterchangeableChoicePolicy.NONE:
                raise ValidationError("extremum selection cannot define an interchangeable choice policy")
'''
if old_validation not in text:
    raise SystemExit("expected extremum policy block not found")
text = text.replace(old_validation, new_validation)

old_compare = '''def _compare_attribute(attribute: BindingAttribute) -> str | Fraction:
    if attribute.kind is BindingAttributeKind.TEXT:
        return attribute.value
    if attribute.kind is BindingAttributeKind.RFC3339_TIMESTAMP:
        return _parse_rfc3339(attribute.value, field=f"BindingAttribute[{attribute.name}]")
    raise AssertionError("unsupported BindingAttributeKind")
'''
new_compare = '''def _compare_attribute(attribute: BindingAttribute) -> tuple[int, str]:
    if attribute.kind is BindingAttributeKind.RFC3339_TIMESTAMP:
        return _parse_rfc3339(attribute.value, field=f"BindingAttribute[{attribute.name}]")
    raise AssertionError("M1.4 v1 extremum comparison supports RFC3339 timestamps only")
'''
if old_compare not in text:
    raise SystemExit("expected comparator block not found")
text = text.replace(old_compare, new_compare)
text = text.replace(
    "        ranked: list[tuple[str | Fraction, BindingInput]] = []\n",
    "        ranked: list[tuple[tuple[int, str], BindingInput]] = []\n",
)
binding_path.write_text(text, encoding="utf-8")

Path("tests/test_m1_4_rfc3339_comparator_hardening.py").write_text('''from __future__ import annotations

import pytest

from intent_resolution_runtime import (
    BindingAttribution,
    BindingAttribute,
    BindingAttributeKind,
    BindingInput,
    BindingInputRole,
    BindingIssue,
    BindingIssueKind,
    BindingRule,
    BindingSelectionMode,
    BindingSelectionPolicy,
    RecordIdentity,
    SourceAttribution,
    StableRef,
    SymbolicReference,
    ValidationError,
    evaluate_binding,
)

RESOLVED = RecordIdentity("sha256", "1" * 64)
SOURCE = RecordIdentity("sha256", "2" * 64)
SELECTION_SCOPE = "scope:timestamps"
SOURCE_REF = StableRef("host.source", "rfc3339-hardening")


def _ref(namespace: str, value: str) -> StableRef:
    return StableRef(namespace, value)


def _input(name: str, timestamp: str) -> BindingInput:
    return BindingInput(
        resolved_intent_identity=RESOLVED,
        input_ref=_ref("irr.binding_input", name),
        attribution=SourceAttribution(source_ref=SOURCE_REF, source_event_ref=_ref("host.event", name)),
        role=BindingInputRole.PLAN_LOCAL_OUTPUT,
        source_identity=SOURCE,
        semantic_type="test.value",
        value=name,
        selection_scope=SELECTION_SCOPE,
        value_scope=f"value:{name}",
        attributes=(BindingAttribute(name="timestamp", kind=BindingAttributeKind.RFC3339_TIMESTAMP, value=timestamp),),
    )


def _rule() -> BindingRule:
    symbolic = SymbolicReference(
        resolved_intent_identity=RESOLVED,
        slot_ref=_ref("irr.slot", "selected"),
        semantic_type="test.value",
        selection_scope=SELECTION_SCOPE,
        description="Select the exact latest timestamp.",
    )
    return BindingRule(
        resolved_intent_identity=RESOLVED,
        rule_ref=_ref("irr.binding_rule", "latest"),
        symbolic_reference=symbolic,
        allowed_input_roles=(BindingInputRole.PLAN_LOCAL_OUTPUT,),
        allowed_source_refs=(SOURCE_REF,),
        allowed_source_identities=(SOURCE,),
        input_semantic_type="test.value",
        required_selection_scope=SELECTION_SCOPE,
        constraints=(),
        selection_policy=BindingSelectionPolicy(
            mode=BindingSelectionMode.MAX_ATTRIBUTE,
            selector_attributes=("timestamp",),
            selector_kinds=(BindingAttributeKind.RFC3339_TIMESTAMP,),
        ),
        description="Choose the unique latest exact RFC3339 instant.",
    )


def _attribution() -> BindingAttribution:
    return BindingAttribution(evaluator_ref=_ref("irr.evaluator", "binding-v1"), binding_event_ref=_ref("irr.event", "r8"))


def test_arbitrary_fractional_precision_does_not_depend_on_decimal_to_int_conversion() -> None:
    prefix = "0" * 5000
    older = _input("older", f"2026-08-30T12:00:00.{prefix}1Z")
    newer = _input("newer", f"2026-08-30T12:00:00.{prefix}2Z")
    result = evaluate_binding(_rule(), (newer, older), attribution=_attribution())
    assert getattr(result, "value", None) == "newer"


def test_year_zero_and_lowercase_rfc3339_forms_compare_as_exact_instants() -> None:
    first = _input("first", "0000-01-01t00:00:00z")
    second = _input("second", "0000-01-01T01:00:00+01:00")
    result = evaluate_binding(_rule(), (first, second), attribution=_attribution())
    assert type(result) is BindingIssue
    assert result.kind is BindingIssueKind.TIE


@pytest.mark.parametrize("mode", [BindingSelectionMode.MAX_ATTRIBUTE, BindingSelectionMode.MIN_ATTRIBUTE])
def test_text_extrema_are_not_admitted_without_an_explicit_text_ordering_contract(mode: BindingSelectionMode) -> None:
    with pytest.raises(ValidationError, match="rfc3339_timestamp selector kind"):
        BindingSelectionPolicy(mode=mode, selector_attributes=("name",), selector_kinds=(BindingAttributeKind.TEXT,))


def test_fractional_trailing_zero_forms_compare_as_the_same_instant() -> None:
    first = _input("first", "2026-08-30T12:00:00.1Z")
    second = _input("second", "2026-08-30t12:00:00.1000z")
    result = evaluate_binding(_rule(), (first, second), attribution=_attribution())
    assert type(result) is BindingIssue
    assert result.kind is BindingIssueKind.TIE
''', encoding="utf-8")

doc_path = Path("docs/m1_4_binding_ir.md")
doc = doc_path.read_text(encoding="utf-8")
doc = doc.replace(
    "For `rfc3339_timestamp`, comparison preserves **all supplied fractional-second digits**. It does not round/truncate to Python microseconds.\n",
    "For `rfc3339_timestamp`, comparison preserves **all supplied fractional-second digits** without converting the complete fractional field to a bounded implementation integer. It does not round/truncate to Python microseconds and does not impose an implementation-specific fractional digit ceiling.\n",
)
doc = doc.replace(
    "No ambient timezone or wall clock is consulted.\n",
    "RFC3339's lowercase `t` and `z` forms are accepted as equivalent syntax. The four-digit RFC3339 year domain includes year `0000`; instant comparison therefore uses explicit proleptic-Gregorian civil-date arithmetic rather than a host datetime type whose year domain starts at 1.\n\nNo ambient timezone or wall clock is consulted.\n",
)
doc = doc.replace(
    "For `max_attribute` / `min_attribute`, both selector name and selector semantic kind are frozen before BindingInput arrives.\n",
    "For `max_attribute` / `min_attribute`, both selector name and selector semantic kind are frozen before BindingInput arrives. M1.4 v1 admits extrema only for `rfc3339_timestamp`; `text` remains equality-comparable but has no implicit cross-language ordering contract. A future text-order comparator must be named and frozen explicitly rather than inheriting a host language's string ordering.\n",
)
doc = doc.replace(
    "RFC3339 comparison preserves arbitrary fractional precision\n",
    "RFC3339 comparison preserves arbitrary fractional precision without host integer conversion limits\nRFC3339 year 0000 and lowercase t/z forms remain inside the admitted comparator domain\ntext extrema fail closed until an explicit text-order comparator is admitted\n",
)
doc_path.write_text(doc, encoding="utf-8")

token = os.environ["GH_TOKEN"]
repo = os.environ["REPO"]
api = f"https://api.github.com/repos/{repo}"


def request(method: str, url: str, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urllib.request.urlopen(req) as response:
        return json.load(response)


head = os.environ["GITHUB_SHA"]
base_commit = request("GET", f"{api}/git/commits/{head}")
entries = []
for path in (
    "src/intent_resolution_runtime/binding.py",
    "tests/test_m1_4_rfc3339_comparator_hardening.py",
    "docs/m1_4_binding_ir.md",
):
    blob = request("POST", f"{api}/git/blobs", {"content": Path(path).read_text(encoding="utf-8"), "encoding": "utf-8"})
    entries.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
for path in (
    ".github/workflows/r8-materialize.yml",
    ".github/workflows/r8-materialize-fix.yml",
    "tools/r8_materialize.py",
):
    entries.append({"path": path, "mode": "100644", "type": "blob", "sha": None})
tree = request("POST", f"{api}/git/trees", {"base_tree": base_commit["tree"]["sha"], "tree": entries})
commit = request("POST", f"{api}/git/commits", {
    "message": "M1.4 review hardening: close RFC3339 comparator semantics",
    "tree": tree["sha"],
    "parents": [head],
})
print(f"MATERIALIZED_COMMIT={commit['sha']}")
