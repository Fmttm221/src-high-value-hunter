# Provider 注册清单

所有 key 填到 `config.yaml` 对应 provider 下，然后设置 `enabled: true`。

## 免 key

### crt.sh
- 地址：https://crt.sh
- 无需注册
- config：

```yaml
crtsh:
  enabled: true
```

### Wayback
- 地址：https://web.archive.org
- 无需注册
- config：

```yaml
wayback:
  enabled: true
```

## 推荐注册

### URLScan
- 注册：https://urlscan.io/user/signup/
- API key：https://urlscan.io/user/profile/
- config：

```yaml
urlscan:
  enabled: true
  api_key: "你的 key"
```

### AlienVault OTX
- 注册：https://otx.alienvault.com/
- API key：登录后 Settings -> API Key
- config：

```yaml
otx:
  enabled: true
  api_key: "你的 key"
```

### GitHub
- 注册：https://github.com/
- Token：https://github.com/settings/tokens
- 只需要 public repo 读权限
- config：

```yaml
github:
  enabled: true
  api_key: "你的 token"
```

### Shodan
- 注册：https://account.shodan.io/register
- API key：https://account.shodan.io/
- config：

```yaml
shodan:
  enabled: true
  api_key: "你的 key"
```

### Censys
- 注册：https://search.censys.io/register
- API：https://search.censys.io/account/api
- 需要 API ID + Secret
- config：

```yaml
censys:
  enabled: true
  api_id: "你的 id"
  api_secret: "你的 secret"
```

### 360 Quake
- 注册：https://quake.360.net/quake/#/register
- Token：登录后个人中心
- config：

```yaml
quake:
  enabled: true
  api_key: "你的 token"
```

### ZoomEye
- 注册：https://www.zoomeye.org/register
- API key：登录后个人中心
- config：

```yaml
zoomeye:
  enabled: true
  api_key: "你的 key"
```

### Hunter.how
- 注册：https://hunter.qianxin.com/
- API key：登录后个人中心
- config：

```yaml
hunter:
  enabled: true
  api_key: "你的 key"
```

### Netlas
- 注册：https://app.netlas.io/registration/
- API key：登录后 Profile
- config：

```yaml
netlas:
  enabled: true
  api_key: "你的 key"
```

### VirusTotal
- 注册：https://www.virustotal.com/gui/join-us
- API key：https://www.virustotal.com/gui/my-apikey
- config：

```yaml
virustotal:
  enabled: true
  api_key: "你的 key"
```

### SecurityTrails
- 注册：https://securitytrails.com/
- API key：登录后 Dashboard -> API
- config：

```yaml
securitytrails:
  enabled: true
  api_key: "你的 key"
```

### GreyNoise
- 注册：https://viz.greynoise.io/signup
- API key：登录后 Account
- config：

```yaml
greynoise:
  enabled: true
  api_key: "你的 key"
```

### AbuseIPDB
- 注册：https://www.abuseipdb.com/register
- API key：https://www.abuseipdb.com/account/api
- config：

```yaml
abuseipdb:
  enabled: true
  api_key: "你的 key"
```

### IPinfo
- 注册：https://ipinfo.io/signup
- Token：https://ipinfo.io/account/token
- config：

```yaml
ipinfo:
  enabled: true
  api_key: "你的 token"
```

## 填完后

1. 重启 dsh web
2. 调用 `recon_phase("passive")` 或 `recon_provider_query`
3. 检查返回的 provider summary