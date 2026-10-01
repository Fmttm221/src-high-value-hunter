# dsh MCP 配置

## recon-hub

把 `recon-hub.yml` 里的条目加入你的 dsh MCP 配置列表。

也可以用 `mcp.config.example.json` 作为通用 MCP 配置参考。

启动前确认：

```powershell
D:\dsh work\src-high-value-hunter\.venv\Scripts\python.exe -m recon_hub.server --help
```

如果这个命令能输出 help，说明 recon-hub 可以被 dsh 拉起。