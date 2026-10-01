from typing import Any

from ..utils import truncate_assets


def register_finding_tools(mcp, storage, config):
    @mcp.tool()
    def recon_ingest_findings(
        findings: list[dict[str, Any]],
        source: str = "import",
    ) -> dict[str, Any]:
        """Store a list of findings."""
        normalized: list[dict[str, Any]] = []
        for finding in findings:
            item = dict(finding)
            item.setdefault("extra", {})
            item["extra"].setdefault("source", source)
            normalized.append(item)

        storage.save_findings(normalized)
        return {
            "status": "ok",
            "count": len(normalized),
            "findings": normalized,
        }

    @mcp.tool()
    def recon_list_findings(
        limit: int = 100,
        offset: int = 0,
        type: str | None = None,
    ) -> dict[str, Any]:
        """List findings from SQLite."""
        findings = storage.list_findings(limit=limit, offset=offset, type=type)
        return {"status": "ok", "count": len(findings), "findings": findings}
