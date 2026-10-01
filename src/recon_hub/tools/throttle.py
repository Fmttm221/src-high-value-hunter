from typing import Any


def register_throttle_tools(mcp, storage, config):
    @mcp.tool()
    def recon_throttle_get(host: str) -> dict[str, Any]:
        """Get throttle profile for a host."""
        profile = storage.get_throttle(host)
        if profile is None:
            return {"host": host, "status": "missing"}
        return {"host": host, "status": "ok", "profile": profile}

    @mcp.tool()
    def recon_throttle_update(host: str, profile: dict[str, Any]) -> dict[str, Any]:
        """Create or update throttle profile for a host."""
        profile = dict(profile or {})
        profile["host"] = host
        storage.save_throttle(profile)
        return {"host": host, "status": "saved"}
