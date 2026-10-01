from typing import Any

from ..utils import truncate_assets

TAG_WEIGHTS = {
    "payment": 40,
    "money": 40,
    "admin": 35,
    "account": 30,
    "cloud": 30,
    "cicd": 30,
    "pii": 30,
    "api": 25,
    "upload": 20,
    "export": 20,
    "internal": 15,
}


def score_asset(asset: dict[str, Any]) -> dict[str, Any]:
    asset = dict(asset)
    score = 0
    reasons: list[str] = []

    for tag in asset.get("tags", []) or []:
        weight = TAG_WEIGHTS.get(str(tag).lower(), 0)
        if weight:
            score += weight
            reasons.append(str(tag).lower())

    if asset.get("alive"):
        score += 10
        reasons.append("alive")

    asset_type = asset.get("type")
    if asset_type == "url":
        score += 5
        reasons.append("url")
    elif asset_type == "domain":
        score += 5
        reasons.append("domain")

    asset["priority"] = min(score, 100)
    asset["priority_reasons"] = sorted(set(reasons))
    return asset


def register_score_tools(mcp, storage, config):
    @mcp.tool()
    def recon_score(assets: list[dict[str, Any]]) -> dict[str, Any]:
        """Score assets by monetization tags and basic factors."""
        scored = [score_asset(asset) for asset in assets]
        storage.save_assets(scored)
        return {"status": "ok", "count": len(scored), "assets": truncate_assets(scored)}
