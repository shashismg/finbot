"""Helpers shared by the tools."""
import json
import math
from typing import Any


def clean(value: Any, digits: int = 2) -> Any:
    """Round floats and turn NaN/inf into None so the JSON stays compact and valid."""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return round(value, digits)
    return value


def to_json(data: Any) -> str:
    if isinstance(data, dict):
        data = {k: clean(v) for k, v in data.items() if clean(v) is not None}
    return json.dumps(data, default=str, ensure_ascii=False)


def error(msg: str) -> str:
    return json.dumps({"error": msg})
