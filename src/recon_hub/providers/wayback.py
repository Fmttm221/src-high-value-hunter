import hashlib
from typing import Any
from urllib.parse import urlparse

import httpx

from .base import Provider


class WaybackProvider(Provider):
    name = "wayback"
    asset_types = ["url", "domain"]
    requires_key = False
    passive = True

    async def query(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> list[list[str]]:
        url = "http://web.archive.org/cdx/search/cdx"
        params = {
            "url": f"*.{query}/*",
            "output": "json",
            "collapse": "urlkey",
            "fl": "original",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and len(data) > 1:
                return data[1:]
            return []

    def normalize(self, raw_items: list[list[str]]) -> list[dict[str, Any]]:
        assets: list[dict[str, Any]] = []
        seen: set[str] = set()

        for row in raw_items:
            if not isinstance(row, list) or not row:
                continue
            original = str(row[0]).strip()
            if not original:
                continue
            parsed = urlparse(original)
            host = (parsed.hostname or "").lower()
            candidates = [
                (original, "url"),
                (host, "domain"),
            ]
            for value, typ in candidates:
                if not value:
                    continue
                key = f"{typ}:{value}"
                if key in seen:
                    continue
                seen.add(key)
                asset_id = hashlib.sha256(key.encode("utf-8")).hexdigest()
                asset: dict[str, Any] = {
                    "id": asset_id,
                    "type": typ,
                    "source": self.name,
                    "extra": {"original": original},
                }
                if typ == "url":
                    asset["url"] = value
                else:
                    asset["host"] = value
                assets.append(asset)

        return assets
