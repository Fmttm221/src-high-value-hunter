import json
from pathlib import Path
from typing import Any


def _write_export(
    items: list[dict[str, Any]],
    base_dir: Path,
    format: str,
    name: str,
) -> dict[str, Any]:
    base_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_")) or "export"

    if format == "json":
        out = base_dir / f"{safe_name}.json"
        out.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        out = base_dir / f"{safe_name}.jsonl"
        with out.open("w", encoding="utf-8") as fh:
            for item in items:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    return {"status": "ok", "path": str(out), "count": len(items), "format": format}


def register_export_tools(mcp, storage, config):
    base_dir = Path(config.storage.jsonl_dir).parent / "exports"

    @mcp.tool()
    def recon_export(
        items: list[dict[str, Any]],
        format: str = "jsonl",
        name: str = "assets",
    ) -> dict[str, Any]:
        """Export a provided list to data/exports."""
        return _write_export(items, base_dir, format, name)

    @mcp.tool()
    def recon_export_db(
        collection: str = "assets",
        format: str = "jsonl",
        name: str = "",
        limit: int = 10000,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Export a collection from SQLite to data/exports."""
        if collection == "assets":
            items = storage.list_assets(limit=limit, offset=offset)
        elif collection == "endpoints":
            items = storage.list_endpoints(limit=limit, offset=offset)

        elif collection == "findings":
            items = storage.list_findings(limit=limit, offset=offset)
        elif collection == "chains":
            items = storage.list_chains(limit=limit, offset=offset)
        else:
            return {
                "status": "unknown_collection",
                "collection": collection,
                "allowed": ["assets", "endpoints", "findings", "chains"],
            }
        return _write_export(items, base_dir, format, name or collection)
