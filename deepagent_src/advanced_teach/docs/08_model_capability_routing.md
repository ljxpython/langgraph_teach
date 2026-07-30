# 第八章：模型能力注册表与运行时模型路由

模型名称不是能力声明。前端可以提交 `model_id`，但服务端必须用受控注册表确认它确实允许使用，并且满足本轮任务的能力要求；不能把任意 provider/model 字符串直接透传给 `init_chat_model`。

本例把已验证的 `gpt-vision-input` 标记为支持 `vision_input`，但故意**不**标记 `vision_tool_result`：第七章的真实探针已经证明，当前 gateway 虽能接收用户图片，却不能正确理解 `read_file` 返回的图片 ToolMessage。

## 最小代码

代码在 `deepagent_src/advanced_teach/08_model_capability_routing.py`。

```python
@wrap_model_call
def select_model(request, handler):
    route = request.runtime.context
    model = resolve_model(route)
    return handler(request.override(model=model.create()))
```

`ModelRoute` 是运行时 context，包含用户选择的受限 `model_id` 和服务端计算出的 `required_capabilities`。`resolve_model` 先检查 model ID 是否在 allowlist，再做能力集合包含判断，最后 middleware 用 `request.override(model=...)` 替换本轮实际调用模型。

## 运行命令

```bash
uv run python -m deepagent_src.advanced_teach.08_model_capability_routing
```

这会做一次真实 `gpt-5.5` 调用。`deepseek-text + vision_input` 的拒绝测试只跑本地集合校验，不调用模型。

## 预期现象

```text
rejected_route: 模型 deepseek-text 不满足能力要求：vision_input
selected_model: gpt-vision-input
final: ROUTER_OK
model capability routing real call ok
```

## 关键边界

1. **能力注册表是应用配置，不是框架自动探测。** 新模型、provider 升级或 gateway 改造后，都要用真实探针更新它。
2. **前端只负责请求。** `required_capabilities` 应由服务端根据任务、文件类型、工具和权限计算；不能信任前端声称“这是纯文本任务”。
3. **模型选择与工具授权分开。** 本章只决定模型；工具、MCP、Skill 的可见性和权限仍由已有 capability middleware 与服务端授权处理。
4. **不做静默降级。** 本例遇到缺失能力直接拒绝。生产环境若允许 fallback，必须记录“从哪个模型降级到哪个模型、缺了什么能力”，并让用户知道结果边界。

## 常见误区

不要把“模型能看用户上传的图片”和“模型能看工具返回的图片”合成一个 `vision=True`。两者是不同的 provider 协议能力，第七章已给出当前 gateway 的真实反例。

官方依据：`/oss/python/deepagents/models` 说明可以通过 runtime context 和 `wrap_model_call` 在每次调用时替换模型，无须重建 Agent；`/oss/python/langchain/middleware/custom` 说明 wrap middleware 在每次模型调用外围执行，并可通过 `request.override(...)` 改写请求。
