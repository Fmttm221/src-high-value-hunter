from typing import Any

MAPPINGS: dict[str, dict[str, Any]] = {
    "subdomain_bruteforce": {
        "tool": "subfinder_scan",
        "arguments": {"domain": "{target}", "silent": True, "all_sources": False},
        "command": "subfinder -d {target} -silent",
        "parse": "lines",
        "ingest": "recon_ingest_domains",
    },
    "dns_resolve": {
        "tool": "dnsenum_scan",
        "arguments": {"target": "{target}"},
        "command": "dnsenum {target}",
        "parse": "text",
        "ingest": None,
    },
    "http_probe": {
        "tool": "execute_command",
        "arguments": {
            "command": "echo {target} | httpx -silent -json -tech-detect -status-code -title -web-server -timeout 10"
        },
        "command": "echo {target} | httpx -silent -json -tech-detect -status-code -title -web-server -timeout 10",
        "parse": "jsonl",
        "ingest": "recon_ingest_assets",
    },
    "waf_detect": {
        "tool": "wafw00f_scan",
        "arguments": {"target": "{target}"},
        "command": "wafw00f {target}",
        "parse": "text",
        "ingest": None,
    },
    "tech_detect": {
        "tool": "nuclei_scan",
        "arguments": {"target": "{target}", "tags": "tech"},
        "command": "nuclei -u {target} -tags tech -jsonl",
        "parse": "jsonl",
        "ingest": "recon_ingest_assets",
    },
    "port_scan": {
        "tool": "nmap_scan",
        "arguments": {
            "target": "{target}",
            "scan_type": "-sV",
            "ports": "80,443,8000,8080,8443",
        },
        "command": "nmap -sV -p 80,443,8000,8080,8443 {target}",
        "parse": "text",
        "ingest": None,
    },
    "crawl": {
        "tool": "katana_crawl",
        "arguments": {"url": "{target}", "depth": 2, "js_crawl": True},
        "command": "katana -u {target} -d 2 -jc",
        "parse": "lines",
        "ingest": "recon_ingest_assets",
    },
    "sqli": {
        "tool": "sqlmap_scan",
        "arguments": {"url": "{target}", "additional_args": "--batch --level=1 --risk=1"},
        "command": "sqlmap -u {target} --batch --level=1 --risk=1",
        "parse": "text",
        "ingest": "recon_ingest_findings",
    },
    "xss": {
        "tool": "dalfox_xss_scan",
        "arguments": {"url": "{target}"},
        "command": "dalfox url {target}",
        "parse": "text",
        "ingest": "recon_ingest_findings",
    },
    "lfi": {
        "tool": "dotdotpwn_scan",
        "arguments": {"target": "{target}", "module": "http"},
        "command": "dotdotpwn -m http -h {target}",
        "parse": "text",
        "ingest": "recon_ingest_findings",
    },
    "cve": {
        "tool": "nuclei_scan",
        "arguments": {"target": "{target}", "tags": "cve"},
        "command": "nuclei -u {target} -tags cve -jsonl",
        "parse": "jsonl",
        "ingest": "recon_ingest_findings",
    },
    "ssrf": {
        "tool": "nuclei_scan",
        "arguments": {"target": "{target}", "tags": "ssrf"},
        "command": "nuclei -u {target} -tags ssrf -jsonl",
        "parse": "jsonl",
        "ingest": "recon_ingest_findings",
    },
    "graphql": {
        "tool": "graphql_scanner",
        "arguments": {"endpoint": "{target}"},
        "command": "",
        "parse": "json",
        "ingest": "recon_ingest_findings",
    },
    "jwt": {
        "tool": "jwt_analyzer",
        "arguments": {"jwt_token": "{target}"},
        "command": "",
        "parse": "json",
        "ingest": "recon_ingest_findings",
    },
}


def _render(value: Any, target: str) -> Any:
    if isinstance(value, str):
        return value.replace("{target}", target)
    if isinstance(value, dict):
        return {key: _render(val, target) for key, val in value.items()}
    if isinstance(value, list):
        return [_render(item, target) for item in value]
    return value


def build_plan(task_type: str, target: str) -> dict[str, Any]:
    mapping = MAPPINGS.get(task_type)
    if not mapping:
        return {
            "status": "unknown_task_type",
            "task_type": task_type,
            "target": target,
        }
    return {
        "status": "ok",
        "task_type": task_type,
        "target": target,
        "tool": mapping["tool"],
        "arguments": _render(mapping["arguments"], target),
        "command": _render(mapping["command"], target),
        "parse": mapping["parse"],
        "ingest": mapping["ingest"],
    }


def register_hexstrike_map_tools(mcp, storage, config):
    @mcp.tool()
    def recon_hexstrike_plan(task_type: str, target: str) -> dict[str, Any]:
        """Return the correct hexstrike tool / command mapping for a task type."""
        return build_plan(task_type, target)

    @mcp.tool()
    def recon_hexstrike_plan_all(target: str) -> dict[str, Any]:
        """Return all known hexstrike plans for a target."""
        plans = [build_plan(task_type, target) for task_type in MAPPINGS]
        return {"status": "ok", "target": target, "plans": plans}
