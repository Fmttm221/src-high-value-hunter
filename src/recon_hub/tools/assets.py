import json
from typing import Any

from ..utils import truncate_asset, truncate_assets


def register_asset_tools(mcp, storage, config):
    @mcp.tool()
    def recon_list_assets(
        limit: int = 100,
        offset: int = 0,
        type: str | None = None,
        host_like: str | None = None,
    ) -> dict[str, Any]:
        """List assets from SQLite."""
        assets = storage.list_assets(limit=limit, offset=offset, type=type, host_like=host_like)
        return {"status": "ok", "count": len(assets), "assets": truncate_assets(assets)}

    @mcp.tool()
    def recon_get_asset(asset_id: str) -> dict[str, Any]:
        """Get a single asset by id."""
        row = storage.conn.execute(
            "SELECT * FROM assets WHERE id = ?", (asset_id,)
        ).fetchone()
        if row is None:
            return {"status": "not_found", "asset_id": asset_id}
        data = dict(row)
        for key in ("tags", "extra"):
            raw = data.get(key)
            if isinstance(raw, str) and raw:
                try:
                    data[key] = json.loads(raw)
                except json.JSONDecodeError:
                    pass
        data["alive"] = bool(data.get("alive"))
        return {"status": "ok", "asset": truncate_asset(data)}
