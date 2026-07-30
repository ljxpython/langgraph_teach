# 01 默认 general-purpose subagent

## 它是什么

Deep Agents 默认会添加一个同步 `general-purpose` subagent，除非你自己提供同名 subagent 或通过 profile 禁用它。主 Agent 通过 `task` 工具委派，等待子 Agent 完成后只接收最终结果。它解决的问题是：把复杂中间步骤隔离在子 Agent 上下文里，主 Agent 保持干净。

## 常用程度

高。你不配置自定义 subagent 时，它就是默认可用的“通用隔离区”。

适合：

- 临时多步骤任务，例如读几个文件、整理一段材料、做一次小研究。
- 你不想污染主 Agent 上下文，但也不需要专门 prompt 或专门工具。
- 任务不值得单独创建一个专家 subagent。

不适合：

- 明确需要专门工具、专门输出格式或权限控制。
- 简单一步任务，比如“把这句话翻译成英文”。

## 执行链路

```text
用户请求
-> 主 Agent 判断需要委派
-> 主 Agent 调 task(subagent_type="general-purpose", description="...")
-> general-purpose 子 Agent 独立运行
-> 子 Agent 返回最终结果
-> 父 Agent 只看到 task 的 ToolMessage
```

这个链路的关键是：父 Agent 不会拿到子 Agent 内部每一步工具调用的完整上下文，只拿最终结果。上下文隔离就是这么来的。

## 最小代码

文件：`deepagent_src/subagents_teach/01_default_general_purpose.py`

```python
agent = create_deep_agent(
    model=get_real_model(),
    system_prompt="delegate to the general-purpose subagent",
)
```

## 运行

```bash
uv run python deepagent_src/subagents_teach/01_default_general_purpose.py
```

预期输出末尾：

```text
default general-purpose subagent real agent ok
```

## 验证方式

脚本真实调用主 Agent，并断言父 Agent 收到的 `task` 工具结果中包含 `default-general-purpose-subagent-called`。

你在输出里会看到：

```text
Tool Calls:
  task
    subagent_type: general-purpose
Tool Message:
  default-general-purpose-subagent-called
```

这说明主 Agent 不是自己回答，而是真实委派给了默认 subagent。

## 常见误区

默认 subagent 不是另一个常驻后台进程。同步 subagent 调用会阻塞主 Agent，直到子 Agent 返回最终结果。

另一个误区是以为 general-purpose 什么都“最合适”。它只是默认通用工具人，生产里稳定任务还是应该写明确的自定义 subagent。
