import base64
import hashlib
from typing import Any

import httpx

from .base import Provider


def _asset(typ: str, value: str, source: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    key = f"{typ}:{value}"
    asset: dict[str, Any] = {
        "id": hashlib.sha256(key.encode("utf-8")).hexdigest(),
        "type": typ,
        "source": source,
        "extra": extra or {},
    }
    if typ == "domain":
        asset["host"] = value.lower()
    elif typ == "ip":
        asset["ip"] = value
    elif typ == "url":
        asset["url"] = value
    return asset


class ShodanProvider(Provider):
    name = "shodan"
    asset_types = ["domain", "ip"]
    requires_key = True
    passive = True

    async def query(self, query: str, options: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        options = options or {}
        key = options.get("api_key")
        if not key:
            raise ValueError("shodan api_key required")

        async with httpx.AsyncClient(timeout=30.0) as client:
            if "." in query and not query.replace(".", "").isdigit():
                resp = await client.get(
                    f"https://api.shodan.io/dns/domain/{query}",
                    params={"key": key},
                )
                resp.raise_for_status()
                data = resp.json()
                return [data] if isinstance(data, dict) else []

            resp = await client.get(
                "https://api.shodan.io/shodan/host/search",
                params={"key": key, "query": query},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("matches", []) if isinstance(data, dict) else []

    def normalize(self, raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        assets: list[dict[str, Any]] = []
        seen: set[str] = set()

        for item in raw_items:
            subdomains = item.get("subdomains", []) or []
            for sub in subdomains:
                host = f"{sub}.{item.get('domain', '')}".strip(".")
                key = f"domain:{host}"
                if host and key not in seen:
                    seen.add(key)
                    assets.append(_asset("domain", host, self.name, item))

            ip = item.get("ip_str") or item.get("ip")
            if ip:
                key = f"ip:{ip}"
                if key not in seen:
                    seen.add(key)
                    assets.append(_asset("ip", str(ip), self.name, item))

            for host in item.get("hostnames", []) or []:
                key = f"domain:{host}"
                if host and key not in seen:
                    seen.add(key)
                    assets.append(_asset("domain", str(host), self.name, item))

        return assets


class CensysProvider(Provider):
    name = "censys"
    asset_types = ["ip", "domain"]
    requires_key = True
    passive = True

    async def query(self, query: str, options: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        options = options or {}
        api_id = options.get("api_id")
        api_secret = options.get("api_secret")
        if not api_id or not api_secret:
            raise ValueError("censys api_id/api_secret required")

        token = base64.b64encode(f"{api_id}:{api_secret}".encode("utf-8")).decode("ascii")
        headers = {"Authorization": f"Basic {token}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                "https://search.censys.io/api/v2/hosts/search",
                params={"q": query, "per_page": 100},
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("result", {}).get("hits", []) or []

    def normalize(self, raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        assets: list[dict[str, Any]] = []
        seen: set[str] = set()

        for item in raw_items:
            ip = item.get("ip")
            if ip:
                key = f"ip:{ip}"
                if key not in seen:
                    seen.add(key)
                    assets.append(_asset("ip", str(ip), self.name, item))

            for name in item.get("names", []) or []:
                key = f"domain:{name}"
                if name and key not in seen:
                    seen.add(key)
                    assets.append(_asset("domain", str(name), self.name, item))

        return assets


class QuakeProvider(Provider):
    name = "quake"
    asset_types = ["ip", "domain", "service"]
    requires_key = True
    passive = True

    async def query(self, query: str, options: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        options = options or {}
        key = options.get("api_key")
        if not key:
            raise ValueError("quake api_key required")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://quake.360.net/api/v3/search/quake_service",
                headers={"X-QuakeToken": key},
                json={"query": query, "start": 0, "size": 100},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", []) or []

    def normalize(self, raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        assets: list[dict[str, Any]] = []
        seen: set[str] = set()

        for item in raw_items:
            ip = item.get("ip")
            if ip:
                key = f"ip:{ip}"
                if key not in seen:
                    seen.add(key)
                    assets.append(_asset("ip", str(ip), self.name, item))

            domain = item.get("domain")
            if domain:
                key = f"domain:{domain}"
                if key not in seen:
                    seen.add(key)
                    assets.append(_asset("domain", str(domain), self.name, item))

        return assets


class ZoomEyeProvider(Provider):
    name = "zoomeye"
    asset_types = ["ip", "domain"]
    requires_key = True
    passive = True

    async def query(self, query: str, options: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        options = options or {}
        key = options.get("api_key")
        if not key:
            raise ValueError("zoomeye api_key required")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                "https://api.zoomeye.org/host/search",
                params={"query": query, "page": 1, "pagesize": 100},
                headers={"API-KEY": key},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("matches", []) or []

    def normalize(self, raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        assets: list[dict[str, Any]] = []
        seen: set[str] = set()

        for item in raw_items:
            ip = item.get("ip")
            if ip:
                key = f"ip:{ip}"
                if key not in seen:
                    seen.add(key)
                    assets.append(_asset("ip", str(ip), self.name, item))

            for domain in item.get("domains", []) or []:
                key = f"domain:{domain}"
                if domain and key not in seen:
                    seen.add(key)
                    assets.append(_asset("domain", str(domain), self.name, item))

            hostname = item.get("hostname")
            if hostname:
                key = f"domain:{hostname}"
                if key not in seen:
                    seen.add(key)
                    assets.append(_asset("domain", str(hostname), self.name, item))

        return assets


class HunterProvider(Provider):
    name = "hunter"
    asset_types = ["ip", "domain", "url"]
    requires_key = True
    passive = True

    async def query(self, query: str, options: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        options = options or {}
        key = options.get("api_key")
        if not key:
            raise ValueError("hunter api_key required")

        search = base64.b64encode(query.encode("utf-8")).decode("ascii")
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                "https://hunter.qianxin.com/openApi/search",
                params={
                    "api-key": key,
                    "search": search,
                    "page": 1,
                    "page_size": 100,
                    "is_web": 3,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", {}).get("arr", []) or []

    def normalize(self, raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        assets: list[dict[str, Any]] = []
        seen: set[str] = set()

        for item in raw_items:
            for value, typ in [
                (item.get("ip"), "ip"),
                (item.get("domain"), "domain"),
                (item.get("url"), "url"),
            ]:
                if not value:
                    continue
                key = f"{typ}:{value}"
                if key in seen:
                    continue
                seen.add(key)
                assets.append(_asset(typ, str(value), self.name, item))

        return assets


class NetlasProvider(Provider):
    name = "netlas"
    asset_types = ["ip", "domain"]
    requires_key = True
    passive = True

    async def query(self, query: str, options: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        options = options or {}
        key = options.get("api_key")
        if not key:
            raise ValueError("netlas api_key required")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                "https://app.netlas.io/api/responses/",
                params={"q": query, "source_type": "include", "fields": "*", "size": 100},
                headers={"X-API-Key": key},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("items", []) or []

    def normalize(self, raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        assets: list[dict[str, Any]] = []
        seen: set[str] = set()

        for item in raw_items:
            data = item.get("data", item)
            ip = data.get("ip")
            if ip:
                key = f"ip:{ip}"
                if key not in seen:
                    seen.add(key)
                    assets.append(_asset("ip", str(ip), self.name, item))

            certificate = data.get("certificate", {}) or {}
            names = certificate.get("names") or []
            if isinstance(names, str):
                names = names.split("\n")
            for name in names:
                name = str(name).strip().lower()
                if not name:
                    continue
                key = f"domain:{name}"
                if key not in seen:
                    seen.add(key)
                    assets.append(_asset("domain", name, self.name, item))

        return assets


class VirusTotalProvider(Provider):
    name = "virustotal"
    asset_types = ["domain"]
    requires_key = True
    passive = True

    async def query(self, query: str, options: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        options = options or {}
        key = options.get("api_key")
        if not key:
            raise ValueError("virustotal api_key required")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"https://www.virustotal.com/api/v3/domains/{query}/subdomains",
                params={"limit": 100},
                headers={"x-apikey": key},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", []) or []

    def normalize(self, raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        assets: list[dict[str, Any]] = []
        for item in raw_items:
            value = item.get("id")
            if value:
                assets.append(_asset("domain", str(value), self.name, item))
        return assets


class SecurityTrailsProvider(Provider):
    name = "securitytrails"
    asset_types = ["domain"]
    requires_key = True
    passive = True

    async def query(self, query: str, options: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        options = options or {}
        key = options.get("api_key")
        if not key:
            raise ValueError("securitytrails api_key required")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"https://api.securitytrails.com/v1/domain/{query}/subdomains",
                params={"children_only": "false"},
                headers={"APIKEY": key},
            )
            resp.raise_for_status()
            data = resp.json()
            return [{"domain": query, "subdomains": data.get("subdomains", [])}]

    def normalize(self, raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        assets: list[dict[str, Any]] = []
        for item in raw_items:
            domain = item.get("domain", "")
            for sub in item.get("subdomains", []) or []:
                host = f"{sub}.{domain}".strip(".")
                assets.append(_asset("domain", host, self.name, item))
        return assets


class GreyNoiseProvider(Provider):
    name = "greynoise"
    asset_types = ["ip"]
    requires_key = True
    passive = True

    async def query(self, query: str, options: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        options = options or {}
        key = options.get("api_key")
        if not key:
            raise ValueError("greynoise api_key required")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"https://api.greynoise.io/v3/community/{query}",
                headers={"key": key, "Accept": "application/json"},
            )
            resp.raise_for_status()
            return [resp.json()]

    def normalize(self, raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        assets: list[dict[str, Any]] = []
        for item in raw_items:
            ip = item.get("ip")
            if ip:
                assets.append(_asset("ip", str(ip), self.name, item))
        return assets


class AbuseIPDBProvider(Provider):
    name = "abuseipdb"
    asset_types = ["ip"]
    requires_key = True
    passive = True

    async def query(self, query: str, options: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        options = options or {}
        key = options.get("api_key")
        if not key:
            raise ValueError("abuseipdb api_key required")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                "https://api.abuseipdb.com/api/v2/check",
                params={"ipAddress": query, "maxAgeInDays": 90},
                headers={"Key": key, "Accept": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
            return [data.get("data", {})]

    def normalize(self, raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        assets: list[dict[str, Any]] = []
        for item in raw_items:
            ip = item.get("ipAddress")
            if ip:
                assets.append(_asset("ip", str(ip), self.name, item))
        return assets


class IPinfoProvider(Provider):
    name = "ipinfo"
    asset_types = ["ip"]
    requires_key = False
    passive = True

    async def query(self, query: str, options: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        options = options or {}
        token = options.get("api_key")
        params = {"token": token} if token else None
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"https://ipinfo.io/{query}/json", params=params)
            resp.raise_for_status()
            return [resp.json()]

    def normalize(self, raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        assets: list[dict[str, Any]] = []
        for item in raw_items:
            ip = item.get("ip")
            if ip:
                assets.append(_asset("ip", str(ip), self.name, item))
        return assets
