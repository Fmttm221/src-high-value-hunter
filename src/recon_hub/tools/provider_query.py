from typing import Any

from ..providers import get_provider
from ..providers.retry import with_retry
from ..utils import truncate_assets


def _provider_options(config, name: str, options: dict[str, Any]) -> dict[str, Any]:
    out = dict(options)
    provider_config = config.providers.get(name)
    if provider_config:
        out.setdefault("api_key", provider_config.api_key)
        out.setdefault("api_id", provider_config.api_id)
        out.setdefault("api_secret", provider_config.api_secret)
    return out


def register_provider_tools(mcp, storage, config):
    @mcp.tool()
    async def recon_provider_query(
        provider: str,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Query a provider and return normalized assets."""
        adapter = get_provider(provider)
        if adapter is None:
            return {
                "provider": provider,
                "status": "unknown_provider",
                "query": query,
                "assets": [],
                "errors": [f"unknown provider: {provider}"],
            }

        provider_config = config.providers.get(provider)
        if provider_config and not provider_config.enabled:
            return {
                "provider": provider,
                "status": "disabled",
                "query": query,
                "assets": [],
                "errors": ["provider disabled in config"],
            }

        adapter_options = _provider_options(config, provider, options or {})

        try:
            raw_items = await with_retry(
                adapter.query,
                query,
                adapter_options,
                retries=3,
                base_delay=1.0,
            )
            assets = adapter.normalize(raw_items)
            storage.save_assets(assets)
            return {
                "provider": provider,
                "status": "ok",
                "query": query,
                "assets": truncate_assets(assets),
                "raw_count": len(raw_items),
                "errors": [],
            }
        except Exception as exc:  # pragma: no cover - network error path
            return {
                "provider": provider,
                "status": "error",
                "query": query,
                "assets": [],
                "errors": [str(exc)],
            }
