# 网络与代理

## Clash

本机 Clash 默认：

```text
HTTP proxy: 127.0.0.1:7890
Controller: 127.0.0.1:9090
```

查看节点：

```powershell
python scripts/clash.py status
python scripts/clash.py list GLOBAL
```

切换节点：

```powershell
python scripts/clash.py switch GLOBAL "<节点名>"
```

## recon-hub 走代理

如果 Kali 能访问 Windows 的 Clash，可在 `config.yaml` 设置：

```yaml
network:
  proxy: "http://192.168.86.1:7890"
```

recon-hub 启动时会自动设置：

```text
HTTP_PROXY
HTTPS_PROXY
```

## 触发条件

- IP 被 WAF 封禁
- provider 429
- 区域访问失败
- 需要切换出口 IP

## 处理

1. 暂停主动任务
2. 切换 Clash 节点
3. 重新跑 probe
4. 更新 throttle_profile
5. 继续