from typing import Any


def register_stats_tools(mcp, storage, config):
    @mcp.tool()
    def recon_stats() -> dict[str, Any]:
        """Return counts for core recon-hub tables."""
        tables = [
            "assets",
            "endpoints",
            "findings",
            "chains",
            "tasks",
            "throttle_profiles",
            "sessions",
            "accounts",
            "evidence_index",
        ]
        stats: dict[str, int] = {}
        for table in tables:
            row = storage.conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
            stats[table] = int(row["count"]) if row else 0
        return {"status": "ok", "stats": stats}
