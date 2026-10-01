import hashlib
from typing import Any

import httpx

from .base import Provider


class OtxProvider(Provider):
    name = "otx"
    asset_types = ["domain", "ip"]
    requires_key = False
    passive = True

    async def query(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        url = f"https://otx.alienvault.com/api/v1/indicators/domain/{query}/passive_dns"
        headers: dict[str, str] = {}
        if options and options.get("api_key"):
            headers["X-OTX-API-KEY"] = str(options["api_key"])

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                return data.get("passive_dns", []) or []
            return []

    def normalize(self, raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        assets: list[dict[str, Any]] = []
        seen: set[str] = set()

        for item in raw_items:
            candidates = [
                (item.get("hostname"), "domain"),
                (item.get("address"), "ip"),
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
                else:
                    asset["ip"] = value
                assets.append(asset)

        return assets
