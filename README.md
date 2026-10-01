# src-high-value-hunter

闈㈠悜鎺堟潈 SRC 鐨勯珮浠峰€兼紡娲炴寲鎺?skill + recon-hub MCP銆?
鏍稿績鐩爣鍙湁涓€涓細

> 鎸栧嚭楂樹环鍊笺€佸彲鎻愪氦銆佽兘鐗熷埄鐨勬紡娲炴垨瀹屾暣婕忔礊閾俱€?
## 鐗规€?
- L0-L6 瀹屾暣娴佺▼
- 琚姩 / 涓诲姩璧勪骇鏀堕泦
- WAF 鎺㈡祴涓庤嚜閫傚簲闄愰€?- hexstrike 宸ュ叿鏄犲皠涓庤緭鍑鸿В鏋?- assets / endpoints / findings / chains 鎸佷箙鍖?- 婕忔礊閾惧缓璁?- Markdown 鎶ュ憡鐢熸垚
- 寰俊灏忕▼搴忔姄鍖呭垎鏋?- 缁忛獙搴擄細骞虫椂涓嶅姞杞斤紝鍛戒腑鍏抽敭璇嶆墠璇诲彇
- Clash / 浠ｇ悊鍒囨崲鏀寔

## 鏋舵瀯

```text
L0 鐩爣涓庤竟鐣?  鈫?L1 璧勪骇鏀堕泦
  鈫?L2 鎺㈤拡涓庢毚闇查潰
  鈫?L3 涓氬姟 / API / 璁よ瘉寤烘ā
  鈫?L4 楂樹环鍊兼紡娲炲彂鐜?  鈫?L5 楠岃瘉涓庢紡娲為摼
  鈫?L6 鎶ュ憡涓庢彁浜?```

## 鐩綍缁撴瀯

```text
skill/
  SKILL.md
  RUNBOOK.md
  playbooks/
src/recon_hub/
  server.py
  config.py
  storage.py
  models.py
  providers/
  tools/
tools/
  wechat_capture.py
  mini_log.py
scripts/
  install.ps1
  install.sh
  run-recon-hub.ps1
  sync-to-kali.ps1
  clash.py
  experience.py
  parse_mini_log.py
experience/
  INDEX.md
  README.md
docs/
  quickstart.md
  provider-registration.md
dsh/
  recon-hub.yml
  mcp.config.example.json
```

## 瀹夎

Windows:

```powershell
git clone <repo>
cd src-high-value-hunter
.\scripts\install.ps1
```

Linux / macOS:

```bash
git clone <repo>
cd src-high-value-hunter
./scripts/install.sh
```

## 閰嶇疆

澶嶅埗锛?
```text
config.example.yaml -> config.yaml
config/targets.yaml
config/identities.yaml
config/accounts.yaml
```

濉啓锛?
- 鐩爣璧勪骇
- 鐗熷埄鏍囩
- provider key
- 璐﹀彿韬唤

## dsh MCP 娉ㄥ唽

鍙傝€冿細

```text
dsh/recon-hub.yml
dsh/mcp.config.example.json
```

绗笁鏂?MCP锛?
- hexstrike
- chrome-devtools
- burp
- ssh-mcp
- wsl

闇€瑕佺敤鎴疯嚜琛屽畨瑁呭拰閰嶇疆銆?
## 鍚姩

```powershell
.\scripts\run-recon-hub.ps1
```

鎴栵細

```powershell
$env:PYTHONPATH = ".\src"
.\.venv\Scripts\python.exe -m recon_hub.server --config .\config.yaml
```

## 鏍囧噯娴佺▼

```text
recon_phase("passive", targets)
recon_phase("probe", targets)
recon_phase("active", targets)
recon_phase("exposure", targets)
recon_phase("js", [], {"urls": [...]})
recon_phase("code", targets)
recon_phase("cloud", targets)
recon_phase("wechat", urls)
recon_ingest_endpoints([...])
recon_phase("vuln")
recon_phase("chain")
recon_report(name="final")
recon_export_db(collection="assets")
recon_export_db(collection="endpoints")
recon_export_db(collection="findings")
recon_export_db(collection="chains")
```

## 寰俊灏忕▼搴忔姄鍖?
```powershell
python tools/wechat_capture.py start
# 鐢ㄦ埛鍦ㄥ井淇′腑鎿嶄綔灏忕▼搴?python tools/wechat_capture.py stop
python scripts/parse_mini_log.py --out wechat_output.json --mini-only
```

鐒跺悗鎶婅緭鍑哄啓鍏?recon-hub锛?
```text
recon_ingest_endpoints
recon_ingest_assets
```

## 缁忛獙搴?
```powershell
python scripts/experience.py search "<鍏抽敭璇?"
python scripts/experience.py add "<鍏抽敭璇?"
```

瑙勫垯锛?
- 骞虫椂涓嶅姞杞?- 鍛戒腑鍏抽敭璇嶆墠璇诲彇
- 鎶ュ憡鎻愪氦鍚庢墠鍐欏叆
- 鍙啓楠岃瘉杩囩殑缁忛獙

## Clash / 缃戠粶

```powershell
python scripts/clash.py status
python scripts/clash.py list GLOBAL
python scripts/clash.py switch GLOBAL "<鑺傜偣鍚?"
```

`config.yaml`锛?
```yaml
network:
  proxy: ""
  clash_api: "http://127.0.0.1:9090"
  clash_secret: ""
  clash_group: "GLOBAL"
```

## 寮€鍙?
```bash
make compile
make smoke
```

## 璁稿彲

MIT