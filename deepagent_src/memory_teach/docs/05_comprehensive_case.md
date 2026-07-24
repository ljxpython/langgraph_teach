# 05 综合案例：真实 Agent 读取 Memory

## 学习目标

把 memory 文件、backend、namespace、权限和实时输出串成一个真实 Agent 调用。

## 场景

我们做一个 memory 教学助手：

- `/memories/AGENTS.md` 是 user-scoped memory。
- `/policies/AGENTS.md` 是 org-scoped policy memory。
- 两者都存在 `InMemoryStore`，但 namespace 不同。
- `memory=[...]` 让 Agent 启动时加载这两个文件。
- 权限禁止写 `/policies/**`。
- 输出使用 `stream_debug_trace()` 实时打印输入消息、节点更新、模型 chunk 和工具调用摘要。

## 真实 Agent 调用

代码见 [`../05_comprehensive_case.py`](../05_comprehensive_case.py)。

核心形态：

```python
messages = [HumanMessage(content="请根据已加载的长期 memory 回答问题。")]
stream_debug_trace(
    graph,
    {"messages": messages},
    {"configurable": {"thread_id": "memory-comprehensive-case"}},
)
```

## 运行

```bash
uv run python deepagent_src/memory_teach/05_comprehensive_case.py
```

注意：这会调用 `deepagent_src.llms.get_gpt_model()`，会产生真实模型请求和可能的 API 费用。

## 你应该从这个案例记住什么

1. `memory=[...]` 指定启动时加载的长期 memory 文件。
2. `StoreBackend` namespace 决定 memory scope。
3. `CompositeBackend` route 会剥掉前缀，store key 要按路由后的路径写。
4. shared policy memory 要只读。
5. 后续教学用 `stream_debug_trace()` 看输入消息、流式 chunk、节点更新和工具调用。
