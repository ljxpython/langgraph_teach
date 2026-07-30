# 第四章：多个远端 A2A Agent 编排

代码在 `deepagent_src/a2a_teach/04_multi_agent_orchestration.py`。

本章启动两个独立的本地 A2A 服务：

1. `quote-specialist`：真实 Deep Agent，负责报价。
2. `risk-specialist`：真实 Deep Agent，负责风险结论。

协调器也是一个真实 Deep Agent。它必须调用 `ask_specialists` 工具；该工具通过 `asyncio.gather()` 并发发送两个 A2A 请求，等待两个远端 Task 完成后把结果交给协调器汇总。

```bash
uv run python -m deepagent_src.a2a_teach.04_multi_agent_orchestration
```

预期输出类似：

```text
coordinator_tool_called: True
quote_agent_calls: 1
risk_agent_calls: 1
answer: 发票 inv-3001 的报价为 USD 108.00，风险状态为 approved。
multi a2a deep agent orchestration ok
```

## 这个例子验证了什么

三个模型调用都是真实的：协调器调用工具，两个远端 A2A Server 各自调用自己的 Deep Agent。断言同时验证协调工具被模型选中，并且两个远端 Executor 都恰好执行了一次。

`asyncio.gather()` 只适合两个任务彼此独立的 fan-out。本例中报价与风险没有依赖，因此应并行；若风险 Agent 必须先读取报价结果，则应该串行调用，不能为了“看起来并发”硬并发。

## A2A 与 Deep Agents Subagent 的边界

这里的远端 Specialist 是独立 HTTP 服务，有自己的 Agent Card、Task 生命周期、部署边界和身份策略，所以使用 A2A 合理。

同一进程、同一权限域的短任务优先用 Deep Agents 内置 `task`/subagent；不要把所有子任务都塞进 HTTP 协议，不然延迟、重试、认证和可观测性成本都会白白增加。

生产系统应为每个远端 Agent 单独设置认证 headers、超时、重试、熔断、任务取消和结果 schema。协调 Agent 不应把一个服务的凭据转发给另一个服务。
