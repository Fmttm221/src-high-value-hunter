# Quickstart

## 1. 安装

```powershell
cd 'D:\dsh work\src-high-value-hunter'
uv venv .venv
uv pip install --python .\.venv\Scripts\python.exe --no-cache "mcp<2" httpx pyyaml
```

## 2. 配置

复制并填写：

```text
config.yaml
config/targets.yaml
config/identities.yaml
config/accounts.yaml
```

## 3. 注册 MCP

参考：

```text
dsh/recon-hub.yml
dsh/mcp.config.example.json
```

## 4. 启动

```powershell
.\scripts\run-recon-hub.ps1
```

## 5. 标准流程

```text
recon_phase("passive", ["example.com"])
recon_phase("probe", ["example.com"])
recon_phase("active", ["example.com"])
recon_phase("exposure", ["example.com"])
recon_phase("js", [], {"urls": ["https://example.com/app.js"]})
recon_phase("code", ["example.com"])
recon_phase("cloud", ["example"])
recon_ingest_endpoints([...])
recon_phase("vuln")
recon_phase("chain")
recon_report(name="final")
recon_export_db(collection="assets")
recon_export_db(collection="findings")
recon_export_db(collection="chains")
```

## 6. 同步到 Kali

```powershell
.\scripts\sync-to-kali.ps1
```

## 7. 注意

- 第三方 MCP 需要自行配置
- 主动测试前必须有 throttle profile
- 遇到验证码 / 滑块 / IP 封禁，暂停并请求人工协助