from typing import Any


def register_endpoint_tools(mcp, storage, config):
    @mcp.tool()
    def recon_ingest_endpoints(
        endpoints: list[dict[str, Any]],
        source: str = "import",
    ) -> dict[str, Any]:
        """Store endpoint models."""
        normalized: list[dict[str, Any]] = []
        for endpoint in endpoints:
            item = dict(endpoint)
            item.setdefault("method", "GET")
            item.setdefault("auth_state", "anonymous")
            item.setdefault("params", [])
            item.setdefault("monetization_tags", [])
            item.setdefault("extra", {})
            item["extra"].setdefault("source", source)
            normalized.append(item)

        storage.save_endpoints(normalized)
        return {"status": "ok", "count": len(normalized), "endpoints": normalized}

    @mcp.tool()
    def recon_list_endpoints(
        limit: int = 100,
        offset: int = 0,
        url_like: str | None = None,
    ) -> dict[str, Any]:
        """List endpoint models from SQLite."""
        endpoints = storage.list_endpoints(limit=limit, offset=offset, url_like=url_like)
        return {"status": "ok", "count": len(endpoints), "endpoints": endpoints}
