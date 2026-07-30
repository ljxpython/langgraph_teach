# Deep Agents Subagents 学习路线

## 学习主题

这部分学习 Deep Agents 的 subagents：主 Agent 通过 `task` 工具把复杂工作委派给子 Agent，让中间工具调用和上下文膨胀留在子 Agent 里。艹，别见啥都派子 Agent，简单一步任务直接做就行；subagent 主要解决多步骤、专业化和上下文隔离。

## 课程大纲

### 00 覆盖清单与常用程度

目标：先知道本教程覆盖了哪些知识点，哪些是高频主线，哪些是高级能力。

### 01 默认 general-purpose subagent

目标：理解 Deep Agents 默认会自动添加同步 `general-purpose` subagent，主 Agent 可以通过 `task` 工具委派。

### 02 自定义字典 subagent

目标：理解 `name`、`description`、`system_prompt`、`tools` 这些字段如何组成一个专用 subagent。

### 03 runtime context 传播

目标：理解父 Agent `invoke(..., context=...)` 传入的 runtime context 会自动传给 subagent。

### 04 structured output

目标：理解 `response_format` 如何让父 Agent 收到 JSON 字符串，而不是自由文本。

### 05 关闭同步 subagents

目标：理解如何通过 HarnessProfile 禁用默认 general-purpose subagent，从而让 Agent 没有 `task` 工具。

### 06 async subagents

目标：理解 async subagent 的配置、工具入口和本地可验证边界。

## 推荐学习顺序

1. 先读 [00 覆盖清单与常用程度](00_coverage_and_usage.md)，别上来就扎进高级分支。
2. 先学默认 general-purpose，知道 `task` 工具是什么。
3. 再学自定义 subagent，掌握最常用的字典配置。
4. 然后学 context 和 structured output，解决真实业务里的数据传递和结果可解析。
5. 最后学禁用同步 subagent 与 async subagent，理解边界和部署要求。

## 最常用的部分

高频必学：

- `task` 工具：同步 subagent 委派入口。
- 字典式 `SubAgent`：`name`、`description`、`system_prompt`、`tools`。
- 工具最小化：每个 subagent 只给必要工具。
- runtime context 传播：用户 ID、session、权限位不要塞 prompt。
- concise result：子 Agent 返回总结，不把中间工具日志塞回父 Agent。

中频常用：

- `response_format`：父 Agent 要继续处理结构化结果时用。
- 禁用 `general-purpose`：不允许委派或要控制工具面时用。
- streaming / `lc_agent_name` tracing：调试和观测时用。

低频或高级：

- `CompiledSubAgent`：已经有复杂 LangGraph 才需要。
- dynamic subagents：需要 interpreter middleware，适合批量 fan-out 编排。
- async subagents：需要 Agent Protocol 服务，适合后台长任务、可取消、可追加指令。

## Sync vs Async

```text
同步 subagent：主 Agent 调 task -> 等 subagent 完成 -> 收到最终结果
异步 subagent：主 Agent 调 start_async_task -> 立刻拿 task_id -> 后续 check/update/cancel/list
```

本教程同步章节都执行真实 Agent 调用。async 章节不启动远端 Agent Protocol 服务，只验证 async middleware 暴露的 `list_async_tasks` 工具；真正 `start_async_task` 需要 co-deployed ASGI graph 或远端 Agent Protocol server。

## 字典 SubAgent 字段速查

| 字段 | 是否常用 | 作用 | 备注 |
| --- | --- | --- | --- |
| `name` | 必用 | `task` 调用时的 subagent 类型 | 必须唯一 |
| `description` | 必用 | 帮主 Agent 判断何时委派 | 写得越具体越稳定 |
| `system_prompt` | 必用 | 子 Agent 自己的行为规则 | 不继承主 Agent prompt |
| `tools` | 高 | 子 Agent 可用工具 | 指定后覆盖继承工具集合 |
| `model` | 中 | 给子 Agent 换模型 | 长文档、代码、财务可按任务换模型 |
| `skills` | 中 | 子 Agent 自己的 skill 源 | 自定义 subagent 不自动继承主 Agent skills |
| `response_format` | 中高 | 返回结构化 JSON | 父 Agent 要解析结果时很有用 |
| `permissions` | 中 | 子 Agent 文件系统权限 | 指定后替换父权限 |
| `middleware` | 中低 | 子 Agent 额外 middleware | 自定义日志、限制、工具面时用 |
| `interrupt_on` | 中低 | 子 Agent 人工审批 | 需要 checkpointer |

## 高级知识点速览

### CompiledSubAgent

`CompiledSubAgent` 用来接入你已经编译好的 LangGraph / LangChain agent graph。

```python
compiled_subagent = {
    "name": "data-analyzer",
    "description": "Analyze data with a prebuilt graph.",
    "runnable": compiled_graph,
}
```

常用程度：低到中。

什么时候用：你已经有一条复杂 LangGraph 工作流，不想把它重写成简单字典 subagent。

关键限制：`runnable` 的 state 必须有 `messages` key；它不会自动继承父 Agent 的 `state_schema`。

### Skills 继承与隔离

常用程度：中。

- `general-purpose` subagent 会继承主 Agent 的 skills。
- 自定义 subagent 不自动继承主 Agent skills。
- 自定义 subagent 如果需要 skills，要自己写 `skills=[...]`。
- 子 Agent 加载过的 skill 不会反向传播给父 Agent。

这个规则很重要。艹，别以为主 Agent 会的 skill 子 Agent 都会，只有默认 general-purpose 是特殊情况。

### Permissions / Middleware / Interrupt

常用程度：中低，生产场景重要。

- `permissions`：子 Agent 指定后会替换父 Agent 文件系统权限，不是追加。
- `middleware`：子 Agent 额外 middleware 不继承主 Agent middleware。
- `interrupt_on`：子 Agent 可以单独设置人工审批，但需要 checkpointer。

这些是安全和治理能力，入门先知道边界；等你做真实文件写入、审批、生产权限隔离时再展开。

### Streaming 与 `lc_agent_name`

常用程度：中。

Deep Agents 可以流式输出主 Agent 和 subagent 的事件。调试时可以用 `subgraphs=True` 或 `stream_events` 看子 Agent 进度。LangSmith trace 里会把 agent 名称写到 metadata 的 `lc_agent_name`，方便过滤某个 subagent 的运行记录。

本教程没有单独做 streaming 脚本，因为当前课程重点是 subagent 配置和委派；项目已有 `agent_output.py` 可以打印完整消息链，够入门观察。

### Dynamic subagents

常用程度：低，高级。

Dynamic subagents 不是普通 `task` 委派，而是配合 interpreter middleware，让 Agent 在代码里批量调度 subagents。适合“审查目录下每个文件”“批量处理一堆 ticket”这种 fan-out 工作流。

需要额外 interpreter 依赖和运行时，本教程不引入新依赖。先学会同步 subagent，再碰它。

## 本地版本

- `deepagents==0.6.12`
- 示例通过 `_model.py` 复用项目已有 `deepagent_src.llms.get_gpt_model()`，会执行真实 Agent 调用。
- 示例通过 `deepagent_src.agent_output.invoke_and_pretty_print()` 打印完整消息链。
- 官方资料来源：`https://docs.langchain.com/oss/python/deepagents/subagents` 和 `https://docs.langchain.com/oss/python/deepagents/async-subagents`

## 当前章节

- [00 覆盖清单与常用程度](00_coverage_and_usage.md)
- [01 默认 general-purpose subagent](01_default_general_purpose.md)
- [02 自定义字典 subagent](02_custom_subagent.md)
- [03 runtime context 传播](03_context_propagation.md)
- [04 structured output](04_structured_output.md)
- [05 关闭同步 subagents](05_disable_subagents.md)
- [06 async subagents](06_async_subagents.md)
