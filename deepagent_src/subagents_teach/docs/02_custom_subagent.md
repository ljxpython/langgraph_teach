# 02 自定义字典 subagent

## 它是什么

自定义 subagent 最常用的形式是一个字典，至少包含 `name`、`description` 和 `system_prompt`。`description` 帮主 Agent 判断何时委派，`system_prompt` 是子 Agent 自己的规则。`tools` 指定后会让子 Agent 聚焦在这些工具上。

## 常用程度

最高。真实项目里最常见的 subagent 用法就是字典式配置。

适合：

- “研究员”“代码审查员”“测试执行员”“报告撰写员”这类固定职责。
- 需要不同工具集合的任务。
- 需要子 Agent 按固定格式返回结果。

不适合：

- 一次性临时任务，直接用 general-purpose 就够。
- 已经有复杂 LangGraph 工作流，这种可以考虑 `CompiledSubAgent`。

## 字段解释

```python
specialist_subagent = {
    "name": "specialist",
    "description": "...",
    "system_prompt": "...",
    "tools": [specialist_marker],
}
```

- `name`：主 Agent 调 `task` 时用的 `subagent_type`，必须唯一。
- `description`：主 Agent 选择 subagent 的依据，越具体越稳定。
- `system_prompt`：子 Agent 的角色、工具使用规则和输出格式。
- `tools`：子 Agent 可用工具。指定后就别乱塞无关工具，工具多了模型更容易跑偏。

## 设计原则

description 写“什么时候用”，system_prompt 写“怎么做”。艹，别把两者都写成一句“你是助手”，那主 Agent 选不准，子 Agent 也干不明白。

## 最小代码

文件：`deepagent_src/subagents_teach/02_custom_subagent.py`

```python
specialist_subagent = {
    "name": "specialist",
    "description": "Use this subagent when the task asks for the specialist marker.",
    "system_prompt": "Always call specialist_marker and return only the tool result.",
    "tools": [specialist_marker],
}
```

## 运行

```bash
uv run python deepagent_src/subagents_teach/02_custom_subagent.py
```

预期输出末尾：

```text
custom subagent real agent ok
```

## 验证方式

脚本真实调用主 Agent，让它委派 `specialist`；断言 `task` 工具结果中包含子 Agent 工具返回的 `custom-specialist-subagent-called`。

输出里如果看到：

```text
Tool Calls:
  task
    subagent_type: specialist
Tool Message:
  custom-specialist-subagent-called
```

说明主 Agent 按 `description` 选中了自定义 subagent，子 Agent 又按 `system_prompt` 调用了自己的工具。

## 常见误区

别把所有工具都塞给每个 subagent。工具越少，子 Agent 越专注，权限边界也越清楚。

还有一个坑：自定义 subagent 的 `system_prompt` 不继承主 Agent 的 `system_prompt`。需要的规则要在子 Agent 里重新写清楚。
