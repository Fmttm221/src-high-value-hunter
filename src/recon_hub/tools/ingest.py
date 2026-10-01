import hashlib
from typing import Any

from ..utils import truncate_assets


def register_ingest_tools(mcp, storage, config):
    @mcp.tool()
    def recon_ingest_domains(
        domains: list[str],
        source: str = "import",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Normalize and store a list of domains/subdomains."""
        assets: list[dict[str, Any]] = []
        seen: set[str] = set()
        tags = tags or []

        for value in domains:
            host = str(value).strip().lower()
            if not host or host in seen:
                continue
            seen.add(host)
            asset_id = hashlib.sha256(f"domain:{host}".encode("utf-8")).hexdigest()
            assets.append(
                {
                    "id": asset_id,
                    "type": "domain",
                    "subtype": "subdomain",
                    "host": host,
                    "source": source,
                    "tags": list(tags),
                }
            )

        storage.save_assets(assets)
        return {
            "status": "ok",
            "count": len(assets),
            "assets": truncate_assets(assets),
        }

    @mcp.tool()
    def recon_ingest_assets(
        assets: list[dict[str, Any]],
        source: str = "import",
    ) -> dict[str, Any]:
        """Store a list of pre-normalized assets."""
        normalized: list[dict[str, Any]] = []
        for asset in assets:
            item = dict(asset)
            item.setdefault("source", source)
            if not item.get("id"):
                key = f"{item.get('type', 'unknown')}:{item.get('host') or item.get('url') or item.get('ip') or ''}"
                item["id"] = hashlib.sha256(key.encode("utf-8")).hexdigest()
            normalized.append(item)

        storage.save_assets(normalized)
        return {
            "status": "ok",
            "count": len(normalized),
            "assets": truncate_assets(normalized),
        }
