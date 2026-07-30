# 第三章：`wrap_tool_call`

`wrap_tool_call` 是包住工具执行的 middleware：它拿到模型发出的 tool call，调用 `handler(request)` 后工具才会真正执行。它解决的是工具层控制问题，例如审计、重试、错误转译、结果改写和敏感信息过滤。

## 最小代码

代码在 `deepagent_src/middleware_teach/03_wrap_tool_call.py`。

```python
@wrap_tool_call
def audit_tool_call(request, handler):
    tool_events.append(f"before:{request.tool_call['name']}")
    result = handler(request)
    tool_events.append(f"after:{result.content}")
    return ToolMessage(
        content=f"AUDITED:{result.content}",
        tool_call_id=request.tool_call["id"],
        name=request.tool_call["name"],
    )
```

`handler(request)` 是工具真正执行的位置；不调用它，就不会调用工具。示例先让模型发出 `add_one(value=2)`，工具返回 `3`，middleware 再把工具消息改成 `AUDITED:3`。

## 运行命令

```bash
uv run python -m deepagent_src.middleware_teach.03_wrap_tool_call
```

## 预期现象

```text
tool_events: ["before:add_one:{'value': 2}", 'after:3']
tool_message: AUDITED:3
final: TOOL_DONE
wrap_tool_call local check ok
```

这说明工具节点真的执行了：`before` 记录模型请求的工具名和参数，`after` 记录原始工具结果，最终进入对话历史的是被 middleware 改写后的 `ToolMessage`。

## 常见误区

`wrap_tool_call` 管的是工具执行，不管模型是否会选择工具。模型要不要发 tool call，是模型层和 prompt/tool schema 的问题；工具一旦被选中，才进入 `wrap_tool_call`。艹，别指望它替你解决“模型不调用工具”的问题。

## 和内置 middleware 的关系

`ToolRetryMiddleware` 和 `ToolErrorMiddleware` 本质上也工作在工具层。区别是：前者负责失败后重试，后者负责把异常转换成模型可见的工具错误消息。自定义 `wrap_tool_call` 更适合做审计、权限检查、结果脱敏这类业务逻辑。

## 为什么用了 `ToolCallingFakeModel`

当前 `FakeMessagesListChatModel` 不实现 `bind_tools()`，直接挂工具会报 `NotImplementedError`。示例里的 `ToolCallingFakeModel` 只是给本地教学模型补一个最小 `bind_tools()`，让 LangChain agent loop 能走到工具节点；真实 OpenAI/Anthropic/DeepSeek 等工具调用模型不需要这层补丁。
