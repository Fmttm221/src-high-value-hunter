from typing import Any
from urllib.parse import urlparse

import httpx

WAF_HEADER_HINTS = {
    "cf-ray": "cloudflare",
    "x-sucuri-id": "sucuri",
    "x-akamai-transformed": "akamai",
    "x-amz-cf-id": "aws-cloudfront",
    "x-iinfo": "imperva",
    "x-cdn": "generic",
    "x-waf": "generic",
}

WAF_COOKIE_HINTS = {
    "__cfduid": "cloudflare",
    "cf_clearance": "cloudflare",
    "incap_ses_": "imperva",
    "visid_incap_": "imperva",
    "ak_bmsc": "akamai",
    "bm_sv": "akamai",
    "AWSALB": "aws",
    "AWSALBCORS": "aws",
}

BODY_HINTS = [
    "access denied",
    "attention required",
    "cloudflare",
    "web application firewall",
    "request blocked",
]


def normalize_url(target: str) -> str:
    if target.startswith("http://") or target.startswith("https://"):
        return target
    return f"https://{target}"


def detect_waf(resp: httpx.Response) -> dict[str, Any]:
    headers = {k.lower(): v for k, v in resp.headers.items()}
    cookies = resp.cookies
    text = resp.text.lower() if resp.text else ""
    signals: list[str] = []
    vendor: str | None = None

    for header, candidate in WAF_HEADER_HINTS.items():
        if header in headers:
            signals.append(f"header:{header}")
            vendor = vendor or candidate

    for cookie_name, candidate in WAF_COOKIE_HINTS.items():
        if cookie_name in cookies:
            signals.append(f"cookie:{cookie_name}")
            vendor = vendor or candidate

    if resp.status_code in (403, 429, 503):
        signals.append(f"status:{resp.status_code}")

    for hint in BODY_HINTS:
        if hint in text:
            signals.append(f"body:{hint}")
            vendor = vendor or "generic"

    detected = bool(signals)
    confidence = min(1.0, len(signals) / 3.0) if detected else 0.0
    return {
        "detected": detected,
        "vendor": vendor,
        "confidence": confidence,
        "signals": signals,
    }


async def probe_target(
    target: str,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    options = options or {}
    primary = normalize_url(target)
    candidates = [primary]
    if primary.startswith("https://"):
        candidates.append(primary.replace("https://", "http://", 1))

    result: dict[str, Any] = {
        "target": target,
        "url": primary,
        "status_code": None,
        "headers": {},
        "waf": {"detected": False, "vendor": None, "confidence": 0.0, "signals": []},
        "error": None,
    }

    last_error: str | None = None
    for candidate in candidates:
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(candidate, headers=options.get("headers"))
                result["url"] = candidate
                result["status_code"] = resp.status_code
                result["headers"] = dict(resp.headers)
                result["waf"] = detect_waf(resp)
                result["error"] = None
                return result
        except Exception as exc:  # pragma: no cover - network error path
            message = str(exc)
            last_error = f"{type(exc).__name__}: {message}" if message else type(exc).__name__

    result["error"] = last_error or "unknown error"
    return result


def register_probe_tools(mcp, storage, config):
    @mcp.tool()
    async def recon_probe(
        targets: list[str],
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Probe targets for WAF and generate throttle profiles."""
        from ..tools.phase import run_probe

        return await run_probe(storage, targets, options or {})
