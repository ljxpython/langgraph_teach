# 第二章：`wrap_model_call`

`wrap_model_call` 是包住模型调用的 middleware：你可以选择调用 `handler(request)`，也可以不调用它直接返回。它解决的是模型层控制问题，比如改模型请求、统计调用、fallback、缓存命中、短路返回。

## 最小代码

代码在 `deepagent_src/middleware_teach/02_wrap_model_call.py`。

```python
@wrap_model_call
def guard_and_rewrite_model(request, handler):
    user_text = request.state["messages"][-1].text
    if "skip-model" in user_text:
        return ModelResponse(result=[AIMessage(content="SHORT_CIRCUIT_OK")])

    response = handler(request)
    model_text = response.result[0].text
    return ModelResponse(result=[AIMessage(content=f"WRAPPED:{model_text}")])
```

正常路径会调用 `handler(request)`，所以模型真的执行；短路路径直接返回 `ModelResponse`，所以模型不会执行。

## 运行命令

```bash
uv run python -m deepagent_src.middleware_teach.02_wrap_model_call
```

## 预期现象

```text
normal: WRAPPED:MODEL_OK
skipped: SHORT_CIRCUIT_OK
handler_calls: 1
wrap_model_call local check ok
```

`handler_calls` 是 1，说明两次 agent 调用里只有正常路径真正进了模型；`skip-model` 路径被 middleware 短路了。

## 常见误区

`wrap_model_call` 不是 `before_model` 的增强版。`before_model` 返回状态更新；`wrap_model_call` 返回模型响应，可以决定是否调用模型。艹，这两个搞混，代码就会一会儿像 LangGraph state update，一会儿像模型 response，迟早炸。

## 和 Deep Agents 的关系

Deep Agents 的动态模型路由、provider fallback、部分安全策略都适合放在 `wrap_model_call` 这一层，因为它刚好包住“模型将要被调用”的瞬间。前面学过的 `08_model_capability_routing.py` 就是同一机制：读取 `request.runtime.context`，再通过 `request.override(model=...)` 替换本轮使用的模型。
