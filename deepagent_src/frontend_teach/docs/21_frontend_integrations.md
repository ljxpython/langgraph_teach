# 21 Frontend Integrations Overview

## 本章目标

学会在 `AI Elements`、`assistant-ui`、`CopilotKit`、`OpenUI` 与自定义 UI 之间做选择。这里没有新 Agent 协议：`useStream` 本身是 UI-agnostic data layer，它把 messages、tool calls、loading、values、thread metadata 等普通响应式状态交给任意组件系统。

## 四种方案怎么选

| 方案 | 核心定位 | 与 `useStream` 的关系 | 后端成本 |
| --- | --- | --- | --- |
| AI Elements | 基于 shadcn/ui 的可组合聊天组件 | 直接渲染 `stream.messages` 等状态 | 通常不变 |
| assistant-ui | Headless React 聊天 runtime | 用 `useExternalStoreRuntime` 一类 adapter 桥接 | 通常不变 |
| CopilotKit | 完整 Copilot runtime、AG-UI、共享状态和生成式 UI | 由 CopilotKit runtime 连接 Agent | 需要自定义 `/api/copilotkit` bridge |
| OpenUI | 声明式 Dashboard、Report 和数据界面 DSL | 消费消息或 subagent 结果 | 通常不变 |

选择规则很直接：

1. 保留 `useStream` 控制权并想要 shadcn 组件，选 AI Elements。
2. 需要成熟的 headless 聊天 runtime，选 assistant-ui。
3. 需要应用级 Copilot、AG-UI 或跨前后端共享状态，选 CopilotKit。
4. 重点是模型生成 Dashboard / Report，选 OpenUI。

不要仅仅为了换一套聊天气泡，就安装完整 runtime。那会同时引入第二套 thread、message 和 tool-call 状态所有权，艹，最后调试时根本分不清谁在管谁。

## 当前项目为什么继续自定义 UI

本课程已经直接使用 `@langchain/react` 实现 Sandbox 文件同步、HITL、Branching、Message Queue、Join/Rejoin、Time Travel、Custom Channels 和 Generative UI。这些界面依赖 LangGraph 的 checkpoint、interrupt 和自定义 state。继续使用 `useStream + 自定义 UI` 改动最小，状态所有权也最清楚。

第 21 章因此只增加纯前端选型页，不修改 `langgraph.json`，也不注册 `frontend_integrations` assistant。

## 最小选型逻辑

```ts
function recommendedIntegration(scenario: Scenario) {
  if (scenario === "dashboard") return "openui";
  if (scenario === "copilot") return "copilotkit";
  if (scenario === "full-runtime") return "assistant-ui";
  return "ai-elements";
}
```

运行：

```bash
./deepagent_src/frontend_teach/start.sh
```

打开 `http://127.0.0.1:5173`，进入 `21 Integrations`，切换四个目标。预期推荐依次对应 AI Elements、assistant-ui、CopilotKit 和 OpenUI；本页不会发送模型请求。

## 真正迁移前要检查什么

- Thread ownership：谁创建、持久化和切换 thread。
- Message normalization：LangChain message/content block 是否被 runtime 无损转换。
- Tool rendering：并行 tool call、结果关联和错误状态是否保留。
- HITL：interrupt 的展示、决策提交和 run 恢复由谁负责。
- Checkpoint：branching、time travel、join/rejoin 能否继续工作。
- Custom state：`stream.values`、custom channels 和 subagent 是否有接入口。

任何一项答不清楚，都别急着迁移。先做独立 spike，证明关键链路能走通。

## 常见误区

1. 把组件库当协议层。AI Elements 主要解决显示组件，不接管 LangGraph。
2. 同时维护两套消息状态。Adapter 应有唯一数据源，不能来回同步副本。
3. 认为四种集成都需要改后端。明显需要自定义 endpoint/AG-UI bridge 的是 CopilotKit。
4. 一次安装四套库做横评。依赖冲突和 CSS 污染会掩盖真实接入成本。

下一步适合做第 22 章 **Frontend Integration Spike**：只选一个候选方案，在隔离页面完成最小接入并验证 thread、tool call 和 interrupt。

## 官方资料

- Integrations overview: `https://docs.langchain.com/oss/python/langchain/frontend/integrations/overview`
- CopilotKit: `https://docs.langchain.com/oss/python/langchain/frontend/integrations/copilotkit`
- AI Elements: `https://docs.langchain.com/oss/python/langchain/frontend/integrations/ai-elements`
- assistant-ui: `https://docs.langchain.com/oss/python/langchain/frontend/integrations/assistant-ui`
- OpenUI: `https://docs.langchain.com/oss/python/langchain/frontend/integrations/openui`
