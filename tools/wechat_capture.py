"""
WeChat Mini Program capture helper.

Usage:
  python tools/wechat_capture.py start [port] [webport]
  python tools/wechat_capture.py headless [port]
  python tools/wechat_capture.py status
  python tools/wechat_capture.py stop
  python tools/wechat_capture.py proxy on|off

Notes:
  - Runs on the Windows host where WeChat runs.
  - mitmweb UI: http://127.0.0.1:<webport>
  - Request log: %TEMP%/mini_req.log
  - Full flow: %TEMP%/mitm_wechat.flow
"""
import ctypes
import os
import shutil
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ACTION = sys.argv[1] if len(sys.argv) > 1 else "status"
PORT = sys.argv[2] if len(sys.argv) > 2 else "8088"
WEBPORT = sys.argv[3] if len(sys.argv) > 3 else "8081"

TEMP = os.environ.get("TEMP", os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp"))
FLOW_FILE = os.path.join(TEMP, "mitm_wechat.flow")
LOG_FILE = os.path.join(TEMP, "mini_req.log")
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
MINI_LOG_ADDON = os.path.join(TOOLS_DIR, "mini_log.py")

MITMDUMP = shutil.which("mitmdump")
MITMWEB = shutil.which("mitmweb")


def set_system_proxy(enabled: bool, host: str = "127.0.0.1", port: str = PORT) -> None:
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1 if enabled else 0)
            if enabled:
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, f"{host}:{port}")
        for option in (39, 37):
            ctypes.windll.Wininet.InternetSetOptionW(None, option, None, 0)
        if enabled:
            print(f"[*] system proxy set to {host}:{port}")
        else:
            print("[*] system proxy disabled")
    except Exception as exc:
        print(f"[!] failed to set system proxy: {exc}")


def wait_for_ca(timeout: int = 10) -> bool:
    ca = os.path.join(os.path.expanduser("~"), ".mitmproxy", "mitmproxy-ca-cert.cer")
    started = time.time()
    while not os.path.exists(ca) and time.time() - started < timeout:
        time.sleep(0.5)
    return os.path.exists(ca)


def install_ca() -> bool:
    ca = os.path.join(os.path.expanduser("~"), ".mitmproxy", "mitmproxy-ca-cert.cer")
    if not os.path.exists(ca):
        print("[!] mitmproxy CA not found")
        return False
    ps = (
        "$c=New-Object System.Security.Cryptography.X509Certificates.X509Certificate2"
        f"('{ca}');"
        "$s=New-Object System.Security.Cryptography.X509Certificates.X509Store('Root','CurrentUser');"
        "$s.Open('ReadWrite');"
        "if(-not($s.Certificates|Where-Object{$_.Thumbprint -eq $c.Thumbprint})){$s.Add($c);"
        "Write-Output 'CA installed'}else{Write-Output 'CA exists'};"
        "$s.Close()"
    )
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    print("[*] mitmproxy CA checked in CurrentUser Root store")
    return True


def start(use_web: bool = True) -> None:
    if not MITMDUMP and not MITMWEB:
        print("[!] mitmdump/mitmweb not found in PATH")
        return

    env = dict(os.environ, MINI_LOG_FILE=LOG_FILE)
    if use_web and MITMWEB:
        cmd = [MITMWEB, "-p", PORT, "--web-port", WEBPORT, "-s", MINI_LOG_ADDON]
        print(f"[*] starting mitmweb on {PORT}, web UI http://127.0.0.1:{WEBPORT}")
    else:
        cmd = [MITMDUMP, "-p", PORT, "-s", MINI_LOG_ADDON]
        print(f"[*] starting mitmdump on {PORT}")

    subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    wait_for_ca()
    install_ca()
    set_system_proxy(True, "127.0.0.1", PORT)
    print(f"[*] flow file: {FLOW_FILE}")
    print(f"[*] request log: {LOG_FILE}")
    print("[+] open or refresh the WeChat Mini Program and trigger requests")


def stop() -> None:
    subprocess.run(["taskkill", "/F", "/IM", "mitmdump.exe"], capture_output=True)
    subprocess.run(["taskkill", "/F", "/IM", "mitmweb.exe"], capture_output=True)
    set_system_proxy(False)
    print("[-] mitmproxy stopped, system proxy restored")


def proxy(action: str) -> None:
    if action == "off":
        set_system_proxy(False)
        print("[-] system proxy off; mitm still running")
    elif action == "on":
        set_system_proxy(True, "127.0.0.1", PORT)
        print(f"[+] system proxy restored to 127.0.0.1:{PORT}")
    else:
        status()


def status() -> None:
    tasks = subprocess.run(["tasklist"], capture_output=True, text=True).stdout.lower()
    print(f"[*] mitmweb: {'running' if 'mitmweb.exe' in tasks else 'stopped'}")
    print(f"[*] mitmdump: {'running' if 'mitmdump.exe' in tasks else 'stopped'}")
    if os.path.exists(LOG_FILE):
        count = sum(1 for _ in open(LOG_FILE, encoding="utf-8"))
        print(f"[*] requests captured: {count}")
        print(f"[*] request log: {LOG_FILE}")
        print(f"[*] flow file: {FLOW_FILE}")
    else:
        print("[*] no request log yet")


if __name__ == "__main__":
    action = ACTION.lower()
    if action == "start":
        start(use_web=True)
    elif action == "headless":
        start(use_web=False)
    elif action == "stop":
        stop()
    elif action == "proxy":
        proxy(sys.argv[2].lower() if len(sys.argv) > 2 else "status")
    else:
        status()