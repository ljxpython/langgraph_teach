# 02 Sandbox 生命周期

Sandbox 是 Deep Agents 的执行环境后端：它让 Agent 不只读写文件，还能通过 `execute` 跑命令。生命周期问题解决的是“这个环境什么时候创建、什么时候复用、什么时候销毁”。生产里最常见的是 thread-scoped：每个 conversation 一个 sandbox，同一个 `thread_id` 后续 run 复用它，不同 thread 彼此隔离。

## 最小代码

本章代码在：

```text
deepagent_src/advanced_teach/02_sandbox_lifecycle.py
```

核心逻辑只有一个 registry：

```python
@dataclass
class ThreadSandboxRegistry:
    root_dir: Path
    sandboxes: dict[str, LocalShellBackend] = field(default_factory=dict)

    def get_or_create(self, thread_id: str) -> LocalShellBackend:
        if thread_id not in self.sandboxes:
            workspace = self.root_dir / f"thread-{thread_id}"
            workspace.mkdir(parents=True, exist_ok=True)
            self.sandboxes[thread_id] = LocalShellBackend(root_dir=workspace)
        return self.sandboxes[thread_id]
```

同一个 `thread_id` 会拿回同一个 backend；不同 `thread_id` 会创建不同 backend 和不同工作目录。官方生产文档里的 `SandboxClient.list_sandboxes()` / `create_sandbox(name=..., idle_ttl_seconds=...)` 做的就是同一件事，只是它创建的是远端隔离容器。

## 运行命令

```bash
uv run python -m deepagent_src.advanced_teach.02_sandbox_lifecycle
```

预期现象：

1. 输出两个不同 backend id，例如 `local-xxxx`。
2. `alpha` 两次获取的是同一个 backend，写入 `/note.txt` 后后续还能读到。
3. `beta` 是另一个 backend，`/note.txt` 内容和 `alpha` 不一样。
4. `execute("pwd")` 的输出分别落在 `thread-alpha` 和 `thread-beta` 临时目录。

## 生产写法

官方最新文档推荐生产中用 graph factory 读取 `config["configurable"]["thread_id"]`，再按名字查找或创建 sandbox：

```python
from deepagents import create_deep_agent
from deepagents.backends.langsmith import LangSmithSandbox
from langchain_core.runnables import RunnableConfig
from langsmith.sandbox import SandboxClient

client = SandboxClient()

async def agent(config: RunnableConfig):
    thread_id = config["configurable"]["thread_id"]
    sandbox_name = f"thread-{thread_id}"
    existing = [sb for sb in client.list_sandboxes() if getattr(sb, "name", None) == sandbox_name]
    ls_sandbox = existing[0] if existing else client.create_sandbox(
        name=sandbox_name,
        idle_ttl_seconds=3600,
    )
    return create_deep_agent(
        model="openai:gpt-5.5",
        backend=LangSmithSandbox(sandbox=ls_sandbox),
    )
```

这里不能用静态 graph，因为 sandbox 选择依赖每次 run 的 `thread_id`。所以生产里导出的 `agent` 是 async factory，LangGraph server 每次 run 调它，拿到本次 thread 对应的 backend 后再返回 agent graph。

## 常见误区

别把 `LocalShellBackend` 当成安全 sandbox。官方文档明确警告：`FilesystemBackend` 和 `LocalShellBackend` 会直接访问 host，不要在部署环境里用。它适合本地教学和开发验证；真正面向用户的 coding agent 要用 LangSmith Sandbox、Daytona、E2B、Modal 这类隔离 provider。

另一个坑是忘记 TTL。sandbox 会占资源和成本，不设置 `idle_ttl_seconds` 或清理策略，assistant-scoped sandbox 会越堆越脏，磁盘和依赖状态都会膨胀。

## 验证

本章不触发 LLM 调用。验证重点是 sandbox backend 的真实行为：文件写入、文件读取、命令执行、同 thread 复用、不同 thread 隔离。
