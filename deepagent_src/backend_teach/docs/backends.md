# Deep Agents Backends 学习笔记

## 1. Backend 是什么

Backend 是 Deep Agents 文件工具背后的存储层。Agent 看到的是统一的虚拟文件系统：

- `ls`：列目录
- `read_file`：读文件，也能读取常见图片
- `write_file`：写文件
- `edit_file`：替换文件内容
- `delete`：删除文件（Backend 支持时才提供）
- `glob`：按文件名模式查找
- `grep`：搜索文件内容
- `execute`：执行命令，仅 Sandbox 和 `LocalShellBackend` 提供

核心关系只有一层：

```text
Agent 文件工具 -> Backend -> 实际存储位置
```

换 Backend，不需要改 Agent 使用文件工具的方式。

## 2. Backend 怎么选

| Backend | 文件存在哪里 | 生命周期 | 适合场景 |
| --- | --- | --- | --- |
| `StateBackend` | LangGraph state | 同一 thread | 临时草稿、中间结果 |
| `FilesystemBackend` | 本地磁盘 | 长期存在 | 本地项目、CI 挂载目录 |
| `LocalShellBackend` | 本地磁盘 | 长期存在 | 可信环境中的本地编程助手 |
| `StoreBackend` | LangGraph Store | 跨 thread | 用户记忆、长期指令 |
| `ContextHubBackend` | LangSmith Context Hub | 长期存在、有提交历史 | 共享 Agent/Skill 内容 |
| `CompositeBackend` | 按路径分流 | 由各子 Backend 决定 | 同时使用临时文件和持久文件 |
| Sandbox | 隔离环境 | 由 Sandbox 决定 | 生产环境中执行不可信代码 |

最简单的选择规则：

1. 只要临时文件：默认 `StateBackend`。
2. 要读写本地项目：`FilesystemBackend`。
3. 还要执行命令：开发环境用 `LocalShellBackend`，生产环境用 Sandbox。
4. 要跨会话记忆：`StoreBackend`。
5. 要把不同路径放到不同存储：`CompositeBackend`。

## 3. StateBackend：默认的线程内文件系统

不传 `backend` 时，Deep Agents 默认使用 `StateBackend`：

```python
from deepagents import create_deep_agent
from deepagent_src.llms import gpt_model

agent = create_deep_agent(model=gpt_model)
```

显式写法：

```python
from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from deepagent_src.llms import gpt_model

agent = create_deep_agent(model=gpt_model, backend=StateBackend())
```

知识点：

- 文件保存在当前 LangGraph thread 的 state 中。
- 配置 checkpointer 后，同一个 thread 的多次运行可以继续访问文件。
- 不同 thread 默认不共享文件。
- supervisor 和 subagent 共享当前 state 中的文件。
- 适合草稿和大工具结果，不适合长期用户记忆。
- 它依赖图运行上下文，不要把它当普通文件类在图外直接操作。

## 4. FilesystemBackend：读写真实磁盘

```python
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from deepagent_src.llms import gpt_model

agent = create_deep_agent(
    model=gpt_model,
    backend=FilesystemBackend(
        root_dir=Path("deepagent_src/backend_teach/workspace").resolve(),
        virtual_mode=True,
    ),
)
```

知识点：

- `root_dir` 指定 Agent 可以操作的根目录。
- `virtual_mode=True` 会限制 `..`、`~` 和根目录外的绝对路径。
- 文件修改直接落盘，具有永久性。
- Agent 可能读取 `.env`、密钥等敏感文件，根目录必须尽量小。
- 单独使用时，Deep Agents 的内部文件也会写进项目目录。

通常更推荐用 `CompositeBackend`，只把 `/workspace/` 映射到真实磁盘，内部文件仍放在 `StateBackend`。

## 5. LocalShellBackend：真实磁盘加 Shell

```python
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from deepagent_src.llms import gpt_model

agent = create_deep_agent(
    model=gpt_model,
    backend=LocalShellBackend(
        root_dir=Path("deepagent_src/backend_teach/workspace").resolve(),
        virtual_mode=True,
        env={"PATH": "/usr/bin:/bin"},
    ),
)
```

它比 `FilesystemBackend` 多一个 `execute` 工具。

必须记住：

- 命令通过宿主机 Shell 直接执行，没有隔离。
- 命令拥有当前用户权限，可以访问 `root_dir` 外的路径。
- `virtual_mode=True` 只能约束文件工具，不能约束 Shell 命令。
- 只用于可信的本地开发环境；生产环境使用 Sandbox。
- 可配置 `timeout`、`max_output_bytes`、`env` 和 `inherit_env`。

## 6. StoreBackend：跨 thread 持久化

```python
from deepagents import create_deep_agent
from deepagents.backends import StoreBackend
from deepagent_src.llms import gpt_model
from langgraph.store.memory import InMemoryStore

agent = create_deep_agent(
    model=gpt_model,
    backend=StoreBackend(namespace=lambda _rt: ("demo-user",)),
    store=InMemoryStore(),
)
```

知识点：

- 文件存进 LangGraph `BaseStore`，可以跨 thread 读取。
- 本地学习可用 `InMemoryStore`；进程结束后数据消失。
- 生产环境可接 Redis、Postgres 或平台提供的 Store。
- 部署到 LangSmith Deployment 时，平台会自动提供 Store。
- 新代码必须显式设置 `namespace`，防止不同用户的数据串到一起。

常见 namespace：

```python
# 每个用户独立
StoreBackend(namespace=lambda rt: (rt.server_info.user.identity,))

# 每个 thread 独立
StoreBackend(namespace=lambda rt: (rt.execution_info.thread_id,))

# 固定共享空间
StoreBackend(namespace=lambda _rt: ("shared", "memories"))
```

namespace 只允许字母、数字、`-`、`_`、`.`、`@`、`+`、`:`、`~`，不能包含 `*` 或 `?`。

## 7. ContextHubBackend：把文件放进 Context Hub

```python
from deepagents import create_deep_agent
from deepagents.backends import ContextHubBackend
from deepagent_src.llms import gpt_model

agent = create_deep_agent(
    model=gpt_model,
    backend=ContextHubBackend("my-agent"),
)
```

知识点：

- 需要有效的 `LANGSMITH_API_KEY`。
- 文件保存在 LangSmith Context Hub 仓库中。
- 首次访问时拉取，之后从内存缓存读取。
- 写入会形成 Hub commit。
- 多个写入者可能发生 parent commit 冲突，需要重新拉取后重试。
- 适合共享 Agent 指令、`AGENTS.md` 和 Skills。

## 8. CompositeBackend：按路径路由

这是最实用的组合：临时数据留在 state，项目文件才写入磁盘。

```python
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from deepagent_src.llms import gpt_model

backend = CompositeBackend(
    default=StateBackend(),
    routes={
        "/workspace/": FilesystemBackend(
            root_dir=Path("deepagent_src/backend_teach/workspace").resolve(),
            virtual_mode=True,
        )
    },
)

agent = create_deep_agent(model=gpt_model, backend=backend)
```

路由结果：

```text
/workspace/app.py             -> FilesystemBackend
/large_tool_results/result    -> StateBackend
/conversation_history/thread  -> StateBackend
```

规则：

- 按路径前缀匹配。
- 更长、更具体的前缀优先。
- `ls`、`glob`、`grep` 会聚合多个 Backend 的结果。
- 返回路径仍保留 Agent 看到的原始前缀。

## 9. Permissions：在 Backend 前拦截访问

```python
from deepagents import FilesystemPermission, create_deep_agent

agent = create_deep_agent(
    model=gpt_model,
    backend=backend,
    permissions=[
        FilesystemPermission(
            operations=["write"],
            paths=["/workspace/config/**"],
            mode="deny",
        )
    ],
)
```

知识点：

- 权限规则在调用 Backend 前执行。
- `operations` 当前控制 `read` 或 `write`。
- `mode` 支持 `allow`、`deny`、`interrupt`。
- `interrupt` 可接入 Human-in-the-Loop 审批。
- Permissions 不是操作系统沙箱，不能限制 `LocalShellBackend.execute` 执行的命令。

## 10. 自定义 Backend

需要接 S3、数据库或远程文件系统时，实现 `BackendProtocol`：

```text
ls      列目录
read    读文件，支持 offset/limit
write   创建文件
edit    查找并替换内容
glob    匹配路径
grep    搜索文本
delete  可选；不实现就不向模型暴露删除工具
```

关键约束：

- 返回 `LsResult`、`ReadResult`、`WriteResult` 等结构化结果。
- 失败时填写结果对象的 `error`，不要抛异常。
- `write` 是 create-only；文件已存在应返回错误。
- `edit` 默认要求 `old_string` 只出现一次；批量替换要显式设置 `replace_all=True`。
- `ls` 结果按 path 排序，保证输出稳定。
- 要支持命令执行，应实现 `SandboxBackendProtocol` 的 `execute`。

## 11. 自定义策略钩子

路径权限不够用时，可以包装或继承 Backend，实现：

- 写入内容审查
- 审计日志
- 限流
- 文件大小限制
- 特定目录禁止编辑

原则是返回带 `error` 的结果，不要让策略异常直接炸掉 Agent。

## 12. 新版迁移知识

`deepagents 0.5.0` 起，Backend factory 已弃用。

```python
# 旧写法，不再推荐
backend=lambda rt: StateBackend(rt)

# 新写法
backend=StateBackend()
```

`deepagents 0.5.2` 起，namespace factory 直接收到 LangGraph `Runtime`：

```python
# 旧写法
namespace=lambda ctx: (ctx.runtime.context.user_id,)

# 新写法
namespace=lambda rt: (rt.server_info.user.identity,)
```

当前项目安装的是 `deepagents 0.6.12`，后续示例统一使用新写法。

## 13. 建议学习顺序

1. `StateBackend`：理解 thread 内临时文件。
2. `FilesystemBackend`：观察 Agent 如何真实读写文件。
3. `CompositeBackend`：理解虚拟路径和路由。
4. `StoreBackend`：理解跨 thread 持久化与 namespace 隔离。
5. Permissions：限制读写范围。
6. `LocalShellBackend`：理解 `execute` 与安全边界。
7. 自定义 Backend：最后再学协议，不要一上来造轮子。

## 14. 后续最小示例规划

后续代码放在 `deepagent_src/backend_teach/`，每个文件只演示一个知识点：

```text
01_state_backend.py
02_filesystem_backend.py
03_composite_backend.py
04_store_backend.py
05_permissions.py
06_local_shell_backend.py
```

所有示例统一复用：

```python
from deepagent_src.llms import gpt_model
```

不重复创建模型，不引入额外框架，不先写自定义 Backend。

## 15. 一句话总结

Backend 决定“Agent 的文件实际放在哪里”，Composite 决定“不同路径交给谁”，Permissions 决定“哪些路径允许读写”，Sandbox 决定“代码在哪里执行”。
