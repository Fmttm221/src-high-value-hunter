---
name: src-high-value-hunter
version: 0.3
description: 面向授权 SRC 的高价值漏洞挖掘 skill。围绕牟利判定模型，编排 Kali、Chrome DevTools、Burp、recon-hub，按 L0-L6 流程发现、验证、串联并提交高价值漏洞。
runtime: dsh
tags:
  - bugbounty
  - src
  - web
  - api
  - cloud
  - high-value
tools:
  - hexstrike
  - chrome-devtools
  - burp
  - ssh-mcp
  - wsl
  - pwsh
  - recon-hub
---

# 0. 核心目标

只做一件事：挖出高价值、可提交、能牟利的漏洞或完整漏洞链。

# 1. 核心公理：牟利判定模型 V1

- 能独立牟利 / 独立造成高影响 -> STANDALONE，可单独提交
- 不能独立牟利，但能进入牟利链 -> CHAIN_ONLY，不单独提交，但必须记录和尝试串联
- 两者皆无 -> DISCARD，不投入

# 2. 硬规则

- 用户提供的目标默认已授权
- 不做授权确认、不要求授权书
- 被动优先，主动其次
- 主动测试前先读 throttle_profile
- 不硬刚滑块、验证码、风控
- 不扩大数据访问，不破坏，不拖库
- 低危不单独提交，只作为链组件
- 没有证据的发现不升级
- 人机协作优先

# 3. 工作流总览

```text
L0 目标与边界
  ↓
L1-P 被动资产发现
  ↓
L1.5 探针与限速
  ↓
L1-A 主动资产发现
  ↓
L1-C JS / 云 / 仓库 / 移动端
  ↓
L1-N 归一化、去重、打分
  ↓
L2 存活指纹与暴露面
  ↓
L3 业务 / API / 认证建模
  ↓
L4 高价值漏洞发现
  ↓
L5 验证与漏洞链
  ↓
L6 报告与提交
```

# 4. L0 目标与边界

## 4.1 目的

1. 打谁：目标资产清单
2. 不打谁：技术排除项
3. 怎么打：被动 / 主动
4. 用什么身份打：手机号、邮箱、账号、角色、Token、Cookie

L0 不做授权确认。用户提供的目标默认已授权。

## 4.2 目标类型

root_domain, subdomain, url, cidr, ip, mobile_app, repo, cloud_account, api_spec

## 4.3 牟利标签

payment, account, admin, api, upload, export, cloud, cicd, pii, money, internal

边缘资产不丢弃，进入边缘队列。

## 4.4 配置

targets.yaml、identities.yaml、accounts.yaml。

账号：

- acc1：普通用户，租户 A
- acc2：普通用户，租户 B
- admin：不提供，需要时请求用户

## 4.5 账号状态机

```text
UNREGISTERED -> REGISTERING -> WAITING_HUMAN -> LOGGED_IN -> SESSION_VALID -> LOCKED / EXPIRED
```

## 4.6 人机协作触发条件

滑块、图形验证码、短信验证码、邮箱验证码、风控、账号锁定、手动登录、实名/人脸、IP 被 WAF 封禁。

请求格式：

```json
{
  "type": "captcha | slider | sms_otp | email_otp | manual_login | risk_control | ip_blocked | admin_needed | risky_action",
  "account": "acc1",
  "host": "",
  "url": "",
  "screenshot": "",
  "message": "",
  "timeout": 300
}
```

## 4.7 规则

- 用户提供的目标默认已授权
- 不预设速率，速率由 L1.5 / L2 探针决定
- 默认自动注册
- 遇到滑块、验证码、风控不硬刚
- 注册 / 登录失败 3 次就停
- 边缘资产不丢弃
- 低危漏洞不单独提交
- 需要 admin 账号时请求用户提供
- 检测到 IP 被封 -> 暂停，请求用户切换热点

## 4.8 产出

targets.yaml, identities.yaml, accounts.yaml, scope.json, edge_queue.jsonl

## 4.9 门禁

1. 至少有一个目标
2. 排除项明确
3. 测试模式明确
4. 需要登录态测试时，至少一个身份配置可用
5. 目标标签已打
6. 边缘资产已进入边缘队列

# 5. L1 资产收集

## 5.1 目的

从 L0 目标出发，建立完整资产清单，为 L2-L4 提供输入。L1 只做资产发现、轻量存活验证、技术栈初判、归一化、去重、打分。L1 不做漏洞验证。

## 5.2 原则

- 被动优先，主动其次
- 主动前先读 throttle_profile
- 边缘资产不丢弃
- 所有结果标准化、去重、打分
- 遇到 IP 封禁 -> 暂停，请求用户切热点
- provider 失败不中断，降级到下一个

## 5.3 子层

L1-P 被动资产发现
L1.5 WAF 探测 + 自适应限速
L1-A 主动资产发现
L1-C JS / 云 / 仓库 / 移动端
L1-N 归一化、去重、打分

规则：

- L1-P 不碰目标
- L1.5 生成 throttle_profile
- L1-A 只主动测试已有 throttle_profile 的 host
- L1-A 新发现的主机 -> 排队回 L1.5 补探针
- L1-A 遇到 IP 封禁 -> 暂停，请求用户切热点
- L1-C 中的 JS 下载、移动 App 下载也要遵守 throttle_profile

## 5.4 被动轮

不直接请求目标，只查第三方数据。数据源类别：证书透明度、子域/DNS 历史、网络空间测绘、历史 URL、代码仓库、云关键词、归档 JS。

产出：passive_assets.jsonl

## 5.5 主动轮

直接请求目标或 DNS。顺序：

1. 读取 throttle_profile
2. 没有 profile -> 先跑 L1.5 探针
3. 子域爆破
4. DNS 解析
5. HTTP 探活
6. 端口扫描
7. 爬虫
8. JS 下载与深度分析
9. 云 Bucket 枚举
10. 移动 App 下载与静态分析

产出：active_assets.jsonl

## 5.6 资产类型

domain, subdomain, ip, cidr, url, service, js, cert, repo, cloud, mobile

## 5.7 统一资产模型

最小核心字段 + extra JSON。

字段分组：

- 身份：asset_id, source, sources[], first_seen, last_seen
- 分类：type, subtype, tags[], monetization_tags[]
- 网络：host, domain, root_domain, ip, port, protocol, url
- 服务：status_code, title, server, tech[], waf, cms
- 内容：content_type, content_length, body_hash, headers
- JS：js_urls[], endpoints[], secrets[], source_maps[]
- 仓库：repo_url, branch, file_path, commit
- 云：bucket_name, cloud_provider, permission
- 移动端：app_id, package_name, version, exported_components[]
- 打分：priority, priority_reasons[], alive, confidence, edge
- 链：chain_roles[], monetization_paths[]

## 5.8 打分

priority = monetization_tag_score + alive_score + tech_score + edge_bonus

优先级：

- P0：核心牟利资产
- P1：相关业务资产
- P2：边缘资产
- P3：未知资产

边缘资产进入 edge_queue.jsonl，不丢弃。抽样比例默认 P2 30%，P3 10%。

## 5.9 工具映射

Kali / hexstrike：subfinder_scan, amass_scan, fierce_scan, dnsenum_scan, gobuster_scan, ffuf_scan, httpx_probe, nmap_scan, nmap_advanced_scan, rustscan_fast_scan, masscan_high_speed, gau_discovery, waybackurls_discovery, katana_crawl, hakrawler_crawl, paramspider_discovery, paramspider_mining, execute_command

Chrome DevTools：navigate_page, list_network_requests, get_network_request, evaluate_script, take_snapshot, take_screenshot, list_console_messages

Burp：proxy_http_history, proxy_http_history_regex, site_map, site_map_regex, response_body_search, proxy_history_annotate, cookie_jar_get

recon-hub：recon_phase, recon_provider_query, recon_expand, recon_urls, recon_js, recon_code, recon_cloud, recon_mobile, recon_normalize, recon_merge, recon_score, recon_throttle_get, recon_throttle_update, recon_export

## 5.10 人机协作

触发：IP 被封、主动测试被 WAF 拦截、需要验证码、需要人工确认。

处理：暂停主动任务 -> 输出当前 host/状态/截图 -> 请求用户切热点/介入 -> 恢复后重新跑 L1.5 探针 -> 更新 throttle_profile -> 继续执行。

## 5.11 产出

assets.jsonl, passive_assets.jsonl, active_assets.jsonl, throttle_profiles.json, priority_queue.jsonl, edge_queue.jsonl, js_findings.jsonl, source_stats.json

## 5.12 门禁

1. 至少一个资产存活
2. 资产已打牟利标签
3. 资产已排序
4. 边缘队列已建立
5. 主动测试前有 throttle_profile
6. 被动轮已完成或 provider 已降级

# 6. L2 存活指纹与暴露面

## 6.1 目的

不挖漏洞，只回答：这个资产活着吗？值不值得打？它的入口、技术栈、暴露面是什么？

## 6.2 原则

- 先 WAF 探测，再限速
- 有 WAF 降速，无 WAF 正常跑
- 每个 host 独立限速
- 遇到封禁不硬刚
- 边缘资产不丢弃
- 只做轻量已知漏洞匹配，不做完整利用

## 6.3 子层

L2.1 存活与指纹
L2.2 暴露面发现
L2.3 已知漏洞线索
L2.4 目标卡片

## 6.4 WAF 探测与限速

前置依赖：L1.5 已生成 throttle_profile。

策略：

- 有 WAF：conservative，并发 1-2，RPS 1-5，延迟 200-1000ms，被动优先，遇 403/429/503 立即回退
- 无 WAF：normal，并发 5-10，RPS 10-20，仍然监控 429/503
- 无法判断：按有 WAF 处理

throttle_profile 字段：

host, waf, mode, safe_concurrency, safe_rps, delay_ms, backoff_on, cooldown_seconds, ip_blocked

IP 被封：检测信号 -> IP_BLOCKED -> 暂停主动任务 -> 请求用户切热点 -> 重新 WAF 探测 -> 重新生成 throttle_profile -> 继续执行。

## 6.5 存活与指纹

HTTP 探活、标题、状态码、内容长度、技术栈、框架、CMS、中间件、WAF、CDN、云厂商、端口与服务、后台入口、API 文档、移动端 API。

产出：alive_assets.jsonl

## 6.6 暴露面发现

管理后台、Swagger/OpenAPI、GraphQL、Actuator、Jenkins/Grafana/Prometheus、云存储/云函数/K8s、CI/CD 入口、旧版接口/测试环境、默认口令入口、未授权入口。

产出：exposure.jsonl

## 6.7 已知漏洞线索

版本号 -> CVE 线索、已知组件漏洞、默认口令、未授权入口、子域接管、云存储配置错误。

产出：exposure_hints.jsonl

## 6.8 目标卡片

host, ip, tech, waf, throttle_profile, entry_points, exposures, tags, priority, edge, chain_hints

产出：target_cards.jsonl

## 6.9 工具映射

Kali / hexstrike：httpx_probe, wafw00f_scan, nmap_scan, nmap_advanced_scan, rustscan_fast_scan, nuclei_scan, wpscan_analyze, execute_command: whatweb

Chrome DevTools：navigate_page, list_network_requests, get_network_request, list_console_messages, take_snapshot, take_screenshot

Burp：proxy_http_history, site_map, response_body_search, proxy_history_annotate

recon-hub：recon_throttle_get, recon_throttle_update, recon_normalize, recon_score, recon_export

## 6.10 人机协作

触发：IP 被封、持续 429/403/503、出现验证码/滑块、风控拦截、主动任务全部失败。

处理：暂停主动任务 -> 输出 host/状态/截图 -> 请求用户切热点/介入 -> 恢复后重新探针 -> 更新 throttle_profile。

## 6.11 产出

throttle_profiles.json, alive_assets.jsonl, exposure.jsonl, exposure_hints.jsonl, target_cards.jsonl

## 6.12 门禁

1. 存活 + 有技术栈 + 至少一个入口或暴露面 -> 进入 L3
2. 边缘资产未知 -> 保留在边缘队列，抽样进入 L3
3. 触发封禁 -> 回退被动，等待 cooldown
4. 没有 throttle_profile 的 host，不允许进入主动测试

# 7. L3 业务 / API / 认证建模

## 7.1 目的

把 L2 发现的入口，变成可测试矩阵：endpoint x 参数 x 角色 x 认证状态 x 数据敏感度 x 牟利标签。L3 不挖漏洞，只建模。

## 7.2 原则

- 先建模，后测试
- 未登录态和登录态分开
- 多账号、多租户分开
- 边缘接口不丢弃
- 接口必须带牟利标签
- 需要登录时，人机协作

## 7.3 子层

L3.1 接口发现
L3.2 参数发现
L3.3 认证与角色建模
L3.4 API 专项建模
L3.5 Token 与会话
L3.6 数据敏感度与牟利标签
L3.7 测试矩阵

## 7.4 接口发现

来源：爬虫、浏览器 SPA 路由、XHR/Fetch、WebSocket、Burp 代理历史、JS 提取、历史 URL、移动端 API。

产出：endpoints.jsonl

## 7.5 参数发现

URL 参数、POST 参数、JSON 字段、Header 参数、Cookie 参数、隐藏参数、GraphQL 字段/变量/mutation。

产出：params.jsonl

## 7.6 认证与角色建模

角色：匿名、acc1（普通用户，租户 A）、acc2（普通用户，租户 B）、admin（不提供，需要时请求用户）。

认证状态：anonymous, user, admin, tenant_a, tenant_b。

产出：roles.json, auth_matrix.jsonl

## 7.7 API 专项建模

Swagger/OpenAPI、GraphQL introspection/schema、gRPC 反射、WebSocket 通道、Webhook 入口、移动端 API、旧版 API。

产出：api_inventory.jsonl

## 7.8 Token 与会话

Cookie、JWT、OAuth token、SAML 断言、Refresh token、CSRF token。

工具：jwt_analyzer, cookie_jar_get, proxy_http_history, params_extract

产出：tokens.jsonl, sessions.json

## 7.9 数据敏感度与牟利标签

payment, account, admin, api, upload, export, cloud, cicd, pii, money, internal

产出：test_matrix.jsonl

## 7.10 测试矩阵

字段：endpoint, method, params, auth_state, role, data_sensitivity, monetization_tags, priority, edge, chain_roles

## 7.11 工具映射

Kali / hexstrike：katana_crawl, hakrawler_crawl, gau_discovery, waybackurls_discovery, paramspider_discovery, paramspider_mining, arjun_parameter_discovery, x8_parameter_discovery, api_schema_analyzer, graphql_scanner, jwt_analyzer, http_repeater

Chrome DevTools：navigate_page, list_network_requests, get_network_request, evaluate_script, fill_form, click, list_console_messages, take_snapshot

Burp：proxy_http_history, site_map, params_extract, cookie_jar_get, find_reflected, comparer_send, diff_requests, repeater_tab

recon-hub：recon_normalize, recon_merge, recon_score, recon_export

## 7.12 人机协作

触发：注册、登录、滑块、短信验证码、邮箱验证码、风控、账号锁定、需要 admin 账号。

处理：暂停 -> 输出账号/URL/截图/所需操作 -> 等待用户介入 -> 恢复后保存会话 -> 继续建模。

## 7.13 产出

endpoints.jsonl, params.jsonl, roles.json, auth_matrix.jsonl, api_inventory.jsonl, tokens.jsonl, sessions.json, test_matrix.jsonl

## 7.14 门禁

1. 每个 endpoint 至少有参数、角色、认证状态
2. 有牟利标签的接口优先进入 L4
3. 边缘接口不丢弃，抽样进入 L4
4. 没有入口、没有参数、没有认证状态的资产，留在 L3 继续补
5. 需要登录态但没有有效会话 -> 暂停，请求用户介入

# 8. L4 高价值漏洞发现

## 8.1 目的

按 L3 的测试矩阵，发现高价值漏洞和链组件。分类：STANDALONE、CHAIN_ONLY、DISCARD。

## 8.2 原则

- 先未登录态，后登录态
- 先 STANDALONE，再 CHAIN_ONLY
- 不无脑扫，只打测试矩阵中的入口
- 主动测试前先读 throttle_profile
- 低危不单独提交，只作为链组件
- 遇到滑块、验证码、风控、IP 封禁 -> 暂停，请求用户介入

## 8.3 总流程

L4-U 未登录态 -> 注册 acc1 -> 登录 -> 注册 acc2 -> 登录 -> L4-A1 单账号测试 -> L4-A2 双账号越权/多租户 -> L4-A3 低权向高权提权 -> L4-A4 差分测试 -> 分类。

## 8.4 L4-U 未登录态

顺序：未授权访问、认证绕过、注入类、SSRF/云、文件类、认证流程、客户端链组件、已知暴露。

重点：未授权 API、预认证 IDOR、SQLi/NoSQLi、命令注入/RCE、SSTI/XXE、SSRF 打云元数据、文件上传/路径穿越/LFI、开放重定向/CRLF/Host 头、密码重置/注册逻辑、默认口令/Actuator/Jenkins/Grafana。

产出：findings_unauth.jsonl

## 8.5 注册 / 登录桥接

自动注册 acc1 -> 遇到滑块/验证码/风控 -> 暂停请求用户介入 -> 完成注册 -> 自动登录 acc1 -> 保存 Cookie/JWT/Refresh Token/CSRF -> 自动注册 acc2 -> 自动登录 acc2 -> 保存会话。

产出：accounts.json, sessions.json

## 8.6 L4-A 登录态

L4-A1 单账号测试：存储 XSS、CSRF、文件上传、API 越权、业务逻辑、支付/改价/退款、优惠券/积分/礼品卡、竞态条件、订阅/试用绕过。

L4-A2 双账号越权/多租户：IDOR/BOLA、水平越权、多租户绕过、邀请/拉新、重复领取、账号绑定/解绑、密码重置、订单/消息越权。

L4-A3 低权向高权提权：BFLA、批量赋值、JWT 篡改、IDOR 打管理员资源、隐藏后台接口、密码重置/邮箱修改、链式提权。

L4-A4 差分测试：acc1 请求 -> acc2 重放 -> 对比；租户 A 请求 -> 租户 B 重放 -> 对比；匿名请求 -> 用户请求 -> 对比；普通用户 -> 管理员接口 -> 对比。

产出：findings_auth.jsonl, authz_matrix.jsonl

## 8.7 分类门禁

字段：type, endpoint, param, role, standalone_impact, chain_roles, monetization_paths, submission, evidence, throttle_profile

## 8.8 工具映射

Kali / hexstrike：sqlmap_scan, nuclei_scan, dalfox_xss_scan, xsser_scan, dotdotpwn_scan, metasploit_run, generate_exploit_from_cve, jwt_analyzer, graphql_scanner, api_schema_analyzer, http_intruder, http_repeater, execute_command

Burp：repeater_tab, intruder, comparer_send, diff_requests, collaborator_generate, collaborator_poll, scan_audit_start, issue_create

Chrome DevTools：evaluate_script, fill_form, click, list_network_requests, get_network_request, list_console_messages, take_screenshot

recon-hub：recon_score, recon_export

## 8.9 人机协作

触发：注册、登录、滑块、短信验证码、邮箱验证码、风控、账号锁定、IP 被封、需要 admin 账号。

处理：暂停 -> 输出账号/URL/截图/所需操作 -> 等待用户介入 -> 恢复后继续。

## 8.10 产出

findings_unauth.jsonl, findings_auth.jsonl, accounts.json, sessions.json, authz_matrix.jsonl, chain_candidates.jsonl, discard.jsonl, pocs/, evidence/

## 8.11 门禁

1. STANDALONE + 证据完整 -> 进入 L5
2. CHAIN_ONLY + 可串联 -> 进入 L5 链图
3. DISCARD -> 停止
4. 主动测试必须先有 throttle_profile
5. 遇到 429/403/503/验证码 -> 停止该 host 主动测试
6. 低危漏洞不单独提交

# 9. L5 验证与漏洞链

## 9.1 目的

把 L4 的发现变成：可复现 PoC、完整攻击链、可提交报告。

## 9.2 原则

- 证据优先
- 最小化 PoC
- 不扩大数据访问
- 不破坏
- 链优先
- 低危不单独提交
- 需要 admin / 验证码 / IP 切换 -> 人机协作

## 9.3 子层

L5.1 可复现性验证
L5.2 最小化 PoC
L5.3 影响验证
L5.4 漏洞链构建
L5.5 提交分类

## 9.4 可复现性验证

重放请求、换会话/换账号/换租户再验证、排除缓存/时间/环境偶然因素、确认稳定复现、失败则标记 NEED_RETEST。

## 9.5 最小化 PoC

只保留必要请求、去掉无关参数/Header、写清复现步骤、不拖库、不批量下载、不删除/不篡改/不破坏、只证明影响不扩大影响。

## 9.6 影响验证

能读什么数据？能改什么数据？能拿什么权限？能造成什么资金/资产损失？能作为什么链的入口？

## 9.7 漏洞链构建

链图模型：节点 finding/asset，边 chain_role，终点 monetization_path。

chain_role：initial_access, info_leak, auth_bypass, privilege, pivot, persistence, client_exec, money, cloud

常见链：

- 开放重定向 -> OAuth token 窃取 -> 账号接管
- 子域接管 -> Cookie/OAuth 重定向 -> 账号接管
- CORS -> 敏感数据窃取 -> 数据倒卖
- 盲 SSRF -> 内网扫描 -> Redis/FastCGI -> RCE
- 目录列表/Source Map -> API Key -> 云接管
- 用户枚举 + 速率限制 -> 撞库 -> 账号接管
- 反射 XSS + CSRF -> 账号接管
- CRLF + 缓存投毒 -> 存储 XSS -> 账号接管
- Host 头 + 密码重置 -> 账号接管
- SSRF + 云元数据 -> 云接管
- SQLi + 文件写 -> RCE
- LFI + 日志污染 -> RCE
- 文件上传 + 路径穿越 -> RCE
- 原型链污染 -> XSS/RCE
- 请求走私 -> 认证绕过/缓存投毒

## 9.8 提交分类

STANDALONE：独立可牟利/独立高影响，可单独提交。
CHAIN_COMPLETE：链已打通到牟利终点，整条链提交。
CHAIN_INCOMPLETE：链未打通，只存内部记录，不提交。
DISCARD：无影响、不可复现、连链都进不去，停止。
NEED_RETEST：信号不明确，回 L4 重测。

## 9.9 工具映射

Burp：repeater_tab, comparer_send, diff_requests, collaborator_generate, collaborator_poll, issue_create
Kali / hexstrike：http_repeater, http_intruder, execute_command
Chrome DevTools：evaluate_script, list_network_requests, get_network_request, take_screenshot
recon-hub：recon_score, recon_export

## 9.10 人机协作

触发：需要 admin 账号、需要短信/邮箱验证码、遇到滑块/验证码、IP 被封、需要人工确认。
处理：暂停 -> 输出当前状态/URL/截图/所需操作 -> 等待用户介入 -> 恢复后继续。

## 9.11 产出

validated_findings.jsonl, chains.jsonl, report_ready.jsonl, pocs/, evidence/

## 9.12 门禁

1. 可复现 + 高影响 -> 进入 L6
2. 链完整 -> 整条链进入 L6
3. 链不完整 -> 保留，不提交
4. 无证据 -> 不升级
5. 低危单独 -> 不提交
6. 需要 admin / 验证码 / IP 切换 -> 暂停，请求用户介入

# 10. L6 报告与提交

## 10.1 目的

只把高价值、可复现、证据完整的漏洞或完整链，变成可提交报告。

## 10.2 原则

高价值才提交、低危不单独提交、完整链作为一个报告提交、证据不完整不提交、重复问题不提交、提交前必须人工复核。

## 10.3 子层

L6.1 去重与确认
L6.2 严重性判定
L6.3 报告生成
L6.4 证据打包
L6.5 提交策略
L6.6 人工复核

## 10.4 去重与确认

检查：同一根因、同一 endpoint + 参数、同一修复方案、Burp Scanner 已有 issue、历史报告、公开已知问题。
标记：DUPLICATE, PARTIAL_DUPLICATE, NEW。

## 10.5 严重性判定

S：RCE、云接管、核心支付、全量数据
A：认证绕过、管理员越权、批量 PII、SSRF 元数据
B：单用户 IDOR、存储 XSS 影响会话、有限 SSRF
C：反射 XSS、CSRF 有限、开放重定向、低敏信息泄露
D：无实际影响、自 XSS、点击劫持、最佳实践

## 10.6 报告结构

报告模板：TBD，后续补充。

占位字段：标题、漏洞类型、影响资产、角色/认证状态、严重性、摘要、牟利影响、复现步骤、证据、根因、修复建议、引用、链信息。

## 10.7 证据打包

原始请求/响应、复现步骤、截图、带外交互、差分对比、账号/角色/租户、时间戳、最小 PoC、敏感数据脱敏。

## 10.8 提交策略

STANDALONE + S/A -> 提交
CHAIN_COMPLETE -> 整条链提交
CHAIN_INCOMPLETE -> 不提交
C/D 单独 -> 不提交

## 10.9 人工复核

提交前必须经用户确认：是否在授权范围、是否重复、是否会造成破坏、是否需要补充证据、是否需要调整严重性。

## 10.10 工具映射

Burp：issue_create, scanner_issues, collaborator_poll
Kali / hexstrike：create_vulnerability_report, scan_report
Chrome DevTools：take_screenshot, list_network_requests, get_network_request
recon-hub：recon_export

## 10.11 产出

reports/, report.md, burp_issue.json, evidence/, submission_checklist.md

## 10.12 门禁

1. 高价值
2. 可复现
3. 证据完整
4. 无重复
5. 修复建议明确
6. 人工复核通过

满足全部条件，才允许提交。

# 11. 数据模型

核心字段 + extra JSON。

Asset: id, type, host, ip, port, url, source, tags, priority, alive, first_seen, last_seen, extra
Finding: id, type, endpoint, param, role, auth_state, standalone_impact, chain_roles, monetization_paths, submission, evidence_refs, reproducible, extra
Chain: id, nodes, edges, target_monetization, status, evidence_refs, extra
Session: id, account_id, role, tenant, cookies, jwt, tokens, csrf, valid, expires_at, extra
ThrottleProfile: host, waf, mode, safe_concurrency, safe_rps, delay_ms, backoff_on, cooldown_seconds, ip_blocked, extra
Task: id, source, type, status, progress, payload, external_ref, result, error, host, provider, timestamps, extra

# 12. 状态与产出文件

```text
outputs/
  assets.jsonl
  passive_assets.jsonl
  active_assets.jsonl
  throttle_profiles.json
  priority_queue.jsonl
  edge_queue.jsonl
  exposure.jsonl
  exposure_hints.jsonl
  target_cards.jsonl
  endpoints.jsonl
  params.jsonl
  roles.json
  auth_matrix.jsonl
  api_inventory.jsonl
  tokens.jsonl
  sessions.json
  test_matrix.jsonl
  findings_unauth.jsonl
  findings_auth.jsonl
  authz_matrix.jsonl
  chain_candidates.jsonl
  validated_findings.jsonl
  chains.jsonl
  report_ready.jsonl
  reports/
  evidence/
  pocs/
```

# 13. 人机协作协议

触发：滑块、图形验证码、短信验证码、邮箱验证码、风控、账号锁定、IP 被封、需要 admin 账号、需要人工确认。

处理：暂停 -> 输出请求格式 -> 等待用户介入 -> 恢复执行。

# 14. 异常处理与降级

provider 超时 -> 降级下一个 provider
provider 限额 -> 切换免 key provider
主动被封 -> 回退被动
登录失败 3 次 -> 停止
验证码 -> 请求人工
长任务 -> 后台运行 + 轮询
MCP 超时 -> 重试或降级

# 15. 待定项

报告模板、recon-hub provider 清单与 API key、链图存储字段细节、dsh 长任务与状态持久化细节、危险工具 guardrails、去重算法实现、严重性评分公式实现。

# 16. MCP 工具调用约定

## 16.1 recon-hub phase

```text
recon_phase("passive", targets)
recon_phase("probe", targets)
recon_phase("active", targets)
recon_phase("exposure", targets)
```

## 16.2 hexstrike 映射

```text
recon_hexstrike_plan(task_type, target)
recon_hexstrike_plan_all(target)
```

映射示例：

```text
subdomain_bruteforce -> subfinder_scan
dns_resolve          -> dnsenum_scan
http_probe           -> execute_command + httpx
waf_detect           -> wafw00f_scan
tech_detect          -> nuclei_scan
port_scan            -> nmap_scan
crawl                -> katana_crawl
```

## 16.3 active / exposure 执行循环

```text
recon_phase("active" | "exposure", targets)
  ↓
拿到 task_id
  ↓
recon_hexstrike_plan(task_type, target)
  ↓
调用 hexstrike MCP 或 execute_command
  ↓
解析输出
  ↓
recon_ingest_domains / recon_ingest_assets
  ↓
recon_task_update(task_id, status="success", result={...})
```

## 16.4 资产查询

```text
recon_list_assets
recon_get_asset
```

## 16.5 任务状态

```text
recon_task_start
recon_task_register
recon_task_update
recon_task_status
recon_task_list
recon_task_cancel
recon_task_result
```
# 17. 发现 / 链 / 资产持久化

## 17.1 资产

```text
recon_ingest_domains
recon_ingest_assets
recon_list_assets
recon_get_asset
```

## 17.2 Finding

```text
recon_ingest_findings
recon_list_findings
```

## 17.3 Chain

```text
recon_ingest_chains
recon_list_chains
```

## 17.4 hexstrike 输出解析

```text
recon_hexstrike_parse(task_type, output)
recon_hexstrike_ingest(task_type, target, output)
```

支持的 task_type：

```text
subdomain_bruteforce
http_probe
crawl
tech_detect
waf_detect
port_scan
```

## 17.5 标准闭环

```text
recon_phase("active" | "exposure", targets)
  ↓
recon_hexstrike_plan(task_type, target)
  ↓
调用 hexstrike MCP / execute_command
  ↓
recon_hexstrike_ingest(task_type, target, output)
  ↓
recon_task_update(task_id, status="success", result={...})
```
# 18. recon-hub 完整工具列表

## 18.1 阶段编排

```text
recon_phase("passive", targets)
recon_phase("probe", targets)
recon_phase("active", targets)
recon_phase("exposure", targets)
recon_phase("js", targets, {"urls": [...]})
recon_phase("code", targets)
recon_phase("cloud", targets)
recon_phase("vuln", targets)
```

## 18.2 Provider

```text
recon_provider_query
recon_expand
recon_urls
recon_js
recon_code
recon_cloud
```

## 18.3 hexstrike 映射

```text
recon_hexstrike_plan
recon_hexstrike_plan_all
recon_hexstrike_parse
recon_hexstrike_ingest
```

## 18.4 持久化

```text
recon_ingest_domains
recon_ingest_assets
recon_list_assets
recon_get_asset

recon_ingest_endpoints
recon_list_endpoints

recon_ingest_findings
recon_list_findings

recon_ingest_chains
recon_list_chains
recon_chain_suggest
```

## 18.5 任务

```text
recon_task_start
recon_task_register
recon_task_update
recon_task_status
recon_task_cancel
recon_task_result
```

## 18.6 限速与导出

```text
recon_throttle_get
recon_throttle_update
recon_export
recon_export_db
recon_stats
```

## 18.7 标准闭环

```text
recon_phase("passive")
  ↓
recon_phase("probe")
  ↓
recon_phase("active")
  ↓
recon_phase("exposure")
  ↓
recon_phase("js")
  ↓
recon_ingest_endpoints
  ↓
recon_phase("vuln")
  ↓
recon_hexstrike_plan
  ↓
hexstrike MCP / execute_command
  ↓
recon_hexstrike_ingest
  ↓
recon_ingest_findings
  ↓
recon_chain_suggest
  ↓
recon_ingest_chains
  ↓
recon_export_db
```
# 19. L5 / L6 编排

## 19.1 链编排

```text
recon_phase("chain")
```

它会：

1. 读取 findings
2. 调用 `suggest_chains`
3. 写入 chains 表
4. 返回候选链

## 19.2 报告

```text
recon_report
```

它会：

1. 读取 findings / chains
2. 生成 Markdown
3. 写入 data/reports/
4. 返回路径
# 20. 专项能力

## 20.1 微信小程序抓包

- 脚本：`tools/wechat_capture.py`
- 插件：`tools/mini_log.py`
- 解析：`scripts/parse_mini_log.py`
- Playbook：`skill/playbooks/wechat.md`

流程：

```text
start -> 微信操作 -> stop -> parse -> recon_ingest_endpoints / recon_ingest_assets
```

## 20.2 经验库

- 索引：`experience/INDEX.md`
- 规则：`experience/README.md`
- 脚本：`scripts/experience.py`
- Playbook：`skill/playbooks/experience.md`

规则：

- 平时不加载
- 命中关键词才读取
- 报告提交后才写入
- 只写验证过的经验

## 20.3 Clash / 网络切换

- 脚本：`scripts/clash.py`
- Playbook：`skill/playbooks/network.md`
- 配置：`config.yaml` 的 `network` 段

用途：

- IP 被封时切节点
- provider 429 时换出口
- 区域访问失败时换节点
# 21. 微信小程序资产

## 21.1 定位

微信小程序属于资产的一部分。

- 类型：`wechat_miniprogram`
- 来源：页面、JS、URL、二维码、用户提供
- 标签：`wechat`、`human_assisted`
- 激活顺序：默认最后

## 21.2 检测

```text
recon_wechat_detect(urls)
recon_phase("wechat", urls)
```

检测内容：

- `wx[0-9a-fA-F]{16}` appid
- `miniprogram`
- `weapp`
- `wx-open-launch-weapp`
- `mp.weixin.qq.com`

## 21.3 抓包

当发现小程序资产后，默认最后开启：

```text
python tools/wechat_capture.py start
  ↓
人工打开小程序并操作
  ↓
python tools/wechat_capture.py stop
  ↓
python scripts/parse_mini_log.py --out wechat_output.json
  ↓
recon_ingest_endpoints / recon_ingest_assets
```

原因：

- 需要人机协作
- 需要用户点击微信
- 不应阻塞前面的自动化流程