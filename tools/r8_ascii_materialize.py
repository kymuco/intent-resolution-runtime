from __future__ import annotations

from pathlib import Path
import json
import os
import subprocess
import urllib.request


CANDIDATE = "503af09f9febad37d836fe5877cd714b11db320b"
subprocess.run(["git", "checkout", "--detach", CANDIDATE], check=True)

binding_path = Path("src/intent_resolution_runtime/binding.py")
text = binding_path.read_text(encoding="utf-8")
old_pattern = '''_RFC3339_PATTERN = re.compile(
    r"^(?P<year>\\d{4})-(?P<month>\\d{2})-(?P<day>\\d{2})[Tt]"
    r"(?P<hour>\\d{2}):(?P<minute>\\d{2}):(?P<second>\\d{2})"
    r"(?P<fraction>\\.\\d+)?(?P<zone>[Zz]|[+-]\\d{2}:\\d{2})$"
)
'''
new_pattern = '''_RFC3339_PATTERN = re.compile(
    r"^(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})[Tt]"
    r"(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})"
    r"(?P<fraction>\\.[0-9]+)?(?P<zone>[Zz]|[+-][0-9]{2}:[0-9]{2})$"
)
'''
if old_pattern not in text:
    raise SystemExit("expected candidate RFC3339 pattern not found")
binding_path.write_text(text.replace(old_pattern, new_pattern), encoding="utf-8")

test_path = Path("tests/test_m1_4_rfc3339_comparator_hardening.py")
tests = test_path.read_text(encoding="utf-8")
tests += '''


def test_non_ascii_decimal_digits_are_not_rfc3339_digits() -> None:
    with pytest.raises(ValidationError, match="RFC3339 timestamp"):
        BindingAttribute(
            name="timestamp",
            kind=BindingAttributeKind.RFC3339_TIMESTAMP,
            value="2026-08-30T12:00:00.١Z",
        )


def test_fractional_comparison_preserves_numeric_order_across_lengths() -> None:
    earlier = _input("earlier", "2026-08-30T12:00:00.19Z")
    later = _input("later", "2026-08-30T12:00:00.2Z")
    result = evaluate_binding(_rule(), (later, earlier), attribution=_attribution())
    assert getattr(result, "value", None) == "later"

    earlier_prefix = _input("earlier-prefix", "2026-08-30T12:00:00.1Z")
    later_prefix = _input("later-prefix", "2026-08-30T12:00:00.11Z")
    result = evaluate_binding(
        _rule(),
        (earlier_prefix, later_prefix),
        attribution=_attribution(),
    )
    assert getattr(result, "value", None) == "later-prefix"


def test_proleptic_gregorian_validation_covers_century_rules_and_year_zero() -> None:
    BindingAttribute(
        name="timestamp",
        kind=BindingAttributeKind.RFC3339_TIMESTAMP,
        value="0000-02-29T00:00:00Z",
    )
    BindingAttribute(
        name="timestamp",
        kind=BindingAttributeKind.RFC3339_TIMESTAMP,
        value="2000-02-29T00:00:00Z",
    )
    with pytest.raises(ValidationError, match="invalid calendar date"):
        BindingAttribute(
            name="timestamp",
            kind=BindingAttributeKind.RFC3339_TIMESTAMP,
            value="1900-02-29T00:00:00Z",
        )
'''
test_path.write_text(tests, encoding="utf-8")

doc_path = Path("docs/m1_4_binding_ir.md")
doc = doc_path.read_text(encoding="utf-8")
needle = "RFC3339's lowercase `t` and `z` forms are accepted as equivalent syntax. The four-digit RFC3339 year domain includes year `0000`; instant comparison therefore uses explicit proleptic-Gregorian civil-date arithmetic rather than a host datetime type whose year domain starts at 1.\n"
replacement = needle + "RFC3339 `DIGIT` is the ASCII range `0..9`; Unicode decimal characters accepted by some host regex engines are not admitted as timestamp digits.\n"
if needle not in doc:
    raise SystemExit("expected RFC3339 domain paragraph not found")
doc_path.write_text(doc.replace(needle, replacement), encoding="utf-8")

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


candidate_commit = request("GET", f"{api}/git/commits/{CANDIDATE}")
entries = []
for path in (
    "src/intent_resolution_runtime/binding.py",
    "tests/test_m1_4_rfc3339_comparator_hardening.py",
    "docs/m1_4_binding_ir.md",
):
    blob = request(
        "POST",
        f"{api}/git/blobs",
        {"content": Path(path).read_text(encoding="utf-8"), "encoding": "utf-8"},
    )
    entries.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})

tree = request(
    "POST",
    f"{api}/git/trees",
    {"base_tree": candidate_commit["tree"]["sha"], "tree": entries},
)
commit = request(
    "POST",
    f"{api}/git/commits",
    {
        "message": "M1.4 review hardening: close exact RFC3339 domain",
        "tree": tree["sha"],
        "parents": [os.environ["GITHUB_SHA"]],
    },
)
print(f"CORRECTED_R8_COMMIT={commit['sha']}")
