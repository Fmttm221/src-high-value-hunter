import uuid
from typing import Any
from urllib.parse import urlparse

from ..providers import get_provider
from ..providers.retry import with_retry
from .probe import probe_target
from .cloud import run_cloud
from .code import run_code
from .js import run_js
from .wechat_detect import run_wechat_detect
from .hexstrike_map import MAPPINGS
from .chain_suggest import suggest_chains

PASSIVE_PROVIDER_ORDER = [
    "certspotter",
    "crtsh",
    "urlscan",
    "otx",
    "wayback",
    "shodan",
    "censys",
    "quake",
    "zoomeye",
    "hunter",
    "netlas",
    "virustotal",
    "securitytrails",
]


def _provider_options(config, name: str, options: dict[str, Any]) -> dict[str, Any]:
    out = dict(options)
    provider_config = config.providers.get(name)
    if provider_config:
        out.setdefault("api_key", provider_config.api_key)
        out.setdefault("api_id", provider_config.api_id)
        out.setdefault("api_secret", provider_config.api_secret)
    return out


def _provider_ready(name: str, adapter, options: dict[str, Any]) -> tuple[bool, str]:
    if not adapter.requires_key:
        return True, ""
    if name == "censys":
        if not options.get("api_id") or not options.get("api_secret"):
            return False, "missing api_id/api_secret"
        return True, ""
    if not options.get("api_key"):
        return False, "missing api_key"
    return True, ""


async def run_passive(
    storage,
    targets: list[str],
    options: dict[str, Any],
    config,
) -> dict[str, Any]:
    provider_summary: dict[str, Any] = {}
    errors: list[dict[str, Any]] = []
    total_assets = 0

    for provider_name in PASSIVE_PROVIDER_ORDER:
        adapter = get_provider(provider_name)
        if adapter is None:
            continue

        provider_config = config.providers.get(provider_name)
        if provider_config and not provider_config.enabled:
            provider_summary[provider_name] = {
                "assets": 0,
                "errors": [{"target": "", "error": "disabled"}],
            }
            continue

        adapter_options = _provider_options(config, provider_name, options)
        ready, reason = _provider_ready(provider_name, adapter, adapter_options)
        if not ready:
            provider_summary[provider_name] = {
                "assets": 0,
                "errors": [{"target": "", "error": reason}],
            }
            continue

        provider_assets = 0
        provider_errors: list[dict[str, Any]] = []

        for target in targets:
            try:
                raw_items = await with_retry(
                    adapter.query,
                    target,
                    adapter_options,
                    retries=3,
                    base_delay=1.0,
                )
                assets = adapter.normalize(raw_items)
                storage.save_assets(assets)
                provider_assets += len(assets)
            except Exception as exc:  # pragma: no cover - network error path
                provider_errors.append({"target": target, "error": str(exc)})

        provider_summary[provider_name] = {
            "assets": provider_assets,
            "errors": provider_errors,
        }
        total_assets += provider_assets
        errors.extend(provider_errors)

    storage.set_state(
        "last_phase",
        {
            "phase": "passive",
            "targets": targets,
            "total_assets": total_assets,
        },
    )

    return {
        "status": "ok",
        "phase": "passive",
        "providers": provider_summary,
        "total_assets": total_assets,
        "errors": errors,
    }


async def run_probe(
    storage,
    targets: list[str],
    options: dict[str, Any],
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []

    for target in targets:
        probe = await probe_target(target, options)
        waf = probe.get("waf", {})
        detected = bool(waf.get("detected"))
        host = urlparse(probe.get("url") or f"https://{target}").hostname or target

        profile = {
            "host": host,
            "waf": waf,
            "mode": "conservative" if detected else "normal",
            "safe_concurrency": 1 if detected else 5,
            "safe_rps": 1.0 if detected else 10.0,
            "delay_ms": 500 if detected else 0,
            "backoff_on": [403, 429, 503],
            "cooldown_seconds": 300,
            "ip_blocked": False,
            "extra": {
                "probe_url": probe.get("url"),
                "status_code": probe.get("status_code"),
                "error": probe.get("error"),
            },
        }
        storage.save_throttle(profile)
        results.append(
            {
                "target": target,
                "host": host,
                "profile": profile,
                "probe": probe,
            }
        )

    storage.set_state(
        "last_phase",
        {
            "phase": "probe",
            "targets": targets,
            "count": len(results),
        },
    )

    return {
        "status": "ok",
        "phase": "probe",
        "results": results,
        "count": len(results),
    }


def run_active(
    storage,
    targets: list[str],
    options: dict[str, Any],
) -> dict[str, Any]:
    tasks: list[dict[str, Any]] = []
    for target in targets:
        definitions = [
            ("subdomain_bruteforce", "hexstrike.subfinder_scan"),
            ("dns_resolve", "hexstrike.dnsenum_scan"),
            ("http_probe", "hexstrike.httpx_probe"),
            ("port_scan", "hexstrike.nmap_scan"),
            ("crawl", "hexstrike.katana_crawl"),
        ]
        for task_type, tool in definitions:
            task_id = str(uuid.uuid4())
            payload = {"target": target, "tool": tool}
            storage.save_task(
                {
                    "id": task_id,
                    "source": "recon-hub",
                    "type": task_type,
                    "status": "queued",
                    "payload": payload,
                    "host": target,
                }
            )
            tasks.append(
                {
                    "task_id": task_id,
                    "type": task_type,
                    "tool": tool,
                    "target": target,
                    "status": "queued",
                }
            )

    return {
        "status": "ok",
        "phase": "active",
        "targets": targets,
        "tasks": tasks,
        "count": len(tasks),
        "message": "Execute these tasks via hexstrike MCP and update with recon_task_update.",
    }


def run_exposure(
    storage,
    targets: list[str],
    options: dict[str, Any],
) -> dict[str, Any]:
    tasks: list[dict[str, Any]] = []
    for target in targets:
        definitions = [
            ("http_probe", "hexstrike.httpx_probe"),
            ("waf_detect", "hexstrike.wafw00f_scan"),
            ("tech_detect", "hexstrike.nuclei_scan"),
            ("port_scan", "hexstrike.nmap_scan"),
        ]
        for task_type, tool in definitions:
            task_id = str(uuid.uuid4())
            payload = {"target": target, "tool": tool}
            storage.save_task(
                {
                    "id": task_id,
                    "source": "recon-hub",
                    "type": task_type,
                    "status": "queued",
                    "payload": payload,
                    "host": target,
                }
            )
            tasks.append(
                {
                    "task_id": task_id,
                    "type": task_type,
                    "tool": tool,
                    "target": target,
                    "status": "queued",
                }
            )

    return {
        "status": "ok",
        "phase": "exposure",
        "targets": targets,
        "tasks": tasks,
        "count": len(tasks),
        "message": "Execute these tasks via hexstrike MCP and update with recon_task_update.",
    }
VULN_RULES: dict[str, list[str]] = {
    "payment": ["sqli", "xss", "cve"],
    "money": ["sqli", "xss", "cve"],
    "account": ["sqli", "xss", "jwt", "cve"],
    "admin": ["sqli", "xss", "cve"],
    "api": ["sqli", "ssrf", "cve"],
    "upload": ["lfi", "cve"],
    "cloud": ["ssrf", "cve"],
    "graphql": ["graphql"],
    "jwt": ["jwt"],
}


def run_vuln(
    storage,
    targets: list[str],
    options: dict[str, Any],
) -> dict[str, Any]:
    endpoints = storage.list_endpoints(limit=options.get("limit", 100))
    tasks: list[dict[str, Any]] = []

    for endpoint in endpoints:
        tags = endpoint.get("monetization_tags", []) or []
        task_types: set[str] = set()
        for tag in tags:
            task_types.update(VULN_RULES.get(str(tag).lower(), []))
        if not task_types:
            task_types.add("cve")

        for task_type in sorted(task_types):
            mapping = MAPPINGS.get(task_type)
            if mapping is None:
                continue
            task_id = str(uuid.uuid4())
            target = endpoint.get("url", "")
            payload = {
                "target": target,
                "task_type": task_type,
                "tool": mapping["tool"],
                "endpoint_id": endpoint.get("id"),
            }
            storage.save_task(
                {
                    "id": task_id,
                    "source": "recon-hub",
                    "type": task_type,
                    "status": "queued",
                    "payload": payload,
                    "host": target,
                }
            )
            tasks.append(
                {
                    "task_id": task_id,
                    "type": task_type,
                    "tool": mapping["tool"],
                    "target": target,
                    "status": "queued",
                }
            )

    return {
        "status": "ok",
        "phase": "vuln",
        "tasks": tasks,
        "count": len(tasks),
        "message": "Execute these tasks via hexstrike MCP and update with recon_task_update.",
    }
def run_chain(
    storage,
    targets: list[str],
    options: dict[str, Any],
) -> dict[str, Any]:
    findings = storage.list_findings(limit=options.get("limit", 1000))
    suggestions = suggest_chains(findings)
    storage.save_chains(suggestions)
    return {
        "status": "ok",
        "phase": "chain",
        "suggestions": suggestions,
        "count": len(suggestions),
    }
def register_phase_tools(mcp, storage, config):
    @mcp.tool()
    async def recon_phase(
        phase: str,
        targets: list[str],
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run a recon phase: passive, probe, active, js, cloud, mobile, code, merge."""
        options = options or {}

        if phase == "passive":
            return await run_passive(storage, targets, options, config)

        if phase == "probe":
            return await run_probe(storage, targets, options)

        if phase == "active":
            return run_active(storage, targets, options)

        if phase == "exposure":
            return run_exposure(storage, targets, options)
        if phase == "js":
            urls = options.get("urls") or targets
            return await run_js(storage, urls, depth=options.get("depth", 1), options=options)

        if phase == "code":
            merged_assets: list[dict[str, Any]] = []
            merged_errors: list[dict[str, Any]] = []
            for target in targets:
                result = await run_code(
                    storage,
                    target,
                    platforms=options.get("platforms"),
                    options=options,
                )
                merged_assets.extend(result.get("assets", []))
                merged_errors.extend(result.get("errors", []))
            return {
                "status": "ok",
                "phase": "code",
                "assets": merged_assets,
                "errors": merged_errors,
                "count": len(merged_assets),
            }

        if phase == "cloud":
            return await run_cloud(storage, targets, options=options)

        if phase == "vuln":
            return run_vuln(storage, targets, options)

        if phase == "chain":
            return run_chain(storage, targets, options)

        if phase == "wechat":
            return await run_wechat_detect(storage, targets, options=options)

        return {
            "status": "not_implemented",
            "phase": phase,
            "targets": targets,
            "options": options,
        }
