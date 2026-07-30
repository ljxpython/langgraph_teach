# 06 综合案例：长期记忆

## 它是什么

Long-term memory 用 `CompositeBackend` 把 `/memories/` 路由到 LangGraph Store，让信息跨 thread、跨会话保留。它解决的问题是：用户偏好、长期项目事实、研究进度不该只活在当前 thread 的 state 里。普通工作文件仍可以留在 `StateBackend` 或 `FilesystemBackend`，别全塞进长期存储。

## 最小代码

文件：`deepagent_src/context_engineering_teach/06_long_term_memory_case.py`

```python
backend = CompositeBackend(
    default=StateBackend(),
    routes={
        "/memories/": StoreBackend(
            store=store,
            namespace=lambda _rt: ("deepagents-context", "u-123"),
        )
    },
)
```

## 运行

```bash
uv run python deepagent_src/context_engineering_teach/06_long_term_memory_case.py
```

预期输出：

```text
long-term memory real agent ok
```

## 验证方式

脚本把用户偏好预写入 `InMemoryStore`，再通过 `/memories/user_preferences.txt` 读取，断言路由和 namespace 生效。最后真实调用 Agent，让 Agent 读取这份长期记忆。

## 常见误区

别把所有文件都放 `/memories/`。只有跨会话还稳定有价值的信息才进长期记忆，临时草稿和工具输出放默认 backend 就够了。
