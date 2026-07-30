# Deep Agents Frontend 学习路线

## 学习主题

这部分学习 Deep Agents 的 Frontend：真实链路是先用 `langgraph dev` 启动 Agent Server，再让前端通过 `useStream()` 连到 `http://localhost:2024` 发起对话并展示流式状态。前端不是只展示一个聊天气泡，而是把 coordinator、subagent、任务状态、工具进度和 sandbox 产物拆开显示。

## 课程大纲

### 01 概述：真实链路与 useStream 暴露了什么

目标：理解 `langgraph dev -> useStream -> UI` 的链路，以及 `stream.messages`、`stream.subagents`、`stream.values` 分别负责什么。

### 02 Subagent streaming

目标：把 coordinator 的工具调用和 subagent 卡片关联起来，显示委派进度。

### 03 Todo list

目标：从 `stream.values.todos` 渲染任务列表，让用户看到 Agent 计划和执行状态。

### 04 Sandbox

目标：理解文件浏览器、代码视图、diff 面板如何来自 sandbox-backed artifacts。

### 05 Frontend HITL

目标：把 interrupts 显示成审批 UI，并恢复同一次运行。

### 06 Dynamic Tools

目标：由前端选择本轮能力，后端通过 middleware 只向模型暴露经过白名单过滤的工具。

### 07 MCP + Skills Selection

目标：加载真实 MCP stdio tool，并让前端通过受信 ID 选择本轮 MCP 能力和 Skill 工作方法。

### 08 LangGraph Graph Execution

目标：理解原生 `StateGraph` 的命名节点、scoped messages 与 graph state 如何映射到执行 UI。

### 09 Custom Stream Channels

目标：让服务端 transformer 通过独立 channel 推送结构化事件，并用 `useExtension` 与 `useChannel` 分别读取最新值和历史。

### 10 Markdown Messages

目标：安全渲染 AI 消息中的 GFM 标题、列表、表格和代码块，并处理流式更新与内容溢出。

### 11 Tool Calling

目标：使用 `useToolCalls` 把工具请求和结果按 `callId` 组装成具有完整生命周期的调用卡片。

### 12 Headless Tools

目标：让 Agent 通过 interrupt 调用浏览器中的 `localStorage` 工具，并由 `useStream` 自动执行和恢复原运行。

### 13 Human-in-the-loop

目标：用工具内自定义 interrupt 渲染业务审核表单，并持久保留已决卡片。

### 14 Branching Chat

目标：从消息的父 checkpoint 编辑问题或重新生成回答，同时保留原对话路径。

### 15 Reasoning Tokens

目标：区分 reasoning content block 与最终文本，并为推理过程提供可折叠展示。

### 16 Structured Output

目标：校验最终 tool call 参数，并把结构化结果渲染为领域组件。

### 17 Message Queues

目标：当前 run 执行时继续提交消息，使用 SDK 原生 FIFO 队列取消或清空等待项。

### 18 Join & Rejoin

目标：断开客户端而不取消服务端 run，再使用持久化 thread ID 自动重新附着并恢复遗漏输出。

### 19 Time Travel

目标：读取 thread checkpoint 历史、检查完整 graph state，并从可执行 checkpoint 重放后续节点。

### 20 Generative UI

目标：让 Agent 生成受 catalog 约束的 JSON UI spec，并通过 json-render registry 安全渲染组件树。

### 21 Frontend Integrations Overview

目标：比较 AI Elements、assistant-ui、CopilotKit 与 OpenUI 的状态所有权、接入边界和后端成本，并根据场景选择方案。

### 22 Frontend Integration Examples

目标：分别运行四种集成的数据流演示，并掌握每套方案的最小安装、接线代码和迁移风险。

## 真实运行链路

本教程不复用项目根目录的 `langgraph.json`，而是在当前学习目录放独立配置：

```json
{
  "graphs": {
    "frontend_agent": "./deepagent_src/frontend_teach/agent.py:agent",
    "subagent_stream_agent": "./deepagent_src/frontend_teach/agent.py:subagent_stream_agent",
    "todo_agent": "./deepagent_src/frontend_teach/agent.py:todo_agent",
    "sandbox_agent": "./deepagent_src/frontend_teach/agent.py:sandbox_agent",
    "hitl_agent": "./deepagent_src/frontend_teach/agent.py:hitl_agent",
    "dynamic_tools_agent": "./deepagent_src/frontend_teach/agent.py:dynamic_tools_agent",
    "mcp_skills_factory_agent": "./deepagent_src/frontend_teach/agent.py:mcp_skills_factory_agent",
    "mcp_skills_isolated_agent": "./deepagent_src/frontend_teach/agent.py:mcp_skills_isolated_agent",
    "mcp_skills_static_agent": "./deepagent_src/frontend_teach/agent.py:mcp_skills_static_agent",
    "graph_execution": "./deepagent_src/frontend_teach/langgraph_graphs.py:graph_execution",
    "custom_stream_channels": "./deepagent_src/frontend_teach/langgraph_graphs.py:custom_stream_channels",
    "markdown_messages": "./deepagent_src/frontend_teach/langgraph_graphs.py:markdown_messages",
    "tool_calling": "./deepagent_src/frontend_teach/langgraph_graphs.py:tool_calling",
    "headless_tools": "./deepagent_src/frontend_teach/langgraph_graphs.py:headless_tools",
    "custom_hitl": "./deepagent_src/frontend_teach/langgraph_graphs.py:custom_hitl",
    "branching_chat": "./deepagent_src/frontend_teach/langgraph_graphs.py:branching_chat",
    "reasoning_tokens": "./deepagent_src/frontend_teach/langgraph_graphs.py:reasoning_tokens",
    "structured_output": "./deepagent_src/frontend_teach/langgraph_graphs.py:structured_output",
    "time_travel": "./deepagent_src/frontend_teach/langgraph_graphs.py:time_travel",
    "generative_ui": "./deepagent_src/frontend_teach/langgraph_graphs.py:generative_ui"
  }
}
```

所以本地开发时直接运行：

```bash
./deepagent_src/frontend_teach/start.sh
```

停止：

```bash
./deepagent_src/frontend_teach/stop.sh
```

等价的后端命令是：

```bash
uv run langgraph dev --config deepagent_src/frontend_teach/langgraph.json
```

服务默认暴露：

```text
API: http://localhost:2024
assistantId: frontend_agent
assistantId: subagent_stream_agent
assistantId: todo_agent
assistantId: sandbox_agent
assistantId: hitl_agent
assistantId: dynamic_tools_agent
assistantId: mcp_skills_factory_agent
assistantId: mcp_skills_isolated_agent
assistantId: mcp_skills_static_agent
assistantId: graph_execution
assistantId: custom_stream_channels
assistantId: markdown_messages
assistantId: tool_calling
assistantId: headless_tools
assistantId: custom_hitl
assistantId: branching_chat
assistantId: reasoning_tokens
assistantId: structured_output
assistantId: message_queues
assistantId: join_rejoin
assistantId: time_travel
assistantId: generative_ui
```

前端连接的核心代码：

```ts
const stream = useStream({
  apiUrl: "http://localhost:2024",
  assistantId: "frontend_agent",
});
```

用户在前端输入消息后，前端调用 `stream.submit(...)`，LangGraph Server 执行 `frontend_agent`，再把 messages、state、subagents 等流式推回前端。

## 当前学到哪里

已经完成 01 至 22。第 22 章为 CopilotKit、AI Elements、assistant-ui 和 OpenUI 分别提供独立接入骨架与可交互数据流示例。

| 数据 | 前端用途 | 常用程度 |
| --- | --- | --- |
| `stream.messages` | coordinator 对话、最终总结 | 高 |
| `stream.subagents` | specialist worker 状态和任务信息 | 高 |
| `stream.values` | todos、计划、报告片段、sandbox 元数据 | 高 |
| Tool-call state | 工具进度卡片、搜索/文件/浏览器结果 | 中高 |
| Interrupts | 人审、补充输入、暂停恢复 | 中 |

## 官方资料

- Deep Agents Frontend Overview: `https://docs.langchain.com/oss/python/deepagents/frontend/overview`
- React SDK `useStream`: `https://reference.langchain.com/javascript/langchain-react/index/useStream`

## 本目录文件

- `../agent.py`：本教程自己的 Deep Agent 后端
- `../langgraph.json`：本教程自己的 LangGraph dev 配置
- `../web/`：本教程自己的最小 React 前端
- `../01_stream_projection.mjs`：不用浏览器的最小 stream 投影示例，只用于理解数据形状
- `01_overview.md`：第一章讲义
- `02_subagent_streaming.md`：第二章讲义
- `03_todo_list.md`：第三章讲义
- `04_sandbox.md`：第四章讲义
- `05_frontend_hitl.md`：第五章讲义
- `06_dynamic_tools.md`：第六章讲义
- `07_mcp_skills_selection.md`：第七章讲义
- `08_langgraph_graph_execution.md`：第八章讲义
- `09_custom_stream_channels.md`：第九章讲义
- `10_markdown_messages.md`：第十章讲义
- `11_tool_calling.md`：第十一章讲义
- `12_headless_tools.md`：第十二章讲义
- `13_human_in_the_loop.md`：第十三章讲义
- `14_branching_chat.md`：第十四章讲义
- `15_reasoning_tokens.md`：第十五章讲义
- `16_structured_output.md`：第十六章讲义
- `17_message_queues.md`：第十七章讲义
- `18_join_rejoin.md`：第十八章讲义
- `19_time_travel.md`：第十九章讲义
- `20_generative_ui.md`：第二十章讲义
- `21_frontend_integrations.md`：第二十一章讲义
- `22_integration_examples.md`：第二十二章讲义
