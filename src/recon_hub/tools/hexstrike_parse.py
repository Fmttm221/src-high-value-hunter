import hashlib
import json
import re
from typing import Any
from urllib.parse import urlparse

from ..utils import truncate_assets


def _asset(typ: str, source: str, **kwargs: Any) -> dict[str, Any]:
    key = f"{typ}:{kwargs.get('host') or kwargs.get('url') or kwargs.get('ip') or ''}"
    asset = {
        "id": hashlib.sha256(key.encode("utf-8")).hexdigest(),
        "type": typ,
        "source": source,
        **kwargs,
    }
    return asset


def _parse_subfinder(output: str) -> dict[str, Any]:
    assets: list[dict[str, Any]] = []
    for line in output.splitlines():
        host = line.strip().lower()
        if not host or host.startswith("[") or " " in host:
            continue
        assets.append(_asset("domain", "hexstrike.subfinder", subtype="subdomain", host=host, tags=[]))
    return {"assets": assets, "findings": [], "summary": {"count": len(assets)}}


def _parse_httpx(output: str) -> dict[str, Any]:
    assets: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        url = data.get("url") or ""
        host = data.get("input") or urlparse(url).hostname or ""
        ip = data.get("host") or ""
        port = data.get("port")
        try:
            port = int(port) if port is not None else None
        except (TypeError, ValueError):
            port = None
        assets.append(
            _asset(
                "url",
                "hexstrike.httpx",
                url=url,
                host=host,
                ip=ip if re.match(r"^[0-9a-fA-F:.]+$", str(ip)) else "",
                port=port,
                alive=not data.get("failed", False),
                tags=["alive"] if not data.get("failed", False) else [],
                extra={
                    "status_code": data.get("status_code"),
                    "title": data.get("title"),
                    "tech": data.get("tech", []),
                    "webserver": data.get("webserver"),
                    "cdn_name": data.get("cdn_name"),
                    "content_length": data.get("content_length"),
                },
            )
        )
    return {"assets": assets, "findings": findings, "summary": {"count": len(assets)}}


def _parse_katana(output: str) -> dict[str, Any]:
    assets: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line in output.splitlines():
        url = line.strip()
        if not url.startswith("http") or url in seen:
            continue
        seen.add(url)
        host = urlparse(url).hostname or ""
        assets.append(_asset("url", "hexstrike.katana", url=url, host=host, tags=[]))
    return {"assets": assets, "findings": [], "summary": {"count": len(assets)}}


def _parse_nuclei(output: str) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        info = data.get("info", {}) or {}
        template_id = data.get("template-id") or data.get("template_id")
        matched_at = data.get("matched-at") or data.get("matched_at")
        findings.append(
            {
                "type": "nuclei",
                "template_id": template_id,
                "matched_at": matched_at,
                "severity": info.get("severity"),
                "name": info.get("name"),
                "extra": {
                    "template_id": template_id,
                    "matched_at": matched_at,
                    "severity": info.get("severity"),
                    "name": info.get("name"),
                    "raw": data,
                },
            }
        )
    return {"assets": [], "findings": findings, "summary": {"count": len(findings)}}


def _parse_wafw00f(output: str) -> dict[str, Any]:
    text = output.lower()
    vendor = None
    detected = False
    if "is behind" in text:
        detected = True
        match = re.search(r"is behind\s+(.+)", output, re.IGNORECASE)
        if match:
            vendor = match.group(1).strip()
    elif "no waf detected" in text:
        detected = False
    return {
        "assets": [],
        "findings": [{"type": "waf", "detected": detected, "vendor": vendor, "raw": output[:2000]}],
        "summary": {"waf_detected": detected, "vendor": vendor},
    }


def _parse_nmap(output: str) -> dict[str, Any]:
    ports: list[dict[str, Any]] = []
    for line in output.splitlines():
        match = re.match(r"^(\d+)/(tcp|udp)\s+open\s+(\S+)(?:\s+(.*))?$", line.strip())
        if match:
            ports.append(
                {
                    "port": int(match.group(1)),
                    "protocol": match.group(2),
                    "service": match.group(3),
                    "version": (match.group(4) or "").strip(),
                }
            )
    return {
        "assets": [],
        "findings": [{"type": "nmap", "ports": ports}],
        "summary": {"open_ports": ports},
    }


PARSERS = {
    "subdomain_bruteforce": _parse_subfinder,
    "http_probe": _parse_httpx,
    "crawl": _parse_katana,
    "tech_detect": _parse_nuclei,
    "waf_detect": _parse_wafw00f,
    "port_scan": _parse_nmap,
}


def parse_output(task_type: str, output: str) -> dict[str, Any]:
    parser = PARSERS.get(task_type)
    if parser is None:
        return {
            "status": "unknown_task_type",
            "task_type": task_type,
            "assets": [],
            "findings": [],
            "summary": {},
        }
    parsed = parser(output)
    return {
        "status": "ok",
        "task_type": task_type,
        "assets": parsed["assets"],
        "findings": parsed["findings"],
        "summary": parsed["summary"],
    }


def register_hexstrike_parse_tools(mcp, storage, config):
    @mcp.tool()
    def recon_hexstrike_parse(task_type: str, output: str) -> dict[str, Any]:
        """Parse raw hexstrike output into assets / findings."""
        result = parse_output(task_type, output)
        result["assets"] = truncate_assets(result.get("assets", []))
        return result

    @mcp.tool()
    def recon_hexstrike_ingest(
        task_type: str,
        target: str,
        output: str,
        source: str = "hexstrike",
    ) -> dict[str, Any]:
        """Parse raw hexstrike output and ingest assets."""
        result = parse_output(task_type, output)
        assets = result.get("assets", [])
        for asset in assets:
            asset.setdefault("source", source)
        storage.save_assets(assets)

        storage.save_findings(result.get('findings', []))
        return {
            "status": "ok",
            "task_type": task_type,
            "target": target,
            "assets": truncate_assets(assets),
            "findings": result.get("findings", []),
            "summary": result.get("summary", {}),
            "count": len(assets),
        }
