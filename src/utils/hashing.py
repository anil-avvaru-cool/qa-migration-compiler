import hashlib
import json
from typing import Any


def deterministic_hash(value: str, length: int = 12) -> str:
    """
    Deterministic hash for IDs.
    Stable across runs.
    """
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return digest[:length]


def hash_dict(data: dict, length: int = 16) -> str:
    """
    Deterministic structural hash of dictionary.
    Ensures sorted keys.
    """
    normalized = json.dumps(data, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return digest[:length]


def hash_object(obj: Any, length: int = 16) -> str:
    """
    Deterministic hash of arbitrary JSON-serializable object.
    """
    normalized = json.dumps(obj, sort_keys=True, default=str)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return digest[:length]
