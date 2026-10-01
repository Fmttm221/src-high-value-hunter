import argparse
import hashlib
import json
import os
import re

INCLUDE_PATTERNS = re.compile(r"(weixin|qqchess|wxs\.qq\.com|qpic\.cn|qlogo\.cn|tencent)", re.IGNORECASE)
EXCLUDE_HOSTS = {
    "functional.events.data.microsoft.com",
    "mcs.doubao.com",
    "clerk.openrouter.ai",
    "www.msftconnecttest.com",
    "ipv6.msftconnecttest.com",
    "srz.salesmartly.com",
    "msg-ws.salesmartly.com",
    "logifier.doubao.com",
}
STATIC_EXT = (
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico",
    ".css", ".js", ".mp4", ".woff", ".woff2", ".ttf", ".zip",
)


def load_entries(path: str) -> list[dict]:
    entries: list[dict] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def host_allowed(entry: dict, mini_only: bool) -> bool:
    host = entry.get("host", "")
    if not host:
        return False
    if mini_only:
        if host in EXCLUDE_HOSTS:
            return False
        if not INCLUDE_PATTERNS.search(host):
            return False
    return True


def is_static(path: str) -> bool:
    return path.lower().endswith(STATIC_EXT)


def build_output(entries: list[dict], mini_only: bool) -> dict:
    endpoints: list[dict] = []
    assets: list[dict] = []
    seen_hosts: set[str] = set()

    for entry in entries:
        if not host_allowed(entry, mini_only):
            continue

        host = entry.get("host", "")
        path = entry.get("path", "")

        if host not in seen_hosts:
            seen_hosts.add(host)
            asset_id = hashlib.sha256(f"domain:{host}".encode("utf-8")).hexdigest()
            assets.append(
                {
                    "id": asset_id,
                    "type": "domain",
                    "subtype": "wechat_api",
                    "host": host,
                    "source": "wechat_capture",
                    "tags": ["api", "wechat"],
                }
            )

        if mini_only and is_static(path):
            continue

        url = f"https://{host}{path}"
        endpoint_id = hashlib.sha256(
            f"{entry.get('method', 'GET')}:{url}".encode("utf-8")
        ).hexdigest()
        endpoints.append(
            {
                "id": endpoint_id,
                "url": url,
                "method": entry.get("method", "GET"),
                "params": [],
                "auth_state": "unknown",
                "role": "",
                "data_sensitivity": "",
                "monetization_tags": [],
                "priority": 0,
                "extra": {
                    "source": "wechat_capture",
                    "resp_code": entry.get("resp_code"),
                    "resp_len": entry.get("resp_len"),
                    "req_ct": entry.get("req_ct"),
                    "resp_ct": entry.get("resp_ct"),
                    "req_body": entry.get("req_body"),
                },
            }
        )

    return {"endpoints": endpoints, "assets": assets}


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse mitmproxy mini_req.log")
    parser.add_argument(
        "--log",
        default=os.path.join(os.environ.get("TEMP", "/tmp"), "mini_req.log"),
    )
    parser.add_argument("--out", default="")
    parser.add_argument("--mini-only", action="store_true")
    args = parser.parse_args()

    entries = load_entries(args.log)
    output = build_output(entries, args.mini_only)
    text = json.dumps(output, ensure_ascii=False, indent=2)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(args.out)
    else:
        print(text)


if __name__ == "__main__":
    main()