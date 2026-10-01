import argparse
import os

from mcp.server.fastmcp import FastMCP

from .config import load_config
from .storage import Storage
from .tools.cloud import register_cloud_tools
from .tools.chains import register_chain_tools
from .tools.chain_suggest import register_chain_suggest_tools
from .tools.assets import register_asset_tools
from .tools.code import register_code_tools
from .tools.expand import register_expand_tools
from .tools.export import register_export_tools
from .tools.endpoints import register_endpoint_tools
from .tools.findings import register_finding_tools
from .tools.js import register_js_tools
from .tools.ingest import register_ingest_tools
from .tools.hexstrike_map import register_hexstrike_map_tools
from .tools.hexstrike_parse import register_hexstrike_parse_tools
from .tools.merge import register_merge_tools
from .tools.mobile import register_mobile_tools
from .tools.phase import register_phase_tools
from .tools.probe import register_probe_tools
from .tools.report import register_report_tools
from .tools.provider_query import register_provider_tools
from .tools.score import register_score_tools
from .tools.stats import register_stats_tools
from .tools.task import register_task_tools
from .tools.throttle import register_throttle_tools
from .tools.urls import register_url_tools
from .tools.wechat_detect import register_wechat_detect_tools

mcp = FastMCP("recon-hub")
storage: Storage | None = None


def main() -> None:
    global storage
    parser = argparse.ArgumentParser(description="recon-hub MCP server")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    args = parser.parse_args()

    config = load_config(args.config)
    if config.network.proxy:
        os.environ.setdefault("HTTP_PROXY", config.network.proxy)
        os.environ.setdefault("HTTPS_PROXY", config.network.proxy)
    storage = Storage(config.storage.sqlite)

    register_phase_tools(mcp, storage, config)
    register_provider_tools(mcp, storage, config)
    register_task_tools(mcp, storage, config)
    register_throttle_tools(mcp, storage, config)
    register_expand_tools(mcp, storage, config)
    register_url_tools(mcp, storage, config)
    register_wechat_detect_tools(mcp, storage, config)
    register_js_tools(mcp, storage, config)
    register_ingest_tools(mcp, storage, config)
    register_hexstrike_map_tools(mcp, storage, config)
    register_hexstrike_parse_tools(mcp, storage, config)
    register_merge_tools(mcp, storage, config)
    register_score_tools(mcp, storage, config)
    register_stats_tools(mcp, storage, config)
    register_probe_tools(mcp, storage, config)
    register_report_tools(mcp, storage, config)
    register_code_tools(mcp, storage, config)
    register_cloud_tools(mcp, storage, config)
    register_chain_tools(mcp, storage, config)
    register_chain_suggest_tools(mcp, storage, config)
    register_asset_tools(mcp, storage, config)
    register_mobile_tools(mcp, storage, config)
    register_export_tools(mcp, storage, config)
    register_endpoint_tools(mcp, storage, config)
    register_finding_tools(mcp, storage, config)

    mcp.run()


if __name__ == "__main__":
    main()
