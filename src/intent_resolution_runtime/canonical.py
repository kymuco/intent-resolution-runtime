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


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    """Serialize a JSON-compatible mapping to deterministic UTF-8 bytes."""

    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise SerializationError("value is not canonical-JSON serializable") from exc
    return encoded.encode("utf-8")


def sha256_hex(data: bytes | bytearray | memoryview) -> str:
    return hashlib.sha256(bytes(data)).hexdigest()
