from typing import Any

from ..utils import truncate_assets

from ..providers import get_provider
from ..providers.retry import with_retry

EXPAND_PROVIDERS = ["certspotter", "crtsh"]


def register_expand_tools(mcp, storage, config):
    @mcp.tool()
    async def recon_expand(
        target: str,
        modes: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Expand a target into domains/certs."""
        modes = modes or ["domain"]
        options = options or {}
        assets: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []

        for name in EXPAND_PROVIDERS:
            adapter = get_provider(name)
            if adapter is None:
                continue
            try:
                raw_items = await with_retry(adapter.query, target, options)
                assets.extend(adapter.normalize(raw_items))
            except Exception as exc:  # pragma: no cover - network error path
                errors.append({"provider": name, "error": str(exc)})

        unique = {asset["id"]: asset for asset in assets if asset.get("id")}
        result = list(unique.values())
        storage.save_assets(result)

        return {
            "status": "ok",
            "target": target,
            "modes": modes,
            "assets": result,
            "errors": errors,
        }
