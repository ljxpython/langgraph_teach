# A2A 教学

这个目录学习如何把 Deep Agent 暴露成标准 A2A Server，以及如何作为 Client 调用远端 Agent。

## 课程路线

1. `01_deep_agent_server`：Agent Card、JSON-RPC、Task 生命周期，以及 A2A Client 到 Deep Agent 的真实调用。
2. `02_streaming_and_cancel`：streaming status/artifact、客户端超时后显式取消远端 Task。
3. `03_auth_and_remote_capabilities`：Bearer 认证、调用方身份、服务端 capability 策略，以及真实 Deep Agent 工具调用。
4. `04_multi_agent_orchestration`：主 Deep Agent 通过工具并发调用多个远端 A2A Deep Agent，并汇总结果。

不要把 A2A 用作进程内 Subagent 的替代品：进程内、同一权限域的短任务优先用 Deep Agents 的 `task` 工具；跨服务、跨团队或异构框架的独立 Agent 才适合 A2A。
