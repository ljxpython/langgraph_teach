# 04 StoreBackend

## 学习目标

理解一句话：`StoreBackend` 把文件存进 LangGraph Store，使不同 thread 可以共享文件。

## 示例

代码见 [`../04_store_backend.py`](../04_store_backend.py)。

核心配置：

```python
agent = create_deep_agent(
    model=gpt_model,
    backend=StoreBackend(namespace=lambda _rt: ("demo-user",)),
    store=InMemoryStore(),
    checkpointer=InMemorySaver(),
)
```

示例执行两步：

```text
thread-a 写入 /memory.txt
thread-b 读取 /memory.txt
```

两个 thread 使用相同 namespace `("demo-user",)`，所以能访问同一份文件。

## 运行

在项目根目录执行：

```bash
uv run python deepagent_src/backend_teach/04_store_backend.py
```

运行调用模型两次，产生 API 费用。

## 三个容易混淆的概念

### thread_id

标识一次对话线程。它决定 checkpointer 保存和恢复哪一份 Agent state。

```python
{"configurable": {"thread_id": "thread-a"}}
```

### namespace

标识 Store 中的数据空间。它决定哪些运行共享 Backend 文件。

```python
StoreBackend(namespace=lambda _rt: ("demo-user",))
```

### Store

真正保存数据的容器。

```python
store=InMemoryStore()
```

关系如下：

```text
thread_id  -> 隔离对话 state
namespace  -> 隔离 StoreBackend 文件
Store      -> 实际保存文件数据
```

## 为什么不同 thread 能读取

`thread-a` 和 `thread-b` 的对话 state 是分开的，但它们的 namespace 相同：

```text
thread-a -> namespace demo-user -> /memory.txt
thread-b -> namespace demo-user -> /memory.txt
```

如果 namespace 不同，两个 thread 就会看到不同的文件空间。

## 多用户隔离

生产环境应按登录用户生成 namespace：

```python
StoreBackend(
    namespace=lambda rt: (rt.server_info.user.identity,),
)
```

结果：

```text
user-a -> namespace ("user-a",)
user-b -> namespace ("user-b",)
```

千万不要在多用户应用里给所有人使用同一个固定 namespace，否则用户数据会互相可见。

## InMemoryStore 是否真正持久化

本课使用 `InMemoryStore` 是为了让示例最简单：

- 可以跨 thread 共享。
- 只能在当前 Python 进程中保存。
- 程序退出后数据消失。

生产环境需要换成 Redis、Postgres、云 Store，或使用 LangSmith Deployment 自动提供的 Store。

## StoreBackend 与 StateBackend

| 对比项 | StateBackend | StoreBackend |
| --- | --- | --- |
| 隔离依据 | thread_id | namespace |
| 默认跨 thread | 否 | 可以 |
| 典型数据 | 草稿、中间结果 | 用户偏好、长期指令 |
| 依赖组件 | checkpointer | BaseStore |

## 本课结论

`thread_id` 管对话，`namespace` 管共享范围，`Store` 管实际数据。长期记忆能不能安全使用，关键看 namespace 是否正确隔离。

## 常见误解：StoreBackend 能嵌套 CompositeBackend 吗？

不能。`StoreBackend` 是一个存储 Backend，不是路由器；它不知道“某个路径应该转给本地磁盘”。

`CompositeBackend` 才是外层路由器：

```text
Agent 文件工具
    -> CompositeBackend
        -> /memories/**  转给 StoreBackend
        -> /workspace/** 转给 FilesystemBackend
        -> 其他路径       转给 StateBackend
```

正确写法：

```python
from pathlib import Path

from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore

backend = CompositeBackend(
    default=StateBackend(),
    routes={
        "/memories/": StoreBackend(namespace=lambda _rt: ("demo-user",)),
        "/workspace/": FilesystemBackend(
            root_dir=Path("workspace").resolve(),
            virtual_mode=True,
        ),
    },
)

agent = create_deep_agent(
    model=gpt_model,
    backend=backend,
    store=InMemoryStore(),
)
```

结果：

```text
/draft.md             -> StateBackend：本次对话临时草稿
/memories/profile.md  -> StoreBackend：同一用户跨 thread 共享
/workspace/report.md  -> FilesystemBackend：本地磁盘持久化
```

技术上也可以把 `StoreBackend` 放在 `default`：

```python
CompositeBackend(
    default=StoreBackend(namespace=lambda _rt: ("demo-user",)),
    routes={"/workspace/": FilesystemBackend(root_dir="...", virtual_mode=True)},
)
```

但通常不推荐。Deep Agents 的内部结果和对话历史也会进入 default，导致它们被长期保存；多数项目选择 `StateBackend` 作为 default，只把明确的 `/memories/` 交给 Store。

## StateBackend 与 StoreBackend：到底差在哪里？

最短答案：`StateBackend` 的文件属于“这条对话”；`StoreBackend` 的文件属于“一个 namespace”。

| 问题 | StateBackend | StoreBackend |
| --- | --- | --- |
| 文件保存在哪里 | LangGraph 的 Agent state | LangGraph `BaseStore` |
| 用什么键隔离 | `thread_id` | `namespace` |
| 不同 thread 能否读取同一文件 | 默认不能 | namespace 相同就能 |
| 需要什么组件 | checkpointer | `store=` |
| 重启后是否存在 | 取决于 checkpointer | 取决于 Store 实现 |
| 典型用途 | 临时计划、草稿、工具结果 | 用户偏好、长期记忆、共享规则 |

看同一个文件路径最容易懂：

```text
StateBackend
thread-a 的 /note.txt  !=  thread-b 的 /note.txt

StoreBackend（同一 namespace）
thread-a 的 /note.txt  ==  thread-b 的 /note.txt

StoreBackend（不同 namespace）
user-a 的 /note.txt    !=  user-b 的 /note.txt
```

`thread_id` 是“一次对话的身份证”；`namespace` 是“一组共享记忆的房间号”。路径 `/note.txt` 只是房间里的文件名，不能单独决定文件是否共享。

还有一个容易踩坑的点：

```python
store=InMemoryStore()
```

它只证明“跨 thread 共享”，不证明“程序重启后仍存在”。进程退出后内存清空；要真正长期保存，需要替换成持久化的 `BaseStore` 实现或使用平台提供的 Store。
