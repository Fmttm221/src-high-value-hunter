import hashlib
from typing import Any

import httpx

from .base import Provider


class UrlscanProvider(Provider):
    name = "urlscan"
    asset_types = ["domain", "url", "ip"]
    requires_key = False
    passive = True

    async def query(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        url = "https://urlscan.io/api/v1/search/"
        params = {"q": f"domain:{query}", "size": 100}
        headers: dict[str, str] = {}
        if options and options.get("api_key"):
            headers["api-key"] = str(options["api_key"])

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                return data.get("results", []) or []
            return []

    def normalize(self, raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        assets: list[dict[str, Any]] = []
        seen: set[str] = set()

        for item in raw_items:
            page = item.get("page", {}) or {}
            candidates = [
                (page.get("domain"), "domain"),
                (page.get("url"), "url"),
                (page.get("ip"), "ip"),
            ]
            for value, typ in candidates:
                if not value:
                    continue
                value = str(value).strip()
                key = f"{typ}:{value}"
                if key in seen:
                    continue
                seen.add(key)
                asset_id = hashlib.sha256(key.encode("utf-8")).hexdigest()
                asset: dict[str, Any] = {
                    "id": asset_id,
                    "type": typ,
                    "source": self.name,
                    "extra": item,
                }
                if typ == "domain":
                    asset["host"] = value.lower()
                elif typ == "url":
                    asset["url"] = value
                elif typ == "ip":
                    asset["ip"] = value
                assets.append(asset)

        return assets
