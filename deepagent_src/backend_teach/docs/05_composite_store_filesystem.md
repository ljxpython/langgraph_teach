# 05 State + Store + Filesystem

## 学习目标

在一个 Agent 中同时使用三种 Backend：

```text
/draft-*       -> StateBackend：线程临时文件
/memories/*    -> StoreBackend：本地 SQLite，跨 thread 共享
/workspace/*   -> FilesystemBackend：本地普通文件
```

代码见 [`../05_composite_store_filesystem.py`](../05_composite_store_filesystem.py)。

## 关键结构

```python
backend = CompositeBackend(
    default=StateBackend(),
    routes={
        "/memories/": StoreBackend(namespace=lambda _rt: ("demo-user",)),
        "/workspace/": FilesystemBackend(root_dir=workspace, virtual_mode=True),
    },
)
```

`CompositeBackend` 在最外层。`StoreBackend` 和 `FilesystemBackend` 都只是它的路由目标，不能反过来嵌套 Composite。

## 运行

```bash
uv run python deepagent_src/backend_teach/05_composite_store_filesystem.py
```

运行调用模型两次，产生 API 费用。

执行过程：

1. `thread-a` 写入三种路径。
2. `thread-b` 读取三种路径。
3. `thread-b` 能读到 `/memories/` 和 `/workspace/`，读不到 `/draft-`。

## 真实本地持久化在哪里

```text
deepagent_src/backend_teach/backend_store.sqlite
    -> StoreBackend 的 /memories/* 数据

deepagent_src/backend_teach/workspace/report-*.txt
    -> FilesystemBackend 的 /workspace/* 数据
```

`backend_store.sqlite` 是数据库文件，不是可直接按普通文本阅读的 Markdown 文件；`workspace/` 下则是普通文件，可直接打开编辑。

## 为什么 State 没有落盘

示例使用 `InMemorySaver()`。因此 `/draft-*` 只存在本次 Python 进程中对应的 `thread-a` state：

- `thread-b` 看不到。
- 程序退出后消失。

## namespace 的意义

示例固定使用：

```python
namespace=lambda _rt: ("demo-user",)
```

所以两个 thread 共享 `/memories/*`。多用户应用必须改为按用户身份生成 namespace，例如：

```python
namespace=lambda rt: (rt.server_info.user.identity,)
```

否则不同用户会访问同一份记忆数据。

## 本课结论

`CompositeBackend` 让你按用途选择存储：短命草稿放 State，结构化长期记忆放 Store，用户想直接看到的文件放 Filesystem。

## 问题：StoreBackend 和 FilesystemBackend 都能共享，效果一样吗？

对 Agent 来说，它们都能通过同一个路径读写文件；但“为什么能共享”完全不同。

| 对比项 | StoreBackend | FilesystemBackend |
| --- | --- | --- |
| 文件实际位置 | LangGraph `BaseStore` | 操作系统真实目录 |
| 共享依据 | 相同 `namespace` | 相同 `root_dir` |
| 隔离用户的常用方式 | namespace 按用户 ID 划分 | 每个用户单独目录，外加权限规则 |
| 人能否直接用编辑器打开 | 通常不能；它可能在数据库中 | 可以，普通文件 |
| 部署时 | 可由 LangGraph/LangSmith 平台提供 Store | 需要挂载磁盘或卷 |
| 重启后是否保留 | 取决于 Store 实现 | 磁盘不丢就保留 |
| 典型内容 | 用户偏好、记忆、共享指令 | 报告、代码、CSV、用户下载文件 |

例如两个 Agent 都映射到同一个目录：

```text
FilesystemBackend(root_dir="/data/project")
    -> 两个 Agent 都能看到 /data/project 下的真实文件
```

这不是“按用户隔离”的共享。只要操作系统允许访问该目录，就都能看到；要隔离用户，需要不同目录，例如 `/data/users/alice` 与 `/data/users/bob`，并配合 Permissions。

而 StoreBackend 的共享是逻辑分区：

```text
namespace ("alice",) -> Alice 的文件空间
namespace ("bob",)   -> Bob 的文件空间
```

同一个 Store 可以保存很多 namespace，应用不必手动拼接真实目录。它特别适合“每个用户一份长期记忆”，不适合让用户直接打开文件修改。

还有一个反例：

```python
store=InMemoryStore()
```

它能跨 thread 共享，但进程退出就清空；所以“能共享”不等于“能持久化”。本课的 `SqliteStore` 才会写入本地数据库文件。

## 问题：`namespace=lambda _rt: ("demo-user",)` 是什么语法？

拆开看：

```python
namespace = lambda _rt: ("demo-user",)
```

它等价于：

```python
def namespace_factory(_rt):
    return ("demo-user",)


namespace = namespace_factory
```

每一部分的意思：

| 片段 | 含义 |
| --- | --- |
| `namespace=` | 把“生成存储分区”的函数传给 StoreBackend |
| `lambda` | 一行定义匿名函数 |
| `_rt` | LangGraph Runtime 参数；这里没有使用，前导 `_` 表示故意不用 |
| `("demo-user",)` | 返回只有一个元素的 tuple，表示存储分区 |

最后那个逗号不能省：

```python
("demo-user")   # 只是 str，不是 tuple
("demo-user",)  # 一个元素的 tuple，正确
```

这个示例每次都返回相同 namespace：

```text
不管 thread-a 还是 thread-b -> ("demo-user",)
```

因此它们共享 `/memories/`。这是教学用固定房间号；真实多用户系统不要这么写。

部署到 LangGraph Server 时，通常按当前用户身份生成 namespace：

```python
StoreBackend(
    namespace=lambda rt: (rt.server_info.user.identity,),
)
```

含义是：运行时传入 `rt`，函数从中取出当前登录用户 ID，再返回该用户专属的 tuple。Alice 得到 `("alice",)`，Bob 得到 `("bob",)`，所以两人即使都写 `/memories/profile.md`，实际也是两个隔离空间。

一句话：`root_dir` 是真实文件夹位置；`namespace` 是 Store 里的逻辑房间号。
