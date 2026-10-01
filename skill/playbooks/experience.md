# 经验库

## 触发

- 卡壳
- 遇到熟悉的问题
- 报告收尾
- 命中 INDEX.md 关键词

## 使用

```powershell
python scripts/experience.py search "<关键词>"
```

## 写入

报告提交后：

```powershell
python scripts/experience.py add "<关键词>"
```

然后填写：

```text
# 现象
# 原因
# 解法
# 验证
confidence: high | medium | low
last_verified: YYYY-MM-DD
```

## 规则

- 平时不加载
- 每次最多读 1-2 条
- 只写验证过的经验
- 不写猜测