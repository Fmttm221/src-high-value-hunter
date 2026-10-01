from typing import Any


def register_mobile_tools(mcp, storage, config):
    @mcp.tool()
    def recon_mobile(
        app: str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Placeholder for APK download and static analysis."""
        return {
            "status": "not_implemented",
            "app": app,
            "options": options or {},
            "message": "Use hexstrike or local tooling (jadx / apktool / MobSF) to analyze the APK.",
        }
