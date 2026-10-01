"""
mitmproxy addon: write request summaries to JSONL.
Environment:
  MINI_LOG_FILE default: %TEMP%/mini_req.log
"""
import json
import os
import time

from mitmproxy import http

OUTFILE = os.environ.get(
    "MINI_LOG_FILE",
    os.path.join(os.environ.get("TEMP", "/tmp"), "mini_req.log"),
)


class MiniLog:
    def __init__(self):
        try:
            open(OUTFILE, "w", encoding="utf-8").close()
        except Exception:
            pass

    def response(self, flow: http.HTTPFlow):
        try:
            host = flow.request.pretty_host
            if host in ("servicewechat.com", "mp.weixin.qq.com", "res.wx.qq.com"):
                return
            content_type = ""
            if flow.response:
                content_type = flow.response.headers.get("content-type", "")
            entry = {
                "time": time.strftime("%H:%M:%S"),
                "method": flow.request.method,
                "host": host,
                "path": flow.request.path[:500],
                "req_ct": flow.request.headers.get("content-type", ""),
                "req_body": (
                    flow.request.get_text(strict=False)[:2000]
                    if flow.request.method in ("POST", "PUT", "PATCH")
                    else ""
                ),
                "resp_code": flow.response.status_code if flow.response else None,
                "resp_len": len(flow.response.content) if flow.response else 0,
                "resp_ct": content_type[:100],
            }
            with open(OUTFILE, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass


addons = [MiniLog()]