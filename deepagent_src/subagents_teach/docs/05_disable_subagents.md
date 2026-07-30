# 05 关闭同步 subagents

## 它是什么

要让 Agent 没有同步 `task` 工具，支持路径是禁用默认 `general-purpose` subagent，并且不传任何同步 `subagents`。这个开关放在 active harness profile 的 `GeneralPurposeSubagentProfile(enabled=False)` 里。它解决的问题是：某些简单 Agent 不允许委派，避免模型把直接任务绕成子任务。

## 常用程度

中。大多数 Deep Agent 会保留 subagent；但当你做一个简单、受控、不能委派的 Agent 时，这个开关很有用。

适合：

- 工具面很敏感，不希望模型把任务转交给默认 subagent。
- Agent 只做单步问答或固定工具调用。
- 你想明确验证“没有 task 工具时模型怎么工作”。

不适合：

- 复杂研究、代码审查、批处理任务。
- 需要上下文隔离的工作流。

## 生效条件

必须同时满足：

```text
general_purpose_subagent.enabled = False
create_deep_agent(..., subagents=None 或不传同步 subagents)
```

如果你禁用了默认 general-purpose，但又传了自定义同步 subagent，`task` 工具仍然会存在。

## 最小代码

文件：`deepagent_src/subagents_teach/05_disable_subagents.py`

```python
register_harness_profile(
    "openai:gpt-5.5",
    HarnessProfile(
        general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
    ),
)
```

## 运行

```bash
uv run python deepagent_src/subagents_teach/05_disable_subagents.py
```

预期输出末尾：

```text
disable synchronous subagents real agent ok
```

## 验证方式

脚本真实调用 Agent，并断言消息链里没有名为 `task` 的工具消息。

## 常见误区

不要用 `excluded_middleware` 去删 `SubAgentMiddleware`。官方支持路径是禁用默认 general-purpose subagent，并且不提供同步 subagents。

async subagents 不受这个规则影响。同步 `task` 工具和 async task 工具是两套 middleware。
