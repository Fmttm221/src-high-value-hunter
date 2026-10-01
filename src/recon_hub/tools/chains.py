from typing import Any


def register_chain_tools(mcp, storage, config):
    @mcp.tool()
    def recon_ingest_chains(chains: list[dict[str, Any]]) -> dict[str, Any]:
        """Store a list of vulnerability chains."""
        storage.save_chains(chains)
        return {"status": "ok", "count": len(chains), "chains": chains}

    @mcp.tool()
    def recon_list_chains(
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List vulnerability chains from SQLite."""
        chains = storage.list_chains(limit=limit, offset=offset)
        return {"status": "ok", "count": len(chains), "chains": chains}
