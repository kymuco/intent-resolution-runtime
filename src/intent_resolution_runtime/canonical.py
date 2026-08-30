from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from .errors import SerializationError


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SerializationError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_nonfinite_constant(value: str) -> None:
    raise SerializationError(f"non-finite JSON number is not allowed: {value}")


def _require_unicode_scalars(value: str, *, field: str) -> None:
    for character in value:
        codepoint = ord(character)
        if 0xD800 <= codepoint <= 0xDFFF:
            raise SerializationError(f"{field} contains a Unicode surrogate code point")


def parse_json_object(data: bytes | bytearray | memoryview) -> dict[str, Any]:
    """Decode one UTF-8 JSON object while rejecting duplicate keys and NaN/Infinity."""
    try:
        text = bytes(data).decode("utf-8")
    except (TypeError, UnicodeDecodeError) as exc:
        raise SerializationError("canonical JSON input must be valid UTF-8 bytes") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_nonfinite_constant,
        )
    except SerializationError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SerializationError("invalid JSON object") from exc
    if not isinstance(value, dict):
        raise SerializationError("top-level canonical JSON value must be an object")
    return value


def _encode_string(value: str) -> str:
    _require_unicode_scalars(value, field="canonical string")
    encoded: list[str] = ['"']
    for character in value:
        codepoint = ord(character)
        if character == '"':
            encoded.append('\\"')
        elif character == "\\":
            encoded.append("\\\\")
        elif codepoint < 0x20:
            encoded.append(f"\\u{codepoint:04x}")
        else:
            encoded.append(character)
    encoded.append('"')
    return "".join(encoded)


def _encode_value(value: object) -> str:
    if isinstance(value, str):
        return _encode_string(value)
    if isinstance(value, Mapping):
        keys = list(value.keys())
        if not all(isinstance(key, str) for key in keys):
            raise SerializationError("canonical object keys must be strings")
        for key in keys:
            _require_unicode_scalars(key, field="canonical object key")
        return "{" + ",".join(
            f"{_encode_string(key)}:{_encode_value(value[key])}" for key in sorted(keys)
        ) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_encode_value(item) for item in value) + "]"
    raise SerializationError(
        "M1.2 canonical domain supports only objects, arrays, and Unicode scalar strings"
    )


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    """Serialize the M1 object/array/string canonical domain to deterministic UTF-8 bytes."""
    if not isinstance(value, Mapping):
        raise SerializationError("top-level canonical value must be an object")
    return _encode_value(value).encode("utf-8")


def sha256_hex(data: bytes | bytearray | memoryview) -> str:
    return hashlib.sha256(bytes(data)).hexdigest()
