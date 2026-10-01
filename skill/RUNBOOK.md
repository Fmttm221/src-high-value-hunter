# src-high-value-hunter Runbook

## 目标

只挖高价值、可提交、能牟利的漏洞或完整链。

## 前置

- recon-hub MCP 已注册
- hexstrike / chrome-devtools / burp / ssh-mcp 已配置
- config/targets.yaml 已填目标
- config/identities.yaml / accounts.yaml 已填身份
- config.yaml 已填 provider key

## L0 目标与边界

读取：

```text
config/targets.yaml
config/identities.yaml
config/accounts.yaml
```

确认：

- active_profile
- 目标列表
- 排除项
- 牟利标签

## L1 资产收集

```text
recon_phase("passive", targets)
recon_phase("probe", targets)
recon_phase("active", targets)
recon_phase("exposure", targets)
recon_phase("js", [], {"urls": [...]})
recon_phase("code", targets)
recon_phase("cloud", targets)
```

每批任务：

```text
recon_hexstrike_plan(task_type, target)
  ↓
调用 hexstrike MCP / execute_command
  ↓
recon_hexstrike_ingest(task_type, target, output)
  ↓
recon_task_update(task_id, status="success", result={...})
```

## L2 暴露面

查看：

```text
recon_list_assets
recon_stats
```

重点：

- 管理后台
- API 文档
- Actuator / Jenkins / Grafana
- 云存储
- CI/CD

## L3 建模

把入口写入 endpoints 表：

```text
recon_ingest_endpoints([...])
recon_list_endpoints
```

字段：

```text
url
method
params
auth_state
role
data_sensitivity
monetization_tags
priority
extra
```

## L4 高价值漏洞发现

```text
recon_phase("vuln")
```

对每个任务：

```text
recon_hexstrike_plan(task_type, target)
  ↓
调用 hexstrike MCP
  ↓
recon_hexstrike_ingest(task_type, target, output)
  ↓
recon_ingest_findings
  ↓
recon_task_update
```

## L5 链

```text
recon_phase("chain")
```

或手动：

```text
recon_chain_suggest
recon_ingest_chains
recon_list_chains
```

## L6 报告

```text
recon_report(name="final")
recon_export_db(collection="assets")
recon_export_db(collection="endpoints")
recon_export_db(collection="findings")
recon_export_db(collection="chains")
```

## 人机协作

遇到以下情况暂停：

- 滑块
- 验证码
- 短信 / 邮箱验证码
- 风控
- 账号锁定
- IP 封禁
- 需要 admin 账号

## 输出

```text
data/recon.db
data/exports/
data/reports/
```

## 提交门禁

- STANDALONE + 高影响 -> 提交
- CHAIN_COMPLETE -> 整条链提交
- CHAIN_INCOMPLETE -> 不提交
- 低危单独 -> 不提交
## 微信小程序资产

L1 检测：

```text
recon_wechat_detect(urls)
recon_phase("wechat", urls)
```

如果发现 `wechat_miniprogram`：

1. 标记为 `human_assisted`
2. 默认最后处理
3. 等自动化流程结束后，请求用户协助
4. 启动 `tools/wechat_capture.py`
5. 解析日志并写回 endpoints / assets
6. 再进入 L3/L4