from typing import Any

CHAIN_PATTERNS: list[dict[str, Any]] = [
    {
        "requires": ["open_redirect", "oauth"],
        "chain": ["open_redirect", "oauth", "account_takeover"],
        "target_monetization": "account_takeover",
    },
    {
        "requires": ["xss", "csrf"],
        "chain": ["xss", "csrf", "account_takeover"],
        "target_monetization": "account_takeover",
    },
    {
        "requires": ["ssrf", "cloud_metadata"],
        "chain": ["ssrf", "cloud_metadata", "cloud_takeover"],
        "target_monetization": "cloud_takeover",
    },
    {
        "requires": ["sqli"],
        "chain": ["sqli", "rce"],
        "target_monetization": "rce",
    },
    {
        "requires": ["lfi"],
        "chain": ["lfi", "rce"],
        "target_monetization": "rce",
    },
    {
        "requires": ["upload"],
        "chain": ["upload", "rce"],
        "target_monetization": "rce",
    },
    {
        "requires": ["idor", "pii"],
        "chain": ["idor", "pii", "data_theft"],
        "target_monetization": "data_theft",
    },
    {
        "requires": ["cors"],
        "chain": ["cors", "data_theft"],
        "target_monetization": "data_theft",
    },
    {
        "requires": ["subdomain_takeover"],
        "chain": ["subdomain_takeover", "oauth", "account_takeover"],
        "target_monetization": "account_takeover",
    },
    {
        "requires": ["info_leak", "auth_bypass"],
        "chain": ["info_leak", "auth_bypass", "account_takeover"],
        "target_monetization": "account_takeover",
    },
    {
        "requires": ["request_smuggling"],
        "chain": ["request_smuggling", "auth_bypass"],
        "target_monetization": "auth_bypass",
    },
    {
        "requires": ["prototype_pollution"],
        "chain": ["prototype_pollution", "xss"],
        "target_monetization": "xss",
    },
]


def suggest_chains(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    present: set[str] = set()
    for finding in findings:
        finding_type = str(finding.get("type", "")).lower()
        if finding_type:
            present.add(finding_type)
        for tag in finding.get("extra", {}).get("tags", []) or []:
            present.add(str(tag).lower())

    suggestions: list[dict[str, Any]] = []
    for pattern in CHAIN_PATTERNS:
        if all(required in present for required in pattern["requires"]):
            suggestions.append(
                {
                    "nodes": pattern["chain"],
                    "edges": [
                        {"from": pattern["chain"][i], "to": pattern["chain"][i + 1]}
                        for i in range(len(pattern["chain"]) - 1)
                    ],
                    "target_monetization": pattern["target_monetization"],
                    "status": "candidate",
                    "requires": pattern["requires"],
                }
            )
    return suggestions


def register_chain_suggest_tools(mcp, storage, config):
    @mcp.tool()
    def recon_chain_suggest(
        findings: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Suggest vulnerability chains from findings."""
        items = findings if findings is not None else storage.list_findings(limit=1000)
        suggestions = suggest_chains(items)
        return {
            "status": "ok",
            "count": len(suggestions),
            "suggestions": suggestions,
        }
