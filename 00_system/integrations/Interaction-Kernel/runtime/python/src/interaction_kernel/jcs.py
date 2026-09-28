from __future__ import annotations
import hashlib
import json
import math
from typing import Any

_MAX_IJSON_INTEGER = 9007199254740991

class JCSError(ValueError):
    pass

def _validate_string(value: str) -> None:
    for ch in value:
        if 0xD800 <= ord(ch) <= 0xDFFF:
            raise JCSError("lone surrogate is not valid I-JSON")

def _string(value: str) -> str:
    _validate_string(value)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

def _utf16_sort_key(value: str) -> bytes:
    _validate_string(value)
    return value.encode("utf-16-be")

def _number(value: int | float) -> str:
    if isinstance(value, bool):
        raise JCSError("boolean is not a number")
    if isinstance(value, int):
        if abs(value) > _MAX_IJSON_INTEGER:
            raise JCSError("integer is outside the interoperable I-JSON range")
        return str(value)
    if not math.isfinite(value):
        raise JCSError("non-finite number is not valid I-JSON")
    if value == 0.0:
        return "0"
    negative = value < 0
    number = -value if negative else value
    raw = repr(number).lower()
    if "e" in raw:
        mantissa, exponent_text = raw.split("e", 1)
        exponent = int(exponent_text)
    else:
        mantissa, exponent = raw, 0
    if "." in mantissa:
        before, after = mantissa.split(".", 1)
        digits = before + after
        decimal_pos = len(before) + exponent
    else:
        digits = mantissa
        decimal_pos = len(mantissa) + exponent
    while len(digits) > 1 and digits[0] == "0":
        digits = digits[1:]
        decimal_pos -= 1
    while len(digits) > 1 and digits[-1] == "0":
        digits = digits[:-1]
    scientific_exponent = decimal_pos - 1
    if 1e-6 <= number < 1e21:
        if decimal_pos <= 0:
            rendered = "0." + ("0" * (-decimal_pos)) + digits
        elif decimal_pos >= len(digits):
            rendered = digits + ("0" * (decimal_pos - len(digits)))
        else:
            rendered = digits[:decimal_pos] + "." + digits[decimal_pos:]
    else:
        rendered_mantissa = digits if len(digits) == 1 else digits[0] + "." + digits[1:]
        sign = "+" if scientific_exponent >= 0 else ""
        rendered = f"{rendered_mantissa}e{sign}{scientific_exponent}"
    return "-" + rendered if negative else rendered

def canonicalize(value: Any) -> str:
    """RFC 8785 JCS for I-JSON values.

    Numeric rendering follows ECMAScript Number serialization boundaries. Object
    property sorting uses UTF-16 code-unit ordering, as required by RFC 8785.
    """
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return _string(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _number(value)
    if isinstance(value, list):
        return "[" + ",".join(canonicalize(item) for item in value) + "]"
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise JCSError("JSON object keys must be strings")
        keys = sorted(value, key=_utf16_sort_key)
        return "{" + ",".join(_string(key) + ":" + canonicalize(value[key]) for key in keys) + "}"
    raise JCSError(f"unsupported JSON value type: {type(value).__name__}")

def sha256_jcs(value: Any) -> str:
    return hashlib.sha256(canonicalize(value).encode("utf-8")).hexdigest()
