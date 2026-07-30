# 第四章：Fault Tolerance

Fault Tolerance 是让 Agent 在真实生产错误里继续可靠工作的能力。它不是把所有异常吞掉，而是按错误类型分流：临时网络错误自动重试，可由模型修正的工具错误转成 `ToolMessage`，需要人判断的操作交给 HITL，无法处理的未知异常直接暴露给开发者。

## 最小代码

代码在 `deepagent_src/advanced_teach/04_fault_tolerance.py`。

本章只演示一个核心点：工具参数错了，但这个错误模型可以修正。`lookup_invoice` 第一次收到 `bad-id` 会抛出 `ValueError`，`ToolErrorMiddleware` 捕获后把错误转成工具消息，模型看到提示后用 `inv_1001` 再调用一次。

关键逻辑：

```python
def recover_tool_error(exc: Exception, request: Any) -> str | None:
    if not isinstance(exc, ValueError):
        return None
    tool_name = request.tool_call["name"]
    return f"Tool `{tool_name}` failed: {exc}. Retry with invoice_id=inv_1001."

agent = create_deep_agent(
    model=get_gpt_model(disable_tool_streaming=True),
    tools=[lookup_invoice],
    middleware=[ToolErrorMiddleware(recover_tool_error)],
    subagents=[],
)
```

`return None` 很关键：它表示这个异常不是你声明能恢复的错误，应该继续抛出去。艹，别把未知异常都包装成“请重试”，那是在把生产事故藏进聊天记录里。

## 运行命令

```bash
uv run python -m deepagent_src.advanced_teach.04_fault_tolerance
```

这会触发一次真实 LLM 调用，使用项目里的 `get_gpt_model(disable_tool_streaming=True)`。如果没有 `CHATGPT_API_KEY` 或 `CHATGPT_API_URL`，真实调用会失败。

## 预期现象

输出里应该能看到：

```text
AIMessage tool_calls=[lookup_invoice bad-id]
ToolMessage Tool `lookup_invoice` failed: ... Retry with invoice_id=inv_1001.
AIMessage tool_calls=[lookup_invoice inv_1001]
ToolMessage invoice inv_1001 total is 42 USD
AIMessage 教学发票 inv_1001 的总金额是 42 USD。
fault tolerance tool error recovery real call ok
```

这说明第一次工具失败没有直接炸掉整次运行，而是被转成模型可读的错误消息；第二次模型修正参数后，工具正常返回。

## 常见误区

不要把 retry 和 tool error recovery 混为一谈。`ToolRetryMiddleware` 适合网络抖动、超时、限流这类“同样输入再试一次可能成功”的问题；`ToolErrorMiddleware` 适合参数错误、业务校验失败这类“模型看见错误后能换输入”的问题。

也不要捕获所有异常。未知异常应该暴露出来修代码，只有你能明确解释给模型并且模型能修正的错误，才应该转成 `ToolMessage`。

## 生产分层

官方文档把容错分成几类：

| 错误类型 | 应对方式 | 常见机制 |
| --- | --- | --- |
| 临时错误、限流、网络抖动 | 自动重试 | `ModelRetryMiddleware`、`ToolRetryMiddleware` |
| 工具参数错误、可恢复业务错误 | 交给模型修正 | `ToolErrorMiddleware` |
| 用户才能决定的问题 | 暂停等待人类 | `interrupt_on` / HITL |
| Provider 故障 | 切备用模型 | `ModelFallbackMiddleware` |
| 失控循环、过量调用 | 设置上限 | `ModelCallLimitMiddleware`、`ToolCallLimitMiddleware` |
| 未知异常 | 直接抛出 | 不加兜底 middleware |

Deep Agents 本身是 built on LangGraph，所以这些 LangChain agent middleware 可以放进 `create_deep_agent(..., middleware=[...])`；Deep Agents 自己的 HITL 则可以直接用 `interrupt_on={...}`。

## 验证

本章验证点：

1. 第一次工具调用参数是 `bad-id`。
2. `ToolErrorMiddleware` 生成包含 `Retry with invoice_id=inv_1001` 的 `ToolMessage`。
3. 模型第二次调用同一个工具，参数修正为 `inv_1001`。
4. 最终回答包含 `inv_1001` 和 `42 USD`。

官方依据：`/oss/python/deepagents/fault-tolerance` 把 LLM-recoverable errors 定义为转成 error `ToolMessage` 让模型调整；同页还列出 retry、fallback、call limit、HITL 等生产容错策略。
