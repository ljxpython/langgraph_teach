# 第三章：认证与远端能力授权

代码在 `deepagent_src/a2a_teach/03_auth_and_remote_capabilities.py`。

本章通过本地 Uvicorn A2A Server 发起一次真实 `gpt-5.5` Deep Agent 调用。模型必须调用 `lookup_invoice`，再把结果作为 A2A Task artifact 返回。

```bash
uv run python -m deepagent_src.a2a_teach.03_auth_and_remote_capabilities
```

预期输出类似：

```text
anonymous_status: 401
task_state: TASK_STATE_COMPLETED
tool_called: True
artifact: Invoice inv-2048: status=paid; amount=USD 128.50.
authenticated a2a deep agent real tool call ok
```

## 三个边界

1. `AgentCard.security_schemes` 和 `security_requirements` 向调用方声明 Bearer 认证要求；Card 是公开发现信息，不能单独作为访问控制。
2. `BearerAuthMiddleware` 在 A2A JSON-RPC 路由之前校验 Token。匿名 `POST /` 返回 `401`，不会进入 AgentExecutor。
3. `AuthContextBuilder` 把服务端验证出的身份和 `allowed_capabilities` 放进 `ServerCallContext`。Executor 只在服务端授予 `invoice_lookup` 时才会运行真实 Deep Agent。

调用方不能通过 A2A Message metadata、前端勾选项或 Agent Card 自己声明权限。它们最多是请求；Token/JWT、服务端权限策略以及每个工具或 MCP 的独立凭据才是授权依据。

自定义 `ServerCallContextBuilder` 时必须保留 `headers`。A2A SDK 通过 `A2A-Version` header 校验协议版本；漏掉它会被 SDK 按旧版 `0.3` 处理，导致 1.0 JSON-RPC 请求被错误拒绝。

## Skill、工具与 MCP 的区别

本例的 `AgentSkill` 仅用于描述“这个远端 Agent 可查询发票”。真正执行的是 Deep Agent 内部注册的 `lookup_invoice` 工具，并由服务端 capability 策略控制。

同理，远端 Agent 若接入 MCP，A2A Token 不应该自动转发成 MCP 凭据。应由远端服务按调用者身份获取最小权限的 MCP/OAuth Token，并在工具执行层再次校验租户、scope、审计和限流。

本例的 demo token 只适合教学。生产环境使用短期 JWT 或 OAuth access token，并把 token 校验、密钥轮换、scope 映射和审计移到专门的身份服务。

真实模型调用通常超过 HTTP 客户端默认的 5 秒读超时，所以示例将 A2A Client timeout 设为 60 秒。生产环境应根据任务 SLA 设置连接、读取、总时长和取消策略，不能无限等待。
