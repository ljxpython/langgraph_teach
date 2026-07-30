# 06 async subagents

## 它是什么

Async subagent 是后台任务模式：主 Agent 启动任务后立刻拿到 task ID，后续可以 check、update、cancel 或 list。它依赖 Agent Protocol server；可以是同部署 ASGI transport，也可以是远端 HTTP transport。它适合长任务、并行任务和需要中途追加指令的任务。

## 常用程度

中到低，取决于系统形态。普通脚本和本地学习很少需要 async subagent；产品级长任务、多后台 worker、用户可继续聊天的场景会用到。

适合：

- 研究、代码生成、批量分析这种可能跑很久的任务。
- 用户启动任务后还要继续聊天。
- 任务需要中途追加指令或取消。

不适合：

- 父 Agent 必须马上拿到结果才能继续。
- 没有 Agent Protocol 服务或 co-deployed graph。
- 本地入门阶段，只想理解 subagent 基础委派。

## 工具生命周期

配置 async subagent 后，supervisor 会看到这些工具：

```text
start_async_task  -> 启动后台任务，立刻返回 task_id
check_async_task  -> 查询状态和结果
update_async_task -> 给运行中任务追加指令
cancel_async_task -> 取消任务
list_async_tasks  -> 列出当前 supervisor 跟踪的任务
```

典型链路：

```text
用户：开始研究 X
-> supervisor 调 start_async_task
-> 返回 task_id
-> supervisor 先把 task_id 告诉用户
-> 用户稍后问进度
-> supervisor 调 check_async_task 或 list_async_tasks
```

不要启动后立刻疯狂 check，那就把 async 又写回同步阻塞了，憨批设计。

## transport 边界

- 不写 `url`：ASGI transport，要求 supervisor 和 subagent graph 在同一个部署里。
- 写 `url`：HTTP transport，调用远端 Agent Protocol server。
- `graph_id`：远端或同部署里注册的 graph/assistant ID。
- `headers`：自托管服务的额外认证头。

本教程不启动 `start_async_task`，因为当前项目没有为 `graph_id="researcher"` 启动 Agent Protocol 服务；贸然跑只会失败。

## 最小代码

文件：`deepagent_src/subagents_teach/06_async_subagents.py`

```python
async_researcher: AsyncSubAgent = {
    "name": "async-researcher",
    "description": "Background research agent for long-running work.",
    "graph_id": "researcher",
}
```

## 运行

```bash
uv run python deepagent_src/subagents_teach/06_async_subagents.py
```

预期输出末尾：

```text
async subagent tool real agent ok
```

## 验证方式

脚本真实调用主 Agent，并要求它调用 `list_async_tasks`。这个工具只读取 supervisor 的 async task 状态，不需要真正启动远端 subagent，因此本地可验证。

## 常见误区

配置 `AsyncSubAgent` 不等于本地已经有可启动的后台 Agent。真正调用 `start_async_task` 需要 `graph_id` 对应的 Agent Protocol 服务存在，否则启动会失败。

另一个误区是把 async subagent 当成“更高级的同步 subagent”。它不是替代品，而是后台任务模型；需要任务状态管理、部署拓扑和失败处理。
