# Contributing

## 开发

1. 创建虚拟环境
2. 安装依赖
3. 运行 `make compile`
4. 运行 `make smoke`

## Provider

新增 provider：

1. 在 `src/recon_hub/providers/` 添加适配器
2. 实现 `query` 和 `normalize`
3. 在 `providers/__init__.py` 注册
4. 在 `config.yaml` 添加配置
5. 添加 smoke test

## MCP 工具

新增工具：

1. 在 `src/recon_hub/tools/` 添加模块
2. 实现 `register_*_tools`
3. 在 `server.py` 注册
4. 更新 README / SKILL.md