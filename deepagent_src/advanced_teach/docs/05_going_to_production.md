# 第五章：Going to Production

生产 Deep Agent 的核心不是“把本地 `agent` 变量直接部署出去”，而是让每个 run 带着稳定的 `thread_id` 和本次请求的 `context`。当后端资源依赖 `thread_id`，例如 thread-scoped sandbox 时，导出的 Agent 应该是 async graph factory：平台每次运行调用 factory，factory 查找或创建正确 sandbox 后返回本次运行的图。

## 最小代码

代码在 `deepagent_src/advanced_teach/05_going_to_production.py`。

本章用 `LocalShellBackend` 在临时目录模拟生产 sandbox。真实生产把 registry 换成 `SandboxClient` + `LangSmithSandbox`；核心映射关系不变：

```python
async def build_agent(config: RunnableConfig, registry: ThreadBackendRegistry):
    thread_id = config["configurable"]["thread_id"]
    backend = await registry.get_or_create(thread_id)
    return create_deep_agent(
        model=get_gpt_model(disable_tool_streaming=True),
        backend=backend,
        subagents=[],
    )
```

例子会实际调用一次 LLM，让 `alpha` 线程的 Agent 用 `write_file` 写 `/thread-note.txt`。随后直接检查 backend：

1. 再次为 `alpha` 调 factory，拿到同一个 backend。
2. 为 `beta` 调 factory，拿到不同 backend。
3. `alpha` 和 `beta` 写同一路径，但内容互不影响。

## 运行命令

```bash
uv run python -m deepagent_src.advanced_teach.05_going_to_production
```

这会触发一次真实 LLM 调用，并只在临时目录中写文件。没有 `CHATGPT_API_KEY` 或 `CHATGPT_API_URL` 时，真实调用会失败。

## 预期现象

```text
alpha backend id: local-...
beta backend id: local-...
graph factory thread-scoped production pattern ok
```

两个 backend ID 不同，但同一 `thread_id="alpha"` 的两次 factory 调用复用同一个 backend。

## `thread_id` 与 `context`

两者容易混，职责完全不同：

| 数据 | 作用域 | 用途 |
| --- | --- | --- |
| `config["configurable"]["thread_id"]` | 对话 / thread | checkpoint、消息历史、thread-scoped sandbox |
| `context` | 单次 run | `user_id`、功能开关、权限信息、短期请求元数据 |

同一个 `thread_id` 能连续对话并返回同一 sandbox；同一 thread 的不同 run 可以携带不同 `context`。不要把用户身份或 API key 塞进 `thread_id`。

## 生产骨架

部署根目录需要 `langgraph.json`，典型最小结构：

```json
{
  "dependencies": ["."],
  "graphs": {
    "agent": "./agent.py:agent"
  },
  "env": ".env"
}
```

真实部署的 graph factory 大致是：

```python
from deepagents.backends.langsmith import LangSmithSandbox
from langsmith.sandbox import SandboxClient

client = SandboxClient()

async def agent(config):
    thread_id = config["configurable"]["thread_id"]
    sandbox = client.create_sandbox(
        name=f"thread-{thread_id}",
        idle_ttl_seconds=3600,
    )
    return create_deep_agent(
        model="openai:gpt-5.5",
        backend=LangSmithSandbox(sandbox=sandbox),
    )
```

示意代码省略了“先按名称查已有 sandbox”的分支；实际代码必须先 lookup 再 create，避免同一线程并发请求各自创建环境。sandbox 生命周期通常用 idle TTL 清理。

## 常见误区

不要把 `LocalShellBackend` 部署到服务端。它访问宿主机文件系统，只适合本地教学。生产执行代码要用隔离 sandbox，并通过 sandbox auth proxy 注入外部服务凭证，sandbox 内不要保存用户 API key。

也不要误以为 factory 每次运行返回新的 graph 就必然浪费很大。graph factory 的必要性来自运行时资源绑定；真正昂贵的通常是 sandbox 创建。通过按 `thread_id` 命名、查找复用和 TTL 管理，避免重复创建即可。

## 验证

1. `alpha` 的两次 factory 调用复用同一个 backend。
2. `alpha` 与 `beta` 的 backend 不同。
3. 真实 LLM 在 `alpha` backend 中调用 `write_file`。
4. 两个 thread 在相同虚拟路径下读到各自内容。

官方依据：`/oss/python/deepagents/going-to-production` 说明 `thread_id` 用于对话与 checkpoint，`context` 用于 per-run 数据；需要 thread-scoped sandbox 时，使用 async graph factory 从 `config["configurable"]["thread_id"]` 解析 sandbox，并用 TTL 清理闲置环境。
