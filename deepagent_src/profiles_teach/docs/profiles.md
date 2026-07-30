# Deep Agents Profiles 学习路线

## 学习主题

这部分学习 Deep Agents 的 profiles：把某个 provider 或某个 model 的默认行为打包起来，让 `create_deep_agent` 在选中模型时自动应用。艹，别把两种 profile 混成一锅：`HarnessProfile` 管 harness 行为，`ProviderProfile` 管模型构造参数。

## 为什么不改 `create_deep_agent` 也能生效

`register_harness_profile()` 和 `register_provider_profile()` 不是装饰器，也不是给 `create_deep_agent` 包一层函数；它们是把配置写入 Deep Agents 内部的全局 profile registry。

当你调用 `create_deep_agent(model=...)` 时，Deep Agents 内部会解析当前模型的 provider 和 identifier，例如本项目的真实模型会解析成：

```text
provider = openai
identifier = gpt-5.5
```

然后 HarnessProfile 会按顺序查：

```text
openai:gpt-5.5
openai
默认空 profile
```

所以提前注册过：

```python
register_harness_profile("openai:gpt-5.5", HarnessProfile(...))
```

后面哪怕 `create_deep_agent(model=get_real_model())` 调用点没多加参数，profile 也会在 Agent 组装时被命中。

ProviderProfile 的链路更早：只有当你传入字符串模型 spec，例如 `create_deep_agent(model="openai:gpt-5.5")` 时，Deep Agents 会先 `resolve_model(...)`，再通过 `apply_provider_profile(...)` 把已注册的模型构造参数传给 `init_chat_model(...)`。

```text
HarnessProfile   -> 影响 Agent harness 行为：prompt、工具描述、隐藏工具、middleware、general-purpose subagent
ProviderProfile  -> 影响模型构造参数：temperature、timeout、base_url、headers、pre_init
```

## 课程大纲

### 01 HarnessProfile：追加模型专属提示

目标：理解 `system_prompt_suffix` 如何在匹配模型时追加到系统提示词末尾。

### 02 工具可见性与描述覆盖

目标：理解 `tool_description_overrides` 和 `excluded_tools` 如何改变模型看到的工具说明和工具集合。

### 03 ProviderProfile：模型构造参数

目标：理解 provider-level 与 model-level 的 `init_kwargs` 如何合并，以及它只影响模型构造，不影响 harness。

### 04 HarnessProfileConfig：配置文件加载

目标：理解 JSON/YAML 友好的 profile 配置如何 round-trip，并直接注册到 harness profile。

### 05 综合案例：Provider + Harness 一起用

目标：把 provider 参数合并、工具描述覆盖、工具隐藏、禁用 general-purpose subagent 串成一条真实流程。

## 推荐学习顺序

1. 先学 HarnessProfile，因为它直接影响 Agent 的提示词、工具和 subagent。
2. 再学 ProviderProfile，因为它只在模型构造阶段生效。
3. 最后学 Config 和综合案例，知道哪些配置适合落盘，哪些只能写在 Python 里。

## 本地版本

- `deepagents==0.6.12`
- 示例通过 `_model.py` 复用项目已有 `deepagent_src.llms.get_gpt_model()`，会执行真实 Agent 调用。
- 示例通过 `deepagent_src.agent_output.invoke_and_pretty_print()` 打印完整消息链。
- 官方资料来源：`https://docs.langchain.com/oss/python/deepagents/profiles`

## 当前章节

- [01 HarnessProfile：追加模型专属提示](01_harness_prompt_suffix.md)
- [02 工具可见性与描述覆盖](02_tool_visibility.md)
- [03 ProviderProfile：模型构造参数](03_provider_profile.md)
- [04 HarnessProfileConfig：配置文件加载](04_config_profile.md)
- [05 综合案例：Provider + Harness 一起用](05_comprehensive_case.md)
