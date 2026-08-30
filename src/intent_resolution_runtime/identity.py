from __future__ import annotations

import re
from dataclasses import dataclass

from .canonical import sha256_hex
from .errors import SerializationError, ValidationError


_SHA256_HEX = re.compile(r"[0-9a-f]{64}\Z", flags=re.ASCII)


@dataclass(frozen=True, slots=True)
class RecordIdentity:
    """Content identity of one canonical IR record."""

    algorithm: str
    digest: str

    def __post_init__(self) -> None:
        if self.algorithm != "sha256":
            raise ValidationError("only sha256 record identity is supported in M1")
        if not isinstance(self.digest, str) or _SHA256_HEX.fullmatch(self.digest) is None:
            raise ValidationError("sha256 digest must be exactly 64 lowercase ASCII hex characters")

    def __str__(self) -> str:
        return f"{self.algorithm}:{self.digest}"

    def to_primitive(self) -> dict[str, str]:
        return {"algorithm": self.algorithm, "digest": self.digest}

    @classmethod
    def from_primitive(cls, value: object, *, field: str) -> "RecordIdentity":
        if not isinstance(value, dict):
            raise SerializationError(f"{field} must be a JSON object")
        if set(value) != {"algorithm", "digest"}:
            raise SerializationError(f"{field} has invalid fields")
        algorithm = value["algorithm"]
        digest = value["digest"]
        if not isinstance(algorithm, str) or not isinstance(digest, str):
            raise SerializationError(f"{field} identity fields must be strings")
        try:
            return cls(algorithm=algorithm, digest=digest)
        except ValidationError as exc:
            raise SerializationError(f"invalid {field}") from exc


def identity_for_bytes(data: bytes | bytearray | memoryview) -> RecordIdentity:
    return RecordIdentity(algorithm="sha256", digest=sha256_hex(data))
