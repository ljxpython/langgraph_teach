# 06 生产化：动态用户 Memory 设计

## 学习目标

理解一句话：多用户场景不要给每个用户写一套代码，而是用同一个 Agent 和同一个 memory 路径，通过 namespace 动态隔离。

## 推荐设计

生产里通常这样分层：

- 认证层拿到 `user_id`。
- 应用层确保这个用户的 memory 文件存在。
- DeepAgent 使用同一个 `memory=["/memories/AGENTS.md"]`。
- `StoreBackend(namespace=...)` 根据当前用户生成 namespace。
- 所有用户都读写同一个虚拟路径，但实际落到不同 namespace。

```text
Alice -> namespace ("users", "alice") -> /AGENTS.md
Bob   -> namespace ("users", "bob")   -> /AGENTS.md
```

注意：`CompositeBackend` 路由 `/memories/` 到 `StoreBackend` 后，会剥掉 route 前缀。所以外部路径是 `/memories/AGENTS.md`，store key 是 `/AGENTS.md`。

## 本地最小例子

代码见 [`../06_production_user_memory_design.py`](../06_production_user_memory_design.py)。

这个例子演示动态新增用户：

- `ensure_user_memory(store, user_id)`：用户第一次出现时创建默认 memory。
- `create_backend_for_user(store, user_id)`：用 user_id 生成隔离 backend。
- Alice、Bob、新用户共用同一个路径 `/memories/AGENTS.md`，但读到不同内容。

## 生产版写法

在 LangSmith / 托管运行时里，namespace 可以直接来自当前请求身份：

```python
StoreBackend(
    namespace=lambda rt: ("users", rt.server_info.user.identity),
)
```

如果你自己用 FastAPI 包一层，通常在请求入口拿到 `user_id`，然后创建或选择这个用户对应的 graph/backend：

```python
def create_user_graph(user_id: str):
    backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/memories/": StoreBackend(
                namespace=lambda _rt: ("users", user_id),
            )
        },
    )
    return create_deep_agent(
        model=model,
        backend=backend,
        memory=["/memories/AGENTS.md"],
        store=store,
    )
```

## 关键原则

1. 不要为每个用户写不同的 memory 路径，路径固定，namespace 动态。
2. 不要把用户 ID 交给模型决定，必须来自认证系统。
3. 用户 memory 默认可写，组织 policy 默认只读。
4. 不要把 API key、token、密码放进 memory。
5. 并发写同一个 memory 文件会 last-write-wins，复杂场景用后台 consolidation 合并。

## 常见误区

最常见的坑是把用户隔离做在文件名上，比如 `/memories/alice.md`、`/memories/bob.md`。这能跑，但权限、检索、迁移都会越来越臭。namespace 才是 StoreBackend 的隔离边界，别把虚拟路径当数据库分区。
