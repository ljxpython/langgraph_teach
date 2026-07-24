# 02 Agent scope 与 User scope

## 学习目标

理解一句话：memory 的隔离不靠文件名，主要靠 backend 的 namespace。

## 它是什么

同一个虚拟路径 `/memories/AGENTS.md`，在不同 `StoreBackend` namespace 下会读到不同内容。Agent-scoped memory 用同一个 namespace，让所有用户共享 Agent 的长期经验。User-scoped memory 用用户 ID 做 namespace，让 Alice 和 Bob 互相看不到对方记忆。

## 最小可运行例子

代码见 [`../02_scoped_memory.py`](../02_scoped_memory.py)。

这个例子把三份 memory 写进同一个 `InMemoryStore`：

- `("agent-memory",)`：Agent 共享记忆
- `("user-alice",)`：Alice 的用户记忆
- `("user-bob",)`：Bob 的用户记忆

三者都用同一个虚拟路径 `/memories/AGENTS.md`，但 namespace 不同，所以内容不同。

## 运行

```bash
uv run python deepagent_src/memory_teach/02_scoped_memory.py
```

预期输出：

```text
scoped memory ok
```

## 常见误区

`CompositeBackend` 会剥掉 route 前缀。`/memories/AGENTS.md` 路由到 `StoreBackend` 后，store 里的 key 是 `/AGENTS.md`，不是 `/memories/AGENTS.md`。这个坑很烦，写错就读不到。
