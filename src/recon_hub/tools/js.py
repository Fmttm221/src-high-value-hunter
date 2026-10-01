import hashlib
import re
from typing import Any

import httpx

from ..utils import truncate_assets

URL_RE = re.compile(r"https?://[^\s\"'<>]+")
PATH_RE = re.compile(r"[\"'](/[A-Za-z0-9_\-./?=&%#]+)[\"']")
SECRET_PATTERNS = {
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "google_api_key": re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    "slack_token": re.compile(r"xox[baprs]-[0-9A-Za-z\-]{10,}"),
}


def extract_from_text(text: str) -> dict[str, list[str]]:
    endpoints = sorted(set(URL_RE.findall(text)) | set(PATH_RE.findall(text)))
    secrets: list[str] = []
    for pattern in SECRET_PATTERNS.values():
        for match in pattern.finditer(text):
            secrets.append(match.group(0))
    return {"endpoints": endpoints, "secrets": sorted(set(secrets))}


async def run_js(
    storage,
    urls: list[str],
    depth: int = 1,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    options = options or {}
    results: list[dict[str, Any]] = []
    assets: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for url in urls:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                extracted = extract_from_text(resp.text)
                results.append(
                    {
                        "url": url,
                        "status_code": resp.status_code,
                        "endpoints": extracted["endpoints"],
                        "secrets": extracted["secrets"],
                    }
                )
                for endpoint in extracted["endpoints"]:
                    key = f"url:{endpoint}"
                    assets.append(
                        {
                            "id": hashlib.sha256(key.encode("utf-8")).hexdigest(),
                            "type": "url",
                            "subtype": "js_endpoint",
                            "url": endpoint,
                            "source": "recon_js",
                            "extra": {"from_js": url},
                        }
                    )
            except Exception as exc:  # pragma: no cover - network error path
                errors.append({"url": url, "error": str(exc)})

    storage.save_assets(assets)
    return {
        "status": "ok",
        "count": len(results),
        "results": results,
        "assets": truncate_assets(assets),
        "errors": errors,
    }


def register_js_tools(mcp, storage, config):
    @mcp.tool()
    async def recon_js(
        urls: list[str],
        depth: int = 1,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Fetch JavaScript URLs and extract endpoints / secrets."""
        return await run_js(storage, urls, depth=depth, options=options)
