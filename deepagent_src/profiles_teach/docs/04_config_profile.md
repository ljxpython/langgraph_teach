# 04 HarnessProfileConfig：配置文件加载

## 它是什么

`HarnessProfileConfig` 是可序列化的 profile 配置，适合从 JSON/YAML 加载。它覆盖的是 `HarnessProfile` 的声明式子集，比如提示词、工具描述、隐藏工具、禁用 general-purpose subagent。运行时对象、middleware 实例和工厂函数不适合放这里。

## 最小代码

文件：`deepagent_src/profiles_teach/04_config_profile.py`

```python
config = HarnessProfileConfig.from_dict(json.loads(CONFIG_PATH.read_text()))
register_harness_profile("openai:gpt-5.5", config)
```

## 运行

```bash
uv run python deepagent_src/profiles_teach/04_config_profile.py
```

预期输出末尾：

```text
config profile real agent ok
```

## 验证方式

脚本写入一个最小 JSON profile，读取成 `HarnessProfileConfig` 后注册，并真实调用 Agent；断言 config 能导出 `excluded_tools`，也断言模型按配置 suffix 返回指定标记。

## 常见误区

配置文件只适合声明式字段。`extra_middleware` 这种运行时对象别硬塞 JSON/YAML，放 Python 代码里更清楚。

