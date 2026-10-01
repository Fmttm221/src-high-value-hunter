import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from recon_hub.providers.certspotter import CertSpotterProvider
from recon_hub.providers.crtsh import CrtshProvider
from recon_hub.providers.otx import OtxProvider
from recon_hub.providers.urlscan import UrlscanProvider
from recon_hub.providers.wayback import WaybackProvider
from recon_hub.storage import Storage
from recon_hub.tools.chain_suggest import suggest_chains
from recon_hub.tools.hexstrike_map import build_plan
from recon_hub.tools.hexstrike_parse import parse_output
from recon_hub.tools.js import extract_from_text
from recon_hub.tools.merge import merge_assets
from recon_hub.tools.score import score_asset
from recon_hub.utils import truncate_assets


def test_crtsh_normalize_dedup():
    provider = CrtshProvider()
    raw = [
        {"name_value": "a.example.com\nb.example.com"},
        {"name_value": "b.example.com\n*.example.com"},
    ]
    assets = provider.normalize(raw)
    hosts = sorted(a["host"] for a in assets)
    assert hosts == ["*.example.com", "a.example.com", "b.example.com"]
    assert all(a["source"] == "crtsh" for a in assets)


def test_certspotter_normalize():
    provider = CertSpotterProvider()
    raw = [{"dns_names": ["a.example.com", "b.example.com"]}]
    assets = provider.normalize(raw)
    hosts = sorted(a["host"] for a in assets)
    assert hosts == ["a.example.com", "b.example.com"]


def test_urlscan_normalize():
    provider = UrlscanProvider()
    raw = [
        {
            "page": {
                "domain": "example.com",
                "url": "https://example.com/",
                "ip": "1.2.3.4",
            }
        }
    ]
    assets = provider.normalize(raw)
    types = sorted(a["type"] for a in assets)
    assert types == ["domain", "ip", "url"]


def test_otx_normalize():
    provider = OtxProvider()
    raw = [{"hostname": "a.example.com", "address": "1.2.3.4"}]
    assets = provider.normalize(raw)
    types = sorted(a["type"] for a in assets)
    assert types == ["domain", "ip"]


def test_wayback_normalize():
    provider = WaybackProvider()
    raw = [["https://example.com/a"], ["https://example.com/b"]]
    assets = provider.normalize(raw)
    types = sorted(a["type"] for a in assets)
    assert types == ["domain", "url", "url"]


def test_js_extract():
    text = 'fetch("/api/users"); const key = "AKIA1234567890ABCDEF";'
    extracted = extract_from_text(text)
    assert "/api/users" in extracted["endpoints"]
    assert "AKIA1234567890ABCDEF" in extracted["secrets"]


def test_merge_assets():
    first = [{"id": "1", "host": "a"}, {"id": "2", "host": "b"}]
    second = [{"id": "1", "host": "a2"}]
    merged = merge_assets([first, second])
    assert len(merged) == 2
    assert any(item["host"] == "a2" for item in merged)


def test_score_asset():
    asset = {"type": "url", "tags": ["payment"], "alive": True}
    scored = score_asset(asset)
    assert scored["priority"] >= 50


def test_truncate_assets():
    assets = [{"id": "1", "extra": {"long": "x" * 1000}}]
    truncated = truncate_assets(assets)
    assert len(truncated[0]["extra"]["long"]) < 1000


def test_hexstrike_plan():
    plan = build_plan("sqli", "https://example.com/?id=1")
    assert plan["tool"] == "sqlmap_scan"
    assert "sqlmap" in plan["command"]


def test_hexstrike_parse_subfinder():
    result = parse_output("subdomain_bruteforce", "a.example.com\nb.example.com\n")
    assert len(result["assets"]) == 2


def test_hexstrike_parse_httpx():
    output = '{"url":"http://example.com","input":"example.com","host":"1.2.3.4","port":"80","status_code":200,"title":"Example","tech":["Cloudflare"],"failed":false}\n'
    result = parse_output("http_probe", output)
    assert len(result["assets"]) == 1
    assert result["assets"][0]["url"] == "http://example.com"


def test_hexstrike_parse_nuclei():
    output = '{"template-id":"tech-detect","matched-at":"https://example.com","info":{"name":"Tech","severity":"info"}}\n'
    result = parse_output("tech_detect", output)
    assert len(result["findings"]) == 1
    assert result["findings"][0]["template_id"] == "tech-detect"


def test_chain_suggest():
    suggestions = suggest_chains([{"type": "open_redirect"}, {"type": "oauth"}])
    assert len(suggestions) == 1
    assert suggestions[0]["target_monetization"] == "account_takeover"


def test_storage_asset_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        storage = Storage(str(Path(tmp) / "recon.db"))
        storage.save_assets(
            [
                {
                    "id": "asset-1",
                    "type": "domain",
                    "host": "example.com",
                    "source": "test",
                    "tags": ["account"],
                    "extra": {"x": 1},
                }
            ]
        )
        assets = storage.list_assets()
        assert len(assets) == 1
        assert assets[0]["host"] == "example.com"
        storage.close()


def test_storage_endpoint_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        storage = Storage(str(Path(tmp) / "recon.db"))
        storage.save_endpoints(
            [
                {
                    "url": "https://example.com/api/user",
                    "method": "GET",
                    "params": ["id"],
                    "monetization_tags": ["account"],
                }
            ]
        )
        endpoints = storage.list_endpoints()
        assert len(endpoints) == 1
        assert endpoints[0]["params"] == ["id"]
        storage.close()


def test_storage_finding_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        storage = Storage(str(Path(tmp) / "recon.db"))
        storage.save_findings([{"type": "open_redirect", "endpoint": "https://example.com"}])
        findings = storage.list_findings()
        assert len(findings) == 1
        assert findings[0]["type"] == "open_redirect"
        storage.close()


def test_storage_chain_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        storage = Storage(str(Path(tmp) / "recon.db"))
        storage.save_chains(
            [
                {
                    "nodes": ["open_redirect", "oauth", "account_takeover"],
                    "target_monetization": "account_takeover",
                    "status": "candidate",
                }
            ]
        )
        chains = storage.list_chains()
        assert len(chains) == 1
        assert chains[0]["target_monetization"] == "account_takeover"
        storage.close()


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for test in tests:
        test()
    print(f"smoke tests: OK ({len(tests)} tests)")
