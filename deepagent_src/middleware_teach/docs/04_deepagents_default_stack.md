# 第四章：Deep Agents 默认 middleware 栈

Deep Agents 不是另起炉灶的 Agent runtime，它是把 LangChain agent loop 和一组默认 middleware 打包成 harness。`create_deep_agent(..., middleware=[...])` 里的自定义 middleware 会插入 Deep Agents 默认栈中间，而不是替换整个栈。

## 最小代码

代码在 `deepagent_src/middleware_teach/04_deepagents_default_stack.py`。

```python
@before_model(name="custom_probe")
def custom_probe(state, runtime):
    return None

agent = create_deep_agent(
    model=FakeListChatModel(responses=["OK"]),
    subagents=[],
    middleware=[custom_probe],
)
graph_nodes = list(agent.get_graph().nodes.keys())
```

这章不调用模型，只编译 Deep Agent 并检查 LangGraph 节点。能稳定观察到的是：`PatchToolCallsMiddleware.before_agent` 在图里，你传入的 `custom_probe.before_model` 也在图里，并且排在 Patch 之后。

## 运行命令

```bash
uv run python -m deepagent_src.middleware_teach.04_deepagents_default_stack
```

## 预期现象

```text
base_stack: SkillsMiddleware -> FilesystemMiddleware -> SubAgentMiddleware -> SummarizationMiddleware -> PatchToolCallsMiddleware -> AsyncSubAgentMiddleware -> your middleware
tail_stack: harness profile extras -> tool exclusion -> prompt caching -> MemoryMiddleware -> HumanInTheLoopMiddleware
graph_nodes: ['__start__', 'model', 'tools', 'PatchToolCallsMiddleware.before_agent', 'custom_probe.before_model', '__end__']
deepagents default stack local check ok
```

## 默认主栈顺序

根据当前本地 `deepagents==0.7.0b2` 的 `create_deep_agent` docstring，主 agent 的顺序是：

1. `SkillsMiddleware`：只有传 `skills` 时出现。
2. `FilesystemMiddleware`：文件系统工具和权限的基础层。
3. `SubAgentMiddleware`：同步 subagent / `task` 工具。
4. `SummarizationMiddleware`：上下文变长后的压缩。
5. `PatchToolCallsMiddleware`：修复中断恢复或 malformed tool call 造成的悬空工具调用。
6. `AsyncSubAgentMiddleware`：只有配置 async subagents 时出现。
7. 你传入的 `middleware=[...]`。
8. Harness profile extras。
9. excluded-tool filtering。
10. prompt caching middleware。
11. `MemoryMiddleware`：只有传 `memory` 时出现。
12. `HumanInTheLoopMiddleware`：只有传 `interrupt_on` 时出现。

## 常见误区

不要以为 `middleware=[custom]` 会让 Deep Agents 只剩你的 middleware。艹，不会。文件系统、subagent、summarization、patch、memory、HITL 这些默认能力仍然按栈顺序存在；你只是把自己的逻辑插进去。

另一个坑是“图节点看不到全部 middleware”。`before_model` / `before_agent` 这类 node-style hook 会变成可见节点；`wrap_model_call` / `wrap_tool_call` 这类 wrap-style hook 是包在模型或工具执行器周围的，通常不会作为独立节点出现在 `get_graph().nodes`。

## 和前面三章的关系

第一章、第二章、第三章讲的是 LangChain middleware 的基本钩子。Deep Agents 默认栈说明这些钩子在真实 harness 里怎么排列：你的模型层逻辑、工具层逻辑不是孤立跑的，而是夹在 Deep Agents 已经组装好的能力层里。
