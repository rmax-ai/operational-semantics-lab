"""Payload canonicalization and SHA-256 hashing.

Every payload-bound approval uses this deterministic hash function.
Canonical JSON encoding ensures same semantic payload always produces
the same hash regardless of dictionary key ordering.
"""

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any


def _default_serializer(obj: Any) -> Any:
    """Custom JSON serializer for domain types."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def compute_payload_hash(payload: dict[str, Any]) -> str:
    """Compute a deterministic SHA-256 hash of a payload dict.

    Uses canonical JSON encoding:
    - sorted keys at every level of nesting
    - UTF-8 encoding
    - no whitespace

    Returns the hex digest.
    """
    canonical = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=_default_serializer,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
