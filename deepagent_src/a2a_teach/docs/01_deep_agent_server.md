# 第一章：通过 A2A 暴露 Deep Agent

A2A 是 Agent-to-Agent 协议：调用方先读取远端的 Agent Card，了解它的接口和 Skill 元数据，再发送任务并接收 Message 或 Task。它不是 Deep Agent 的 `task` 工具，也不是 MCP；本例把一个真实 Deep Agent 包在 A2A Server 中，让另一个 A2A Client 通过 JSON-RPC 调用它。

## 最小代码

代码在 `deepagent_src/a2a_teach/01_deep_agent_server.py`。

`RemoteDeepAgentExecutor` 是 A2A 与 Deep Agent 的适配层：读取 `RequestContext` 中的 A2A 用户文本，调用 `agent.ainvoke`，并把最终文本作为 Task artifact 发布。

```python
state = await self.agent.ainvoke(
    {"messages": [HumanMessage(content=context.get_user_input())]}
)
await updater.add_artifact([new_text_part(state["messages"][-1].text)])
await updater.complete()
```

Executor 必须先 enqueue 一个初始 `Task`，之后才能发送 working、artifact 或 completed 更新。A2A SDK 用这个 Task 保存状态、历史与 artifact；直接先发 status 会被协议拒绝。

## 本地真实调用

```bash
uv run python -m deepagent_src.a2a_teach.01_deep_agent_server
```

这会发起一次真实 `gpt-5.5` 调用，但 A2A HTTP 通路使用 `httpx.ASGITransport` 在进程内执行：没有开放端口，也没有调用外部 A2A 服务。

客户端仍执行完整协议流程：

1. 从 `/.well-known/agent-card.json` 读取 Agent Card。
2. 根据 Card 选择 JSON-RPC transport。
3. 发送 `SendMessageRequest`。
4. Server 创建 Task，调用 Deep Agent，并发布 artifact 与 completed 状态。
5. Client 收到最终 Task，读取 artifact。

## 预期现象

```text
task_state: TASK_STATE_COMPLETED
artifact: A2A_REMOTE_OK: inv-1001
a2a deep agent real call ok
```

## 常见误区

`AgentSkill` 只是在 Agent Card 中声明远端能力，不能自动把本地 Skill 文件、工具、MCP 连接或权限同步给对方。远端服务仍要独立进行认证、授权、输入验证、超时与审计。

这个示例禁用 A2A streaming，目的是聚焦最小 Task 生命周期。长任务要在后续章节使用 streaming status/artifact updates、任务取消、`input_required` / `auth_required` 和持久化 TaskStore。

官方依据：A2A SDK 的 `AgentExecutor` 要求 Executor 发布 Message 或 Task，并在长任务中持续发布状态和 artifact 事件；`ClientFactory.create_from_url` 会先解析 Agent Card，再选择兼容 transport。
