from typing import Any

from ..utils import truncate_assets

from ..providers import get_provider
from ..providers.retry import with_retry

URL_PROVIDERS = ["urlscan", "wayback", "otx"]


def register_url_tools(mcp, storage, config):
    @mcp.tool()
    async def recon_urls(
        target: str,
        sources: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Discover historical URLs for a target."""
        sources = sources or URL_PROVIDERS
        options = options or {}
        assets: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []

        for name in sources:
            adapter = get_provider(name)
            if adapter is None:
                continue
            try:
                raw_items = await with_retry(adapter.query, target, options)
                assets.extend(adapter.normalize(raw_items))
            except Exception as exc:  # pragma: no cover - network error path
                errors.append({"provider": name, "error": str(exc)})

        unique = {asset["id"]: asset for asset in assets if asset.get("id")}
        result = [
            asset for asset in unique.values()
            if asset.get("type") in ("url", "domain")
        ]
        storage.save_assets(result)

        return {
            "status": "ok",
            "target": target,
            "sources": sources,
            "assets": result,
            "errors": errors,
        }
