# 22 Frontend Integration Examples

## 本章目标

分别看清 CopilotKit、AI Elements、assistant-ui 和 OpenUI 的真实接线。本章为教学对照把四套依赖装在同一入口；每个标签都会调用真实 `gpt-5.5`、执行真实 LangGraph run，并在天气请求中实际调用工具。

## 1. AI Elements

AI Elements 是写进项目的 shadcn/ui 源码组件，不接管 LangGraph 状态。直接遍历 `stream.messages`，按 `HumanMessage`、`AIMessage` 和 tool call 映射组件。

```bash
npm install @langchain/react
npx ai-elements@latest add conversation message prompt-input tool reasoning
```

```tsx
const stream = useStream({ apiUrl: "http://localhost:2024", assistantId: "agent" });

return <Conversation>
  {stream.messages.map((message) =>
    AIMessage.isInstance(message)
      ? <MessageResponse>{message.text}</MessageResponse>
      : <MessageContent>{message.text}</MessageContent>
  )}
  <PromptInput onSubmit={({ text }) =>
    stream.submit({ messages: [{ type: "human", content: text }] })
  } />
</Conversation>;
```

关键点：流式文本用 `MessageResponse`；消息类型用 `isInstance` 判断；组件源码可以直接改。

## 2. assistant-ui

assistant-ui 提供完整 headless thread runtime。`useExternalStoreRuntime` 是边界，必须把 LangChain messages 单向转换成 `ThreadMessageLike[]`，不能再维护第二份可写消息状态。

```bash
npm install @assistant-ui/react @assistant-ui/react-markdown
```

```tsx
const messages = useMemo(() => toThreadMessages(stream.messages), [stream.messages]);
const runtime = useExternalStoreRuntime({
  messages,
  convertMessage: (message) => message,
  onNew: async (message) => stream.submit({
    messages: [{ type: "human", content: textOf(message) }],
  }),
  onCancel: () => stream.stop(),
});

return <AssistantRuntimeProvider runtime={runtime}><Thread /></AssistantRuntimeProvider>;
```

转换函数要覆盖 human、AI、tool、reasoning，并按 `toolCallId` 把 ToolMessage 结果接回对应调用。LangGraph branching 仍需结合 `useMessageMetadata` 和 `forkFrom`。

## 3. CopilotKit

CopilotKit 与前三者最大的区别是需要 AG-UI bridge。前端不能把 `runtimeUrl` 直接指向普通 LangGraph graph REST 地址。

```bash
uv add copilotkit ag-ui-langgraph fastapi uvicorn
npm install @copilotkit/react-core @copilotkit/react-ui @ag-ui/client
```

```python
agent = create_deep_agent(
    model=model,
    middleware=[CopilotKitMiddleware()],
)

add_langgraph_fastapi_endpoint(
    app=app,
    agent=LangGraphAGUIAgent(name="agent", graph=agent),
    path="/api/copilotkit",
)
```

```tsx
const agent = new HttpAgent({
  agentId: "copilotkit_integration",
  url: "http://localhost:2024/api/copilotkit",
});

<CopilotKit selfManagedAgents={{ copilotkit_integration: agent }} agent="copilotkit_integration">
  <CopilotChat />
</CopilotKit>
```

真实职责边界：LangGraph 负责执行，CopilotKit 负责聊天 UI，`HttpAgent` 通过 AG-UI endpoint 驱动真实 run。`selfManagedAgents` 适合这个无密钥的本地教学示例；生产环境应部署与前端版本匹配的 CopilotKit Runtime，并改用 `runtimeUrl`，不要把密钥放进浏览器。

## 4. OpenUI

OpenUI 让模型输出 `openui-lang` 程序，`Renderer` 按受控 library 渲染。它不是 JSON spec；程序以 `root` 为入口，并推荐把 `root` 放在第一行实现 hoisting。

```bash
npm install @langchain/react @openuidev/react-ui @openuidev/react-headless @openuidev/react-lang zustand
```

```tsx
const SYSTEM_PROMPT = openuiLibrary.prompt(openuiPromptOptions);
const stream = useStream({ apiUrl: "http://localhost:2024", assistantId: "openui" });

return <Renderer
  response={lastAiMessage(stream.messages)?.text ?? ""}
  library={openuiLibrary}
  isStreaming={stream.isLoading}
/>;
```

只在新 thread 的第一条提交里注入 system prompt。生产实现还要按完整 statement 稳定渲染，避免每个 token 都重解析，并在 chart 引用完整后才显示图表。

## 运行本章

```bash
./deepagent_src/frontend_teach/start.sh
```

打开 `http://127.0.0.1:5173`，进入 `22 Integration Examples`。依次切换四个标签并发送不同城市：AI Elements、assistant-ui 和 OpenUI 请求 LangGraph API；CopilotKit 请求 `/api/copilotkit` AG-UI endpoint。模型从自然语言提取城市、调用 `get_teaching_weather`，再根据 `ToolMessage` 生成最终回复或 OpenUI DSL；每次提交都会产生真实模型 API 调用和少量费用。

## 对比结论

| 方案 | 最小迁移单位 | 新后端路由 | 最容易丢失的能力 |
| --- | --- | --- | --- |
| AI Elements | 展示组件 | 否 | tool result 关联 |
| assistant-ui | message adapter + runtime | 否 | checkpoint branching 语义 |
| CopilotKit | 前端 runtime + AG-UI bridge | 是 | 原始 LangGraph 自定义状态 |
| OpenUI | prompt + DSL renderer | 否 | 流式半成品的解析稳定性 |

## 常见误区

1. 把 CopilotKit 的 `runtimeUrl` 指向 `http://localhost:2024` 普通 graph API。它需要 AG-UI endpoint。
2. assistant-ui adapter 双向复制消息。`stream.messages` 应保持唯一事实源。
3. AI Elements 只渲染 `message.text`，漏掉 reasoning 和 tool calls。
4. OpenUI 在每个 token 上直接重解析包含 chart 的半成品程序。
5. 生产项目一次安装四套 UI。本章仅为对照教学这样做；正式选型应建立隔离 spike，再按 thread、tool、interrupt、checkpoint 清单验收。

## 官方资料

- `https://docs.langchain.com/oss/python/langchain/frontend/integrations/copilotkit`
- `https://docs.langchain.com/oss/python/langchain/frontend/integrations/ai-elements`
- `https://docs.langchain.com/oss/python/langchain/frontend/integrations/assistant-ui`
- `https://docs.langchain.com/oss/python/langchain/frontend/integrations/openui`
