"""Fixed-work JSON parsing budgets for untrusted evidence, before model validation."""

import json
import math

from orbitiq.replay_contract import (
    MAX_COLLECTION_ITEMS,
    MAX_FILE_BYTES,
    MAX_JSON_DEPTH,
    MAX_JSON_NODES,
    MAX_STRING_LENGTH,
    BundleError,
)


def decoded(data, *, manifest=False):
    if len(data) > MAX_FILE_BYTES:
        raise BundleError("JSON exceeds byte budget", "json_limit")
    text = data.decode("utf-8") if isinstance(data, bytes) else data
    depth, quoted, escaped = 0, False, False
    # Reject deep nesting before the JSON decoder allocates nested structures.
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > (12 if manifest else MAX_JSON_DEPTH):
                raise BundleError("JSON nesting exceeds budget", "json_limit")
        elif char in "]}":
            depth -= 1

    def pairs(items):
        if len(items) > MAX_COLLECTION_ITEMS:
            raise BundleError("JSON object exceeds budget", "json_limit")
        result = {}
        for key, value in items:
            if key in result:
                raise BundleError("Duplicate JSON field", "duplicate_json_field")
            result[key] = value
        return result

    def constant(_):
        raise BundleError("Nonfinite JSON number", "json_nonfinite")

    def number(value):
        result = float(value)
        if not math.isfinite(result):
            raise BundleError("Nonfinite JSON number", "json_nonfinite")
        return result

    value = json.loads(
        text, object_pairs_hook=pairs, parse_constant=constant, parse_float=number
    )
    pending, nodes = [value], 0
    while pending:
        current = pending.pop()
        nodes += 1
        if nodes > (4096 if manifest else MAX_JSON_NODES):
            raise BundleError("JSON node budget exceeded", "json_limit")
        if isinstance(current, (dict, list)):
            if len(current) > MAX_COLLECTION_ITEMS:
                raise BundleError("JSON collection exceeds budget", "json_limit")
            pending.extend(current.values() if isinstance(current, dict) else current)
            if isinstance(current, dict):
                pending.extend(current.keys())
        elif isinstance(current, str) and len(current) > MAX_STRING_LENGTH:
            raise BundleError("JSON string exceeds budget", "json_limit")
    return value
