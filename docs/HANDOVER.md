# src-high-value-hunter 交接文档

## 1. 项目概况

项目名称：`src-high-value-hunter`

目标：面向授权 SRC 的高价值漏洞挖掘 skill + recon-hub MCP。

核心原则：

- 只挖高价值、可提交、能牟利的漏洞或完整链
- 被动优先，主动其次
- 证据优先，最小化 PoC
- 低危不单独提交，只作为链组件
- 需要人工介入时暂停并请求协助

仓库：

```text
https://github.com/Fmttm221/src-high-value-hunter
```

## 2. 当前已完成

### 2.1 Skill 流程

已完成 L0-L6 文档：

```text
skill/SKILL.md
skill/RUNBOOK.md
skill/playbooks/wechat.md
skill/playbooks/experience.md
skill/playbooks/network.md
```

### 2.2 recon-hub MCP

已实现：

- `recon_phase`：passive / probe / active / exposure / js / code / cloud / vuln / chain / wechat
- Provider 查询
- hexstrike 映射与输出解析
- assets / endpoints / findings / chains 持久化
- 任务状态管理
- Markdown 报告生成
- JSONL / JSON 导出
- 统计

### 2.3 Provider

已接入：

```text
crtsh
certspotter
urlscan
otx
wayback
shodan
censys
quake
zoomeye
hunter
netlas
virustotal
securitytrails
greynoise
abuseipdb
ipinfo
github
```

可用情况：

- 可用：certspotter、urlscan、netlas、abuseipdb、ipinfo、github
- 需要 key：urlscan、github、netlas、abuseipdb、ipinfo
- 有限制：shodan（免费无查询额度）、censys（免费无 API 权限）、otx（限流）
- 不可用：quake（注册 404）、zoomeye（v1 502）、hunter（无 API 权限）、virustotal（注册失败）、securitytrails（企业邮箱）、greynoise（企业 API）

### 2.4 持久化

SQLite 表：

```text
assets
endpoints
findings
chains
tasks
throttle_profiles
sessions
accounts
state
provider_cache
evidence_index
```

### 2.5 hexstrike 映射

支持：

```text
subdomain_bruteforce
dns_resolve
http_probe
waf_detect
tech_detect
port_scan
crawl
sqli
xss
lfi
cve
ssrf
graphql
jwt
```

### 2.6 微信小程序抓包

已完成：

```text
tools/wechat_capture.py
tools/mini_log.py
scripts/parse_mini_log.py
skill/playbooks/wechat.md
```

已验证：

- mitmweb 启动
- 系统代理切换
- 微信小程序流量抓取
- 日志解析
- 资产和 endpoint 写回

### 2.7 经验库

已完成：

```text
experience/INDEX.md
experience/README.md
scripts/experience.py
skill/playbooks/experience.md
```

规则：

- 平时不加载
- 命中关键词才读取
- 报告提交后才写入
- 只写验证过的经验

### 2.8 Clash / 网络

已完成：

```text
scripts/clash.py
skill/playbooks/network.md
config.yaml 的 network 段
```

recon-hub 支持通过环境变量设置：

```text
HTTP_PROXY
HTTPS_PROXY
```

### 2.9 GitHub

已完成：

- 仓库初始化
- 首次提交
- README 编码修复
- 敏感文件清理
- 示例配置

### 2.10 测试

```text
tests/test_smoke.py
18 个测试
compileall: OK
smoke tests: OK
```

## 3. 待完善工作

### P0 阻塞项

1. Clash 控制器与代理拓扑未打通
   - `127.0.0.1:9090/proxies` 返回 502
   - 需要正确端口和 secret
   - Kali 当前无法访问 Windows Clash
   - recon-hub 还没有真正走 Clash

2. L4 执行器未自动化
   - `recon_phase("vuln")` 只生成任务
   - 实际 hexstrike / CLI 执行仍需人工编排
   - 部分 hexstrike 工具参数不匹配，例如 httpx_probe 需要文件输入

3. L3 建模未自动化
   - endpoints 需要手工 ingest
   - 还没有从 Burp / Chrome / JS 自动提取 endpoint 模型
   - 没有参数、角色、认证状态的自动填充

4. 账号注册 / 登录 / 会话自动化未实现
   - L0 已定义账号
   - 但注册、登录、验证码、滑块、会话保存还没有代码实现

5. 微信小程序真实业务 API 尚未深挖
   - 目前只抓到首页静态资源和微信运行时
   - 未抓到登录、对局、商城、支付等业务 API
   - 需要用户实际操作后继续抓包

### P1 重要项

6. Provider 可用性补强
   - 继续找可用免费 provider
   - 补充 GitLab、PublicWWW、grep.app 等
   - 处理 OTX 429、crt.sh 502、Wayback 连接失败
   - 增加 provider 级代理和重试策略

7. 报告系统不完善
   - 当前是基础 Markdown
   - 缺少严重性评分、CVSS、去重、Burp issue 创建
   - 缺少 assets / endpoints 附录
   - 报告模板仍为 TBD

8. Chain 系统不完善
   - 目前是硬编码规则
   - 缺少证据关联
   - 缺少链状态自动更新
   - 缺少更多链模式

9. 经验库未接入报告流程
   - 目前只有手动脚本
   - 需要在报告提交后自动触发写入
   - 需要质量门禁和过期机制

10. 状态 / 任务执行器未实现
    - tasks 表只是记录
    - 没有后台 worker
    - 没有断点续跑

11. 错误处理 / 限速 / 代理 fallback
    - 目前只有基础重试
    - 需要 provider 级 backoff
    - 需要 IP 被封后的自动降级

12. 目标配置加载
    - `config/targets.yaml` 已存在
    - 但 skill 还没有自动读取 active_profile

13. 文档与可移植性
    - `dsh/recon-hub.yml` 使用绝对路径
    - `scripts/sync-to-kali.ps1` 硬编码 IP 和路径
    - 需要改成配置化

### P2 优化项

14. JS 分析增强
    - Source Map 还原
    - secret 验证
    - WebSocket / API 前缀提取

15. 移动端分析
    - `recon_mobile` 目前是占位
    - 需要 APK 下载、jadx、apktool、MobSF

16. 云资产分析增强
    - 目前只有基础 S3 bucket 检查
    - 需要多云枚举、权限验证

17. API 专项
    - GraphQL / gRPC / WebSocket / Webhook
    - 需要更完整的自动化

18. 测试增强
    - 增加 integration test
    - 增加 provider mock test
    - 增加 MCP tool schema test

19. 发布增强
    - GitHub Release
    - Docker 镜像
    - PyPI 包

## 4. 已知问题

- crt.sh 经常 502
- OTX 经常 429
- Wayback 偶发连接失败
- Shodan 免费 key 无查询额度
- Censys 免费用户无 API 权限
- Quake 注册页 404
- ZoomEye v1 API 502
- Hunter 免费账号无 API 权限
- VirusTotal 注册失败
- SecurityTrails 仅企业邮箱
- GreyNoise API 需企业邮箱
- Clash 控制器 9090 返回 502
- Kali 无法访问 Windows Clash
- 微信小程序业务 API 未抓到
- 部分 hexstrike 工具参数不匹配
- 报告模板未最终确定

## 5. 环境与部署

### 本地

```text
D:\dsh work\src-high-value-hunter
```

### Kali

```text
~/src-high-value-hunter
```

### dsh MCP

```text
D:\dsh work\src-hunting\dsh-mcp.yml
```

### recon-hub 启动

```powershell
$env:PYTHONPATH = ".\src"
.\.venv\Scripts\python.exe -m recon_hub.server --config .\config.yaml
```

### 同步到 Kali

```powershell
.\scripts\sync-to-kali.ps1
```

## 6. 关键文件

```text
skill/SKILL.md
skill/RUNBOOK.md
src/recon_hub/server.py
src/recon_hub/storage.py
src/recon_hub/config.py
src/recon_hub/tools/phase.py
src/recon_hub/tools/hexstrike_map.py
src/recon_hub/tools/hexstrike_parse.py
tools/wechat_capture.py
scripts/parse_mini_log.py
scripts/experience.py
scripts/clash.py
config.example.yaml
config/targets.example.yaml
config/identities.example.yaml
config/accounts.example.yaml
dsh/recon-hub.yml
```

## 7. 常用命令

```powershell
# 安装
.\scripts\install.ps1

# 测试
python tests\test_smoke.py

# 同步到 Kali
.\scripts\sync-to-kali.ps1

# 微信抓包
python tools\wechat_capture.py start
python tools\wechat_capture.py stop
python scripts\parse_mini_log.py --out wechat_output.json --mini-only

# 经验库
python scripts\experience.py search "<关键词>"
python scripts\experience.py add "<关键词>"

# Clash
python scripts\clash.py status
python scripts\clash.py list GLOBAL
python scripts\clash.py switch GLOBAL "<节点名>"
```

## 8. 安全注意事项

- 不要把 `config.yaml`、`config/identities.yaml`、`config/accounts.yaml`、`config/targets.yaml` 提交到 Git
- 不要把真实 API key、手机号、邮箱、Token 写进文档
- 对话里出现过的 GitHub Token 建议吊销并重新生成
- 报告中的 PII 必须脱敏
- 只对授权目标进行测试
- 主动测试前必须有 throttle profile

## 9. 下一步建议

优先级从高到低：

1. 打通 Clash 控制器与代理
2. 实现 L3 endpoint 自动建模
3. 实现 L4 任务执行器
4. 实现账号注册 / 登录 / 会话自动化
5. 完成微信小程序业务 API 抓取
6. 完善报告系统
7. 完善 chain 系统和经验库
8. 补充 provider 和测试

## 10. 交接清单

- [ ] 确认 GitHub Token 已轮换
- [ ] 确认 Clash 控制器端口和 secret
- [ ] 确认 Kali 能访问 Windows Clash
- [ ] 确认 provider key 仍在本地 config.yaml
- [ ] 确认 dsh MCP 配置可用
- [ ] 确认微信抓包代理可切换
- [ ] 确认报告模板后续补充
- [ ] 确认经验库第一条真实经验