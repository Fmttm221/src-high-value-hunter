# Quickstart

## 1. 瀹夎

```powershell
cd 'D:\dsh work\src-high-value-hunter'
uv venv .venv
uv pip install --python .\.venv\Scripts\python.exe --no-cache "mcp<2" httpx pyyaml
```

## 2. 閰嶇疆

澶嶅埗骞跺～鍐欙細

```text
config.yaml
config/targets.yaml
config/identities.yaml
config/accounts.yaml
```

## 3. 娉ㄥ唽 MCP

鍙傝€冿細

```text
dsh/recon-hub.yml
dsh/mcp.config.example.json
```

## 4. 鍚姩

```powershell
.\scripts\run-recon-hub.ps1
```

## 5. 鏍囧噯娴佺▼

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

## 6. 鍚屾鍒?Kali

```powershell
.\scripts\sync-to-kali.ps1
```

## 7. 娉ㄦ剰

- 绗笁鏂?MCP 闇€瑕佽嚜琛岄厤缃?- 涓诲姩娴嬭瘯鍓嶅繀椤绘湁 throttle profile
- 閬囧埌楠岃瘉鐮?/ 婊戝潡 / IP 灏佺锛屾殏鍋滃苟璇锋眰浜哄伐鍗忓姪