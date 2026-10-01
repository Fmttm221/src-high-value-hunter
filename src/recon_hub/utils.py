from typing import Any


def truncate_value(
    value: Any,
    max_str: int = 200,
    max_items: int = 10,
    depth: int = 0,
) -> Any:
    if depth > 3:
        return "..."
    if isinstance(value, str):
        if len(value) > max_str:
            return value[:max_str] + "...[truncated]"
        return value
    if isinstance(value, list):
        return [truncate_value(item, max_str, max_items, depth + 1) for item in value[:max_items]]
    if isinstance(value, dict):
        items = list(value.items())[:max_items]
        return {key: truncate_value(val, max_str, max_items, depth + 1) for key, val in items}
    return value


def truncate_asset(asset: dict[str, Any], max_str: int = 200) -> dict[str, Any]:
    out = dict(asset)
    if "extra" in out:
        out["extra"] = truncate_value(out["extra"], max_str=max_str)
    return out


def truncate_assets(assets: list[dict[str, Any]], max_str: int = 200) -> list[dict[str, Any]]:
    return [truncate_asset(asset, max_str=max_str) for asset in assets]
