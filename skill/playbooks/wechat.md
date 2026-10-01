# 微信小程序抓包分析

## 触发条件

- 目标存在微信小程序
- 小程序有 API / 登录 / 支付 / 上传 / 导出等功能
- Burp 抓包困难

## 工具

```text
tools/wechat_capture.py
tools/mini_log.py
scripts/parse_mini_log.py
```

## 流程

1. 启动抓包：

```powershell
python tools/wechat_capture.py start
```

2. 打开 mitmweb：

```text
http://127.0.0.1:8081
```

3. 在微信中打开目标小程序，触发功能。

4. 查看请求日志：

```text
%TEMP%/mini_req.log
```

5. 停止抓包：

```powershell
python tools/wechat_capture.py stop
```

6. 解析日志：

```powershell
python scripts/parse_mini_log.py --out wechat_output.json
```

7. 写入 recon-hub：

```text
recon_ingest_endpoints(endpoints)
recon_ingest_assets(assets)
```

## 重点

- API 域名
- 登录 / Token / JWT
- 支付 / 订单 / 退款
- 上传 / 下载 / 导出
- 越权接口
- 参数和签名

## 注意

- 必须在运行微信的 Windows 主机上执行
- 安装 mitmproxy CA 到 CurrentUser Root
- 识别图片 / 验证码前可临时关闭系统代理