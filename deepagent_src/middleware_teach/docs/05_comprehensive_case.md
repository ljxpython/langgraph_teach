# 第五章：综合案例

本章把 `wrap_model_call`、`wrap_tool_call` 和 `create_deep_agent` 放到同一条真实流程里。`wrap_model_call` 观察模型层调用，并对临时上游错误做最小重试；`wrap_tool_call` 观察并改写工具结果；Deep Agent 负责真实调用模型并决定工具调用。

## 最小代码

代码在 `deepagent_src/middleware_teach/05_comprehensive_case.py`。

```python
@wrap_model_call
def record_model_call(request, handler):
    model_events.append(f"model_call:{len(request.state['messages'])}")
    for attempt in range(3):
        try:
            return handler(request)
        except Exception:
            if attempt == 2:
                raise

@wrap_tool_call
def audit_invoice_tool(request, handler):
    result = handler(request)
    return ToolMessage(
        content=f"AUDITED_TOOL:{result.content}",
        tool_call_id=request.tool_call["id"],
        name=request.tool_call["name"],
    )
```

模型层 middleware 不碰工具结果，只记录每次模型调用，并在模型服务临时不可用时重试同一个请求。工具层 middleware 不决定模型是否调用工具，只包住已经发生的工具执行。

## 运行命令

```bash
uv run python -m deepagent_src.middleware_teach.05_comprehensive_case
```

## 预期现象

输出类似：

```text
model_events: ['model_call:1', 'model_call:3']
tool_events: ["before:lookup_invoice:{'invoice_id': 'mw-5001'}", 'after:invoice mw-5001 total is 88 USD']
tool_message: AUDITED_TOOL:invoice mw-5001 total is 88 USD
final: MIDDLEWARE_CASE_OK: AUDITED_TOOL:invoice mw-5001 total is 88 USD
middleware comprehensive real call ok
```

这里有两次模型调用：第一次模型决定调用工具，工具结果进入历史后，第二次模型生成最终回答。`wrap_tool_call` 只在工具节点执行时触发一次。

## 常见误区

不要把 middleware 当成万能业务框架。模型选择、工具审计、错误恢复、HITL 都能放 middleware，但每层只干自己的事：模型层管模型请求，工具层管工具执行，权限边界还要落在后端服务和工具实现里。艹，把所有逻辑塞进一个 middleware，就是换个地方写屎山。

## 五章串起来

1. `before_model` / `after_model`：看模型调用前后状态。
2. `wrap_model_call`：包住模型调用，可重试、fallback、短路或替换模型。
3. `wrap_tool_call`：包住工具执行，可审计、脱敏、错误转译。
4. Deep Agents 默认栈：理解你的 middleware 插在 Deep Agents harness 的哪个位置。
5. 综合案例：真实 Deep Agent 中同时使用模型层和工具层 middleware。

本章触发真实 `gpt-5.5` Deep Agent 调用，会产生最小模型调用成本。没有使用 mock、fake model 或内部函数冒充 Agent 运行。

本地验证时 `gpt-5.5` 曾连续返回上游 `503 Service temporarily unavailable`，所以示例在 `wrap_model_call` 里保留 3 次最小重试。生产环境不要裸捕全部异常，应按 provider 错误类型、重试预算和审计策略收窄。
