from __future__ import annotations

from dataclasses import dataclass

from .canonical import sha256_hex
from .errors import ValidationError


@dataclass(frozen=True, slots=True)
class RecordIdentity:
    """Content identity of one canonical IR record."""

    algorithm: str
    digest: str

    def __post_init__(self) -> None:
        if self.algorithm != "sha256":
            raise ValidationError("only sha256 record identity is supported in M1.1")
        if len(self.digest) != 64:
            raise ValidationError("sha256 digest must contain exactly 64 hexadecimal characters")
        try:
            int(self.digest, 16)
        except ValueError as exc:
            raise ValidationError("sha256 digest must be hexadecimal") from exc
        if self.digest != self.digest.lower():
            raise ValidationError("sha256 digest must use lowercase hexadecimal")

    def __str__(self) -> str:
        return f"{self.algorithm}:{self.digest}"


def identity_for_bytes(data: bytes | bytearray | memoryview) -> RecordIdentity:
    return RecordIdentity(algorithm="sha256", digest=sha256_hex(data))
