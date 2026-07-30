# 02 工具可见性与描述覆盖

## 它是什么

Harness profile 可以用 `tool_description_overrides` 改工具描述，用 `excluded_tools` 把工具从模型可见工具集中移除。它解决的问题是：同一套 Agent 在不同模型下可能需要不同的工具说明，或者某些模型不该看到某些工具。工具隐藏是按工具名匹配。

## 最小代码

文件：`deepagent_src/profiles_teach/02_tool_visibility.py`

```python
register_harness_profile(
    "openai:gpt-5.5",
    HarnessProfile(
        tool_description_overrides={
            "visible_profile_tool": "Use this tool when the user asks for the visible profile marker."
        },
        excluded_tools=frozenset({"hidden_profile_tool"}),
    ),
)
```

## 运行

```bash
uv run python deepagent_src/profiles_teach/02_tool_visibility.py
```

预期输出末尾：

```text
tool visibility profile real agent ok
```

## 验证方式

脚本真实调用 Agent，要求它调用 `visible_profile_tool`；断言工具消息中出现可见工具结果，并且没有出现隐藏工具结果。

## 常见误区

`excluded_tools` 不是删除工具函数，也不是改 Python 代码；它是在模型请求前过滤工具，让模型看不见这个工具。

