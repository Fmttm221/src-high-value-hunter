import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _render_finding(finding: dict[str, Any]) -> str:
    lines = [
        f"### {finding.get('type', 'unknown')}",
        "",
        f"- ID: `{finding.get('id', '')}`",
        f"- Endpoint: `{finding.get('endpoint', '')}`",
        f"- Param: `{finding.get('param', '')}`",
        f"- Role: `{finding.get('role', '')}`",
        f"- Auth state: `{finding.get('auth_state', '')}`",
        f"- Standalone impact: `{finding.get('standalone_impact', '')}`",
        f"- Submission: `{finding.get('submission', '')}`",
        f"- Monetization paths: `{finding.get('monetization_paths', [])}`",
        f"- Chain roles: `{finding.get('chain_roles', [])}`",
        "",
        "```json",
        json.dumps(finding.get("extra", {}), ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    return "\n".join(lines)


def _render_chain(chain: dict[str, Any]) -> str:
    lines = [
        f"### {chain.get('target_monetization', 'chain')}",
        "",
        f"- ID: `{chain.get('id', '')}`",
        f"- Status: `{chain.get('status', '')}`",
        f"- Nodes: `{chain.get('nodes', [])}`",
        f"- Edges: `{chain.get('edges', [])}`",
        "",
        "```json",
        json.dumps(chain.get("extra", {}), ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    return "\n".join(lines)


def register_report_tools(mcp, storage, config):
    @mcp.tool()
    def recon_report(
        name: str = "report",
        finding_ids: list[str] | None = None,
        chain_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate a Markdown report from findings and chains."""
        findings = storage.list_findings(limit=1000)
        chains = storage.list_chains(limit=1000)

        if finding_ids:
            wanted = set(finding_ids)
            findings = [item for item in findings if item.get("id") in wanted]
        if chain_ids:
            wanted = set(chain_ids)
            chains = [item for item in chains if item.get("id") in wanted]

        reports_dir = Path(config.storage.jsonl_dir).parent / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_")) or "report"
        out = reports_dir / f"{safe_name}.md"

        lines = [
            f"# {name}",
            "",
            f"Generated at: {datetime.now(timezone.utc).isoformat()}",
            "",
            "## Summary",
            "",
            f"- Findings: {len(findings)}",
            f"- Chains: {len(chains)}",
            "",
            "## Findings",
            "",
        ]
        if findings:
            lines.extend(_render_finding(finding) for finding in findings)
        else:
            lines.append("No findings.")
            lines.append("")

        lines.extend(["## Chains", ""])
        if chains:
            lines.extend(_render_chain(chain) for chain in chains)
        else:
            lines.append("No chains.")
            lines.append("")

        out.write_text("\n".join(lines), encoding="utf-8")
        return {
            "status": "ok",
            "path": str(out),
            "findings": len(findings),
            "chains": len(chains),
        }
