import hashlib
from typing import Any

import httpx

from ..utils import truncate_assets


async def run_code(
    storage,
    query: str,
    platforms: list[str] | None = None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    platforms = platforms or ["github"]
    options = options or {}
    assets: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    if "github" in platforms:
        token = options.get("token")
        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    "https://api.github.com/search/repositories",
                    params={"q": query, "per_page": 20},
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
                for item in data.get("items", []) or []:
                    html_url = item.get("html_url", "")
                    if not html_url:
                        continue
                    asset_id = hashlib.sha256(
                        f"repo:{html_url}".encode("utf-8")
                    ).hexdigest()
                    assets.append(
                        {
                            "id": asset_id,
                            "type": "repo",
                            "subtype": "github",
                            "url": html_url,
                            "source": "github",
                            "extra": {
                                "full_name": item.get("full_name"),
                                "description": item.get("description"),
                                "html_url": html_url,
                                "stargazers_count": item.get("stargazers_count"),
                                "language": item.get("language"),
                                "updated_at": item.get("updated_at"),
                            },
                        }
                    )
        except Exception as exc:  # pragma: no cover - network error path
            errors.append({"platform": "github", "error": str(exc)})

    storage.save_assets(assets)
    return {
        "status": "ok",
        "query": query,
        "platforms": platforms,
        "assets": truncate_assets(assets),
        "errors": errors,
    }


def register_code_tools(mcp, storage, config):
    @mcp.tool()
    async def recon_code(
        query: str,
        platforms: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Search GitHub repositories and return repo assets."""
        return await run_code(storage, query, platforms=platforms, options=options)
