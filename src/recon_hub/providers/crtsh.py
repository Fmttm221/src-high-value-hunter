import hashlib
from typing import Any

import httpx

from .base import Provider


class CrtshProvider(Provider):
    name = "crtsh"
    asset_types = ["domain", "cert"]
    requires_key = False
    passive = True

    async def query(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        url = "https://crt.sh/"
        params = {"q": f"%.{query}", "output": "json"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                return data
            return []

    def normalize(self, raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        assets: list[dict[str, Any]] = []
        seen: set[str] = set()

        for item in raw_items:
            name_value = str(item.get("name_value", ""))
            for host in name_value.split("\n"):
                host = host.strip().lower()
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
                        "source": self.name,
                        "tags": [],
                        "extra": item,
                    }
                )

        return assets
