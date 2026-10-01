from typing import Any

from ..utils import truncate_assets


def merge_assets(asset_sets: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for asset_set in asset_sets:
        for asset in asset_set:
            asset_id = asset.get("id")
            if not asset_id:
                continue
            if asset_id not in merged:
                merged[asset_id] = asset
            else:
                merged[asset_id].update(
                    {k: v for k, v in asset.items() if v not in (None, "", [])}
                )
    return list(merged.values())


def register_merge_tools(mcp, storage, config):
    @mcp.tool()
    def recon_merge(asset_sets: list[list[dict[str, Any]]]) -> dict[str, Any]:
        """Merge and deduplicate asset sets by id."""
        assets = merge_assets(asset_sets)
        storage.save_assets(assets)
        return {"status": "ok", "count": len(assets), "assets": truncate_assets(assets)}
