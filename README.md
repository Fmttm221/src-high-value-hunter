# src-high-value-hunter

面向授权 SRC 的高价值漏洞挖掘 skill + recon-hub MCP。

核心目标只有一个：

> 挖出高价值、可提交、能牟利的漏洞或完整漏洞链。

## 特性

- L0-L6 完整流程
- 被动 / 主动资产收集
- WAF 探测与自适应限速
- hexstrike 工具映射与输出解析
- assets / endpoints / findings / chains 持久化
- 漏洞链建议
- Markdown 报告生成
- 微信小程序抓包分析
- 经验库：平时不加载，命中关键词才读取
- Clash / 代理切换支持

## 架构

```text
L0 目标与边界
  ↓
L1 资产收集
  ↓
L2 探针与暴露面
  ↓
L3 业务 / API / 认证建模
  ↓
L4 高价值漏洞发现
  ↓
L5 验证与漏洞链
  ↓
L6 报告与提交
```

## 目录结构

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

## 安装

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

## 配置

复制：

```text
config.example.yaml -> config.yaml
config/targets.yaml
config/identities.yaml
config/accounts.yaml
```

填写：

- 目标资产
- 牟利标签
- provider key
- 账号身份

## dsh MCP 注册

参考：

```text
dsh/recon-hub.yml
dsh/mcp.config.example.json
```

第三方 MCP：

- hexstrike
- chrome-devtools
- burp
- ssh-mcp
- wsl

需要用户自行安装和配置。

## 启动

```powershell
.\scripts\run-recon-hub.ps1
```

或：

```powershell
$env:PYTHONPATH = ".\src"
.\.venv\Scripts\python.exe -m recon_hub.server --config .\config.yaml
```

## 标准流程

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

## 微信小程序抓包

```powershell
python tools/wechat_capture.py start
# 用户在微信中操作小程序
python tools/wechat_capture.py stop
python scripts/parse_mini_log.py --out wechat_output.json --mini-only
```

然后把输出写入 recon-hub：

```text
recon_ingest_endpoints
recon_ingest_assets
```

## 经验库

```powershell
python scripts/experience.py search "<关键词>"
python scripts/experience.py add "<关键词>"
```

规则：

- 平时不加载
- 命中关键词才读取
- 报告提交后才写入
- 只写验证过的经验

## Clash / 网络

```powershell
python scripts/clash.py status
python scripts/clash.py list GLOBAL
python scripts/clash.py switch GLOBAL "<节点名>"
```

`config.yaml`：

```yaml
network:
  proxy: ""
  clash_api: "http://127.0.0.1:9090"
  clash_secret: ""
  clash_group: "GLOBAL"
```

## 开发

```bash
make compile
make smoke
```

## 许可

MIT