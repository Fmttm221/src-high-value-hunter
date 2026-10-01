import hashlib
from typing import Any

import httpx

from ..utils import truncate_assets


def bucket_candidates(keyword: str) -> list[str]:
    suffixes = ["", "-dev", "-prod", "-backup", "-data", "-assets", "-static", "-test"]
    return [f"{keyword}{suffix}" for suffix in suffixes]


async def check_bucket(bucket: str, options: dict[str, Any] | None = None) -> dict[str, Any] | None:
    options = options or {}
    url = f"https://{bucket}.s3.amazonaws.com/"
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code not in (200, 403):
                return None
            public_read = resp.status_code == 200 and "ListBucketResult" in resp.text
            asset_id = hashlib.sha256(f"cloud:aws:s3:{bucket}".encode("utf-8")).hexdigest()
            return {
                "id": asset_id,
                "type": "cloud",
                "subtype": "s3",
                "bucket_name": bucket,
                "cloud_provider": "aws",
                "source": "recon_cloud",
                "extra": {
                    "url": url,
                    "status_code": resp.status_code,
                    "public_read": public_read,
                    "public_write": False,
                },
            }
    except Exception:  # pragma: no cover - network error path
        return None


async def run_cloud(
    storage,
    keywords: list[str],
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    options = options or {}
    assets: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for keyword in keywords:
        for bucket in bucket_candidates(keyword):
            try:
                asset = await check_bucket(bucket, options)
                if asset:
                    assets.append(asset)
            except Exception as exc:  # pragma: no cover - network error path
                errors.append({"bucket": bucket, "error": str(exc)})

    storage.save_assets(assets)
    return {
        "status": "ok",
        "keywords": keywords,
        "assets": truncate_assets(assets),
        "errors": errors,
    }


def register_cloud_tools(mcp, storage, config):
    @mcp.tool()
    async def recon_cloud(
        keywords: list[str],
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Check common S3 bucket name candidates."""
        return await run_cloud(storage, keywords, options=options)
