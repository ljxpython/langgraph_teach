# 02 Subagent streaming：把专家子代理单独展示

## 它是什么

Subagent streaming 是把 coordinator 的对话和 specialist subagent 的输出分开渲染。它解决的问题是：长任务里主 Agent 只负责规划和汇总，真正干活的 researcher、analyst、writer 需要各自有进度卡片。前端不要从一堆混在一起的 token 里猜来源，而是用 `stream.subagents` 发现子代理，再用 selector 读取这个子代理自己的消息。

## 最小真实链路

后端这章多注册了一个图：

```json
{
  "graphs": {
    "frontend_agent": "./deepagent_src/frontend_teach/agent.py:agent",
    "subagent_stream_agent": "./deepagent_src/frontend_teach/agent.py:subagent_stream_agent"
  }
}
```

启动：

```bash
./deepagent_src/frontend_teach/start.sh
```

打开前端：

```text
http://127.0.0.1:5173
```

切到 `02 Subagent streaming`，发送默认问题。这个 tab 会连接：

```ts
const stream = useStream({
  apiUrl: "http://localhost:2024",
  assistantId: "subagent_stream_agent",
});
```

## 前端核心代码

`stream.messages` 只放 coordinator 的主对话：

```tsx
{stream.messages.map((message) => (
  <article key={message.id}>{textOf(message)}</article>
))}
```

`stream.subagents` 只放子代理发现快照，不直接带完整消息：

```tsx
const subagents = [...stream.subagents.values()];
```

要读某个子代理自己的输出，把快照传给 selector：

```tsx
function SubagentCard({ stream, subagent }) {
  const messages = useMessages(stream, subagent);
  const toolCalls = useToolCalls(stream, subagent);

  return (
    <article>
      <button type="button">{subagent.name}</button>
      <p>scoped messages: {messages.length}</p>
      <p>tool calls: {toolCalls.length}</p>
    </article>
  );
}
```

这就是官方文档说的 selector-based subagent streams：根 stream 保持干净，子代理卡片按需订阅自己的 namespace。

## 预期现象

页面左侧 `Coordinator` 会显示用户输入、主 Agent 汇总，以及 root `task` 工具调用卡片。右侧 `Subagents` 会出现 `frontend_researcher` 卡片，卡片里能看到 scoped messages 和子代理自己的 `frontend_note` 工具调用。

本章的真实 SDK 验证命令：

```bash
uv run python - <<'PY'
from langgraph_sdk import get_sync_client

client = get_sync_client(url="http://127.0.0.1:2024")
events = 0
saw_frontend_note = False
for chunk in client.runs.stream(
    None,
    "subagent_stream_agent",
    input={"messages": [{"role": "human", "content": "请用 subagent streaming 的方式解释 stream.subagents 和 useMessages(stream, subagent)"}]},
    stream_mode=["messages-tuple", "updates"],
    stream_subgraphs=True,
):
    events += 1
    text = str(chunk.data)
    if "frontend_note" in text:
        saw_frontend_note = True
print("events", events)
print("saw_frontend_note", saw_frontend_note)
PY
```

当前验证结果：能看到 root `task` 和 subagent `frontend_note`，并且没有再出现 `Error:  is not a valid tool`。

## 常见误区

不要以为 `stream.subagents` 里就有所有子代理消息。它只是发现快照，告诉 UI “有一个子代理、叫什么、状态是什么、namespace 在哪里”；真正的消息和工具调用要用 `useMessages(stream, subagent)`、`useToolCalls(stream, subagent)` 读取。

根消息区只渲染 `HumanMessage` 和 `AIMessage`。`ToolMessage` 已经由工具卡片表达，再当普通消息渲染会重复展示整段原始结果；同理，root 工具区只保留协调器的 `task`，`frontend_note` 留在对应 subagent 卡片中。

之前那个空工具名错误，是因为让概述图强行触发 DeepAgent 内置 `task` 工具后，流式工具调用 chunk 在当前依赖组合下会让前端看到空 tool name。现在概述图保持无工具、第二章图单独演示 subagent，并给模型设置了 `disable_streaming="tool_calling"`，避免这个教学例子被工具名流式增量干扰。

当前环境里如果去掉 `disable_streaming="tool_calling"`，真实 stream 会复现空工具名：

```text
AIMessageChunk.tool_call_chunks: [{"name": "", "args": "{\"", ...}]
```

官方文档里的正常形态是首个 chunk 有工具名、后续参数 chunk 的 name 可以为空值；但当前 provider 返回的是空字符串，前端 SDK 会把它当非法工具名。所以本章页面展示的是实时运行状态、subagent discovery、tool call 卡片和 scoped messages；工具调用参数本身不做 token 级增量流式展示。

## 官方资料

- Deep Agents Subagent streaming: `https://docs.langchain.com/oss/python/deepagents/frontend/subagent-streaming`
- Deep Agents Frontend overview: `https://docs.langchain.com/oss/python/deepagents/frontend/overview`
