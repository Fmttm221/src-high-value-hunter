import argparse
import json
import sys

import httpx


def _headers(secret: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {secret}"} if secret else {}


def _api(api: str, secret: str, path: str, method: str = "GET", payload: dict | None = None):
    url = api.rstrip("/") + path
    with httpx.Client(timeout=10.0) as client:
        if method == "GET":
            resp = client.get(url, headers=_headers(secret))
        else:
            resp = client.put(url, headers=_headers(secret), json=payload)
        resp.raise_for_status()
        return resp.json()


def status(api: str, secret: str) -> None:
    data = _api(api, secret, "/proxies")
    proxies = data.get("proxies", {})
    for name, info in proxies.items():
        if info.get("type") in ("Selector", "URLTest", "Fallback", "LoadBalance"):
            print(f"{name}: {info.get('now')}")


def list_group(api: str, secret: str, group: str) -> None:
    data = _api(api, secret, f"/proxies/{group}")
    print(f"group: {group}")
    print(f"now: {data.get('now')}")
    for item in data.get("all", []):
        print(f"  - {item}")


def switch(api: str, secret: str, group: str, node: str) -> None:
    _api(api, secret, f"/proxies/{group}", method="PUT", payload={"name": node})
    print(f"switched {group} -> {node}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Clash controller helper")
    parser.add_argument("--api", default="http://127.0.0.1:9090")
    parser.add_argument("--secret", default="")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status")

    p_list = sub.add_parser("list")
    p_list.add_argument("group")

    p_switch = sub.add_parser("switch")
    p_switch.add_argument("group")
    p_switch.add_argument("node")

    args = parser.parse_args()
    try:
        if args.command == "status":
            status(args.api, args.secret)
        elif args.command == "list":
            list_group(args.api, args.secret, args.group)
        elif args.command == "switch":
            switch(args.api, args.secret, args.group, args.node)
    except Exception as exc:
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()