import hashlib
import re
from typing import Any
from urllib.parse import urlparse

import httpx

from ..utils import truncate_assets

APPID_RE = re.compile(r"wx[0-9a-fA-F]{16}")
KEYWORDS = [
    "miniprogram",
    "weapp",
    "wx-open-launch-weapp",
    "mp.weixin.qq.com",
]


def _asset_for(url: str, appid: str | None, evidence: str) -> dict[str, Any]:
    host = urlparse(url).hostname or ""
    key = f"wechat:{appid or url}"
    return {
        "id": hashlib.sha256(key.encode("utf-8")).hexdigest(),
        "type": "wechat_miniprogram",
        "subtype": "appid" if appid else "reference",
        "host": host,
        "url": url,
        "source": "recon_wechat_detect",
        "tags": ["wechat", "human_assisted"],
        "extra": {
            "appid": appid,
            "evidence": evidence,
            "activation": "last",
            "human_assisted": True,
        },
    }


async def run_wechat_detect(
    storage,
    urls: list[str],
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    options = options or {}
    assets: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for url in urls:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                text = resp.text
                appids = sorted(set(APPID_RE.findall(text)))
                lower = text.lower()
                matched_keywords = [kw for kw in KEYWORDS if kw in lower]

                if appids:
                    for appid in appids:
                        assets.append(_asset_for(url, appid, "appid"))
                elif matched_keywords:
                    assets.append(_asset_for(url, None, ",".join(matched_keywords)))
            except Exception as exc:  # pragma: no cover - network error path
                errors.append({"url": url, "error": str(exc)})

    storage.save_assets(assets)
    return {
        "status": "ok",
        "urls": urls,
        "assets": truncate_assets(assets),
        "errors": errors,
        "count": len(assets),
    }


def register_wechat_detect_tools(mcp, storage, config):
    @mcp.tool()
    async def recon_wechat_detect(
        urls: list[str],
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Detect WeChat Mini Program references in web pages."""
        return await run_wechat_detect(storage, urls, options=options)
