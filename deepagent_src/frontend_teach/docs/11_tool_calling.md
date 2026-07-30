# 11 Tool Calling

## 它是什么

工具调用不是普通聊天文本。`useToolCalls(stream)` 会用相同的 `callId` 把 `AIMessage.tool_calls` 与 `ToolMessage` 组装成响应式对象，并让它依次呈现 `running`、`finished` 或 `error`。

## 后端协议

本章不用模型决定是否调用工具，而是通过确定性 `StateGraph + ToolNode` 产生真实协议：

```python
AIMessage(tool_calls=[{
    "name": "get_teaching_weather",
    "args": {"city": "上海"},
    "id": f"weather-{uuid4()}",
    "type": "tool_call",
}])
```

`ToolNode` 执行工具并生成具有相同 `tool_call_id` 的 `ToolMessage`。前端 SDK 正是依靠这个 ID 完成配对。

普通 `StateGraph` 还必须在编译时注册工具投影：

```python
graph = builder.compile(transformers=[ToolCallTransformer])
```

`ToolCallTransformer` 会把 `ToolNode` 发出的 `tools` channel 事件投影为前端可消费的生命周期。它不是默认 transformer；只在 state 中存在 `AIMessage/ToolMessage`，`useToolCalls` 不会自行扫描和配对。

## 前端读取

```tsx
const stream = useStream({ apiUrl: API_URL, assistantId: "tool_calling" });
const toolCalls = useToolCalls(stream);

return toolCalls.map((call) => (
  <ToolCallCard key={call.callId} toolCall={call} />
));
```

核心字段：

| 字段 | 含义 |
| --- | --- |
| `name` | 工具名称 |
| `input` / `args` | 结构化调用参数 |
| `output` | 成功结果，运行中或失败时为 `null` |
| `status` | `running`、`finished`、`error` |
| `error` | 工具失败详情 |

同一个调用应使用 `callId` 作为 React key，让卡片原地更新，不能在完成后创建第二张结果卡。
每次新调用的 `callId` 必须唯一；同一调用生命周期内则保持不变。

## 运行

```bash
./deepagent_src/frontend_teach/start.sh
```

打开 `http://127.0.0.1:5173`，进入 `11 Tool Calling` 并提交默认请求。预期右侧出现 `get_teaching_weather` 卡片，先显示 `running`，约 0.6 秒后原地变为 `finished` 并显示上海天气结果。

## 常见误区

- 不要手动扫描所有 messages 配对工具调用；使用 `useToolCalls`。
- 自定义 `StateGraph` 不要漏掉 `ToolCallTransformer`，否则 `useToolCalls` 会保持空数组。
- 不要把 `ToolMessage` 再渲染成普通聊天气泡，否则结果重复。
- 始终处理 `running`、`finished`、`error` 三种状态。
- 专用卡片必须先校验 `output`；未知工具保留紧凑 JSON fallback。

## 下一章

第 12 章学习 Headless Tools：工具逻辑在浏览器执行，Agent 通过 interrupt 等待前端结果。

## 官方资料

- Tool calling: `https://docs.langchain.com/oss/python/langchain/frontend/tool-calling`
