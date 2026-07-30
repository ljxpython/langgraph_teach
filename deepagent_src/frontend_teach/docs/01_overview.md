# 01 概述：真实链路与 useStream 暴露了什么

## 它是什么

真实 Deep Agents 前端链路是：`langgraph dev` 启动 Agent Server，前端用 `useStream()` 连接这个服务，用户在前端发消息后实时展示后端流回来的状态。它解决的问题是：用户不能只看到一个黑盒回答，还要看到主 Agent 怎么分解任务、哪个 subagent 在干活、任务列表推进到哪了。概述阶段先抓后端地址、assistantId，以及三个核心投影：`messages`、`subagents`、`values`。

## 最小真实链路

后端：

```bash
./deepagent_src/frontend_teach/start.sh
```

当前教程自己的 `langgraph.json` 里 assistantId 是 `frontend_agent`：

```json
{
  "graphs": {
    "frontend_agent": "./deepagent_src/frontend_teach/agent.py:agent"
  }
}
```

前端 React 入口长这样：

```ts
import { useStream } from "@langchain/react";

function App() {
  const stream = useStream<typeof agent>({
    apiUrl: "http://localhost:2024",
    assistantId: "frontend_agent",
  });

  const coordinatorMessages = stream.messages;
  const subagents = [...stream.subagents.values()];
  const todos = stream.values?.todos ?? [];
}
```

真实 UI 里，用户输入时通常调用：

```ts
stream.submit({
  messages: [{ type: "human", content: "你好" }],
});
```

## 本章离线练习

`01_stream_projection.mjs` 不会连接 `langgraph dev`，只模拟 `useStream` 返回后的数据形状，帮你先看懂 UI 应该渲染什么：

```bash
node deepagent_src/frontend_teach/01_stream_projection.mjs
```

## 预期现象

终端会输出一个 UI 可直接消费的投影：

```json
{
  "coordinatorMessages": ["研究 Deep Agents 前端概述", "我会委派 researcher 收集资料。"],
  "visibleSubagents": [{ "name": "researcher", "status": "running" }],
  "todos": [{ "text": "理解 useStream", "status": "done" }]
}
```

脚本末尾有 `assert`，如果 subagent 关联或 todos 投影坏了会直接报错。

## 本章真实前端

本教程也放了一个最小 React 前端：

```bash
./deepagent_src/frontend_teach/start.sh
```

然后打开：

```text
http://127.0.0.1:5173
```

这个页面会连接 `http://localhost:2024` 的 `frontend_agent`，展示 coordinator messages、subagents 和 values。

停止：

```bash
./deepagent_src/frontend_teach/stop.sh
```

## 常见误区

不要把离线投影示例当成完整前端。完整体验必须有 `langgraph dev` 后端、前端 `useStream` 连接、用户通过 `stream.submit` 发起对话；离线脚本只是为了先理解 `messages/subagents/values` 怎么投影成 UI。
