import React, { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { tool } from "langchain";
import * as z from "zod";
import { defineCatalog, type Spec } from "@json-render/core";
import { defineRegistry, JSONUIProvider, Renderer } from "@json-render/react";
import { schema as jsonRenderSchema } from "@json-render/react/schema";
import {
  AssistantRuntimeProvider,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  type ThreadMessageLike,
  useExternalStoreRuntime,
} from "@assistant-ui/react";
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { HttpAgent } from "@ag-ui/client";
import { Renderer as OpenUIRenderer } from "@openuidev/react-lang";
import { openuiLibrary } from "@openuidev/react-ui/genui-lib";
import {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import { Message, MessageContent, MessageResponse } from "@/components/ai-elements/message";
import { Tool, ToolContent, ToolHeader, ToolInput, ToolOutput } from "@/components/ai-elements/tool";
import {
  type AnyStream,
  type AnyHeadlessToolImplementation,
  type SubagentDiscoverySnapshot,
  handleHeadlessToolInterrupt,
  parseHeadlessToolInterruptPayload,
  useMessages,
  useMessageMetadata,
  useSubmissionQueue,
  useChannel,
  useExtension,
  useStream,
  useToolCalls,
} from "@langchain/react";
import "@copilotkit/react-ui/styles.css";
import "@openuidev/react-ui/index.css";
import "./shadcn.css";
import "./styles.css";

const API_URL = "http://localhost:2024";
const COPILOTKIT_AGENT = new HttpAgent({
  agentId: "copilotkit_integration",
  description: "真实 LLM 天气工具教学 Agent",
  url: `${API_URL}/api/copilotkit`,
});

const ASSISTANTS = {
  frontend_agent: {
    label: "01 Overview",
    prompt: "请解释 stream.messages、stream.subagents 和 stream.values",
  },
  subagent_stream_agent: {
    label: "02 Subagent streaming",
    prompt: "请用 subagent streaming 的方式解释 stream.subagents 和 useMessages(stream, subagent)",
  },
  todo_agent: {
    label: "03 Todo list",
    prompt: "请分三步解释 stream.values.todos 如何驱动前端实时任务列表",
  },
  sandbox_agent: {
    label: "04 Sandbox",
    prompt: "请把 greeting 改成友好的中文问候，并记录到 CHANGELOG.md",
  },
  hitl_agent: {
    label: "05 Frontend HITL",
    prompt: "请向 #release 频道发送“Frontend HITL 教学已上线”",
  },
  dynamic_tools_agent: {
    label: "06 Dynamic Tools",
    prompt: "请查询上海天气，并计算单价 79.9 元的商品购买 3 件需要多少钱",
  },
  mcp_skills_agent: {
    label: "07 MCP + Skills",
    prompt: "请查询 USD/CNY 教学汇率，并按选中的 skill 简短解释结果",
  },
  graph_execution: {
    label: "08 Graph Execution",
    prompt: "分析前端图执行",
  },
  custom_stream_channels: {
    label: "09 Custom Channels",
    prompt: "分析前端图执行",
  },
  markdown_messages: {
    label: "10 Markdown Messages",
    prompt: "展示 Markdown 消息",
  },
  tool_calling: {
    label: "11 Tool Calling",
    prompt: "查询上海天气",
  },
  headless_tools: {
    label: "12 Headless Tools",
    prompt: "Headless Tools 已在浏览器执行",
  },
  custom_hitl: {
    label: "13 Human-in-the-loop",
    prompt: "商品与描述不符，申请退款",
  },
  branching_chat: {
    label: "14 Branching Chat",
    prompt: "解释 LangGraph checkpoint",
  },
  reasoning_tokens: {
    label: "15 Reasoning Tokens",
    prompt: "解释 reasoning tokens 如何在前端展示",
  },
  structured_output: {
    label: "16 Structured Output",
    prompt: "学习 LangChain 前端结构化输出",
  },
  message_queues: {
    label: "17 Message Queues",
    prompt: "排队任务 1",
  },
  join_rejoin: {
    label: "18 Join & Rejoin",
    prompt: "离开页面后继续完成分析",
  },
  time_travel: {
    label: "19 Time Travel",
    prompt: "检查并重放 checkpoint",
  },
  generative_ui: {
    label: "20 Generative UI",
    prompt: "生成 Agent 运行仪表盘",
  },
  frontend_integrations: {
    label: "21 Integrations",
    prompt: "选择前端集成方案",
  },
  integration_examples: {
    label: "22 Integration Examples",
    prompt: "比较四种前端集成代码",
  },
};

const INTEGRATION_SCENARIOS = [
  { id: "keep-control", label: "保留 useStream 控制权", detail: "组合可编辑的 shadcn/ui 聊天组件" },
  { id: "full-runtime", label: "需要完整聊天 Runtime", detail: "线程、消息与交互组件由 headless runtime 管理" },
  { id: "copilot", label: "嵌入应用级 Copilot", detail: "需要 AG-UI、共享状态与结构化生成式 UI" },
  { id: "dashboard", label: "生成 Dashboard / Report", detail: "让模型输出声明式数据界面" },
] as const;

type IntegrationScenario = typeof INTEGRATION_SCENARIOS[number]["id"];
type IntegrationId = "ai-elements" | "assistant-ui" | "copilotkit" | "openui";

const INTEGRATIONS: { id: IntegrationId; name: string; position: string; connection: string; backend: string }[] = [
  { id: "ai-elements", name: "AI Elements", position: "shadcn/ui 可组合聊天组件", connection: "直接消费 useStream 状态", backend: "沿用 LangGraph API" },
  { id: "assistant-ui", name: "assistant-ui", position: "Headless React 聊天 runtime", connection: "通过 external store adapter 桥接", backend: "沿用 LangGraph API" },
  { id: "copilotkit", name: "CopilotKit", position: "应用内 Copilot 与 AG-UI runtime", connection: "CopilotKit runtime 连接 Agent", backend: "新增 /api/copilotkit bridge" },
  { id: "openui", name: "OpenUI", position: "声明式 Dashboard / Report DSL", connection: "消费消息或 subagent 输出", backend: "通常沿用 LangGraph API" },
];

function recommendedIntegration(scenario: IntegrationScenario): IntegrationId {
  if (scenario === "dashboard") return "openui";
  if (scenario === "copilot") return "copilotkit";
  if (scenario === "full-runtime") return "assistant-ui";
  return "ai-elements";
}

const DYNAMIC_TOOL_OPTIONS = [
  { name: "lookup_weather", label: "Weather", description: "城市天气查询" },
  { name: "calculate_total", label: "Calculator", description: "商品总价计算" },
] as const;

const MCP_TOOL_OPTIONS = [
  { id: "teaching_lookup_exchange_rate", label: "Exchange rate", description: "MCP 汇率工具" },
] as const;

const SKILL_OPTIONS = [
  { id: "currency-guide", label: "Currency guide", description: "汇率结果教学格式" },
] as const;

type Todo = {
  content: string;
  status: "pending" | "in_progress" | "completed";
};

type FileEntry = {
  name: string;
  path: string;
  type: "file" | "directory";
  size: number;
};

type HitlAction = {
  name: string;
  args: Record<string, unknown>;
  description?: string;
};

type HitlRequest = {
  action_requests: HitlAction[];
  review_configs: { allowed_decisions: ("approve" | "edit" | "reject")[] }[];
};

type ReviewDecision = {
  approved: boolean;
  values?: { amount: number; note: string };
};

type RefundReviewCard = {
  form_type: "refund_approval";
  title: string;
  context: { order_id: string; amount: number; reason: string };
  fields: { name: string; label: string; type: string }[];
  resolved?: boolean;
  decision?: ReviewDecision;
};

const LearningPlanSchema = z.object({
  topic: z.string().min(1),
  level: z.enum(["beginner", "intermediate", "advanced"]),
  objectives: z.array(z.string().min(1)).min(1),
  lessons: z.array(z.object({
    title: z.string().min(1),
    duration_minutes: z.number().int().positive(),
  })).min(1),
  total_minutes: z.number().int().positive(),
});

type LearningPlan = z.infer<typeof LearningPlanSchema>;

const generativeCatalog = defineCatalog(jsonRenderSchema, {
  components: {
    Card: {
      description: "带标题和说明的内容容器",
      props: z.object({ title: z.string(), description: z.string().optional() }),
    },
    Stack: {
      description: "水平或垂直排列子组件",
      props: z.object({ direction: z.enum(["horizontal", "vertical"]) }),
    },
    Metric: {
      description: "展示一个指标名称和值",
      props: z.object({ label: z.string(), value: z.string() }),
    },
    List: {
      description: "展示带标题的文本列表",
      props: z.object({ title: z.string(), items: z.array(z.string()) }),
    },
  },
  actions: {},
});

const { registry: generativeRegistry } = defineRegistry(generativeCatalog, {
  components: {
    Card: ({ props, children }) => (
      <section className="generatedCard">
        <header><h2>{props.title}</h2>{props.description && <p>{props.description}</p>}</header>
        {children}
      </section>
    ),
    Stack: ({ props, children }) => <div className={`generatedStack ${props.direction}`}>{children}</div>,
    Metric: ({ props }) => <article className="generatedMetric"><span>{props.label}</span><strong>{props.value}</strong></article>,
    List: ({ props }) => <section className="generatedList"><h3>{props.title}</h3><ol>{props.items.map((item) => <li key={item}>{item}</li>)}</ol></section>,
  },
});

const SANDBOX_THREAD_KEY = "deepagent-sandbox-thread-id";
const HITL_THREAD_KEY = "deepagent-hitl-thread-id";
const CUSTOM_HITL_THREAD_KEY = "langchain-custom-hitl-thread-id";
const BRANCHING_THREAD_KEY = "langchain-branching-thread-id";
const JOIN_REJOIN_THREAD_KEY = "langchain-join-rejoin-thread-id";
const TIME_TRAVEL_THREAD_KEY = "langchain-time-travel-thread-id";
const FILE_MUTATING_TOOLS = new Set(["write_file", "edit_file"]);

function textOf(message: any) {
  if (typeof message.text === "string") return message.text;
  if (typeof message.content === "string") return message.content;
  if (Array.isArray(message.content)) {
    return message.content
      .map((block: any) => block?.text ?? block?.content ?? "")
      .filter(Boolean)
      .join("");
  }
  return JSON.stringify(message.content ?? message, null, 2);
}

function messageType(message: any) {
  return message.type ?? message._getType?.() ?? message.constructor?.name ?? "message";
}

function isConversationMessage(message: any) {
  return ["human", "ai", "HumanMessage", "AIMessage"].includes(messageType(message));
}

function pretty(value: unknown) {
  if (value == null || value === "") return "";
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2);
}

function toolName(toolCall: any) {
  const name = toolCall.name ?? toolCall.tool_name ?? toolCall.function?.name;
  if (name) return name;
  const args = toolArgs(toolCall);
  const output = toolResult(toolCall);
  if (args?.topic || String(output ?? "").startsWith("已记录前端观察点")) {
    return "frontend_note";
  }
  return "tool";
}

function toolArgs(toolCall: any) {
  return toolCall.args ?? toolCall.input ?? toolCall.arguments ?? toolCall.function?.arguments;
}

function toolResult(toolCall: any) {
  return toolCall.output ?? toolCall.result ?? toolCall.response ?? toolCall.error;
}

function ToolCallCard({ toolCall }: { toolCall: any }) {
  const args = pretty(toolArgs(toolCall));
  const result = pretty(toolResult(toolCall));
  const status = toolCall.status ?? (result ? "finished" : "running");
  const badgeClass = status === "finished" || status === "complete" ? "done" : status;

  return (
    <article className="toolCard">
      <div className="toolHead">
        <span>{toolName(toolCall)}</span>
        <span className={`badge ${badgeClass}`}>{status}</span>
      </div>
      {args && <pre className="toolBody">{args}</pre>}
      {result && <pre className="toolResult">{result}</pre>}
    </article>
  );
}

function ToolCallingPage() {
  const [input, setInput] = useState(ASSISTANTS.tool_calling.prompt);
  const stream = useStream<any>({ apiUrl: API_URL, assistantId: "tool_calling" });
  const toolCalls = useToolCalls(stream);

  function submit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content) return;
    stream.submit({ messages: [{ type: "human", content }] });
    setInput("");
  }

  return (
    <section className="layout toolCallingLayout">
      <section className="panel">
        <div className="panelTitle"><h2>Conversation</h2><span className={`live ${stream.isLoading ? "on" : ""}`}>{stream.isLoading ? "streaming" : "idle"}</span></div>
        <div className="messages">
          {(stream.messages ?? []).filter(isConversationMessage).map((message: any, index: number) => <MessageBubble message={message} key={message.id ?? index} />)}
          {stream.error ? <pre className="errorBox">{pretty(stream.error)}</pre> : null}
        </div>
        <form className="composer" onSubmit={submit}>
          <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="输入需要工具处理的问题" />
          <button type="submit" disabled={stream.isLoading}>发送</button>
        </form>
      </section>
      <aside className="panel toolCallingPanel">
        <div className="panelTitle"><h2>Tool calls</h2><span className="count">{toolCalls.length}</span></div>
        <div className="toolList">
          {toolCalls.length ? toolCalls.map((toolCall: any) => <ToolCallCard key={toolCall.callId} toolCall={toolCall} />) : <p className="empty">等待 AIMessage.tool_calls</p>}
        </div>
      </aside>
    </section>
  );
}

const BROWSER_MEMORY_KEY = "headless:lesson-12";
const browserMemoryPut = tool({
  name: "browser_memory_put",
  description: "Store a teaching value in browser localStorage.",
  schema: z.object({ key: z.string(), value: z.string() }),
}).implement(async ({ key, value }) => {
  localStorage.setItem(`headless:${key}`, value);
  return { success: true, key, value };
});

function HeadlessToolsPage() {
  const [input, setInput] = useState(ASSISTANTS.headless_tools.prompt);
  const [phase, setPhase] = useState("idle");
  const [browserValue, setBrowserValue] = useState(() => localStorage.getItem(BROWSER_MEMORY_KEY) ?? "");
  const handledInterrupts = useRef(new Set<string>());
  const onTool = useCallback((event: { phase: string }) => {
    setPhase(event.phase);
    if (event.phase === "success") {
      setBrowserValue(localStorage.getItem(BROWSER_MEMORY_KEY) ?? "");
    }
  }, []);
  const stream = useStream<any>({
    apiUrl: API_URL,
    assistantId: "headless_tools",
  });
  const toolCalls = useToolCalls(stream);

  useEffect(() => {
    const pending = stream.getThread()?.interrupts.find(
      (entry) => !handledInterrupts.current.has(entry.interruptId)
        && parseHeadlessToolInterruptPayload(entry.payload),
    );
    if (!pending) return;
    const payload = parseHeadlessToolInterruptPayload(pending.payload);
    if (!payload) return;
    handledInterrupts.current.add(pending.interruptId);
    void handleHeadlessToolInterrupt(
      payload,
      [browserMemoryPut as AnyHeadlessToolImplementation],
      onTool,
    )
      .then((result) => stream.respond(
        result.toolCallId ? { [result.toolCallId]: result.value } : result.value,
        { interruptId: pending.interruptId, namespace: pending.namespace },
      ))
      .catch(() => setPhase("error"));
  }, [stream, stream.values, onTool]);

  function submit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content) return;
    setPhase("waiting");
    stream.submit({ messages: [{ type: "human", content }] });
    setInput("");
  }

  return (
    <section className="layout headlessToolsLayout">
      <section className="panel">
        <div className="panelTitle"><h2>Conversation</h2><span className={`live ${stream.isLoading ? "on" : ""}`}>{stream.isLoading ? "streaming" : "idle"}</span></div>
        <div className="messages">
          {(stream.messages ?? []).filter(isConversationMessage).map((message: any, index: number) => <MessageBubble message={message} key={message.id ?? index} />)}
          {stream.error ? <pre className="errorBox">{pretty(stream.error)}</pre> : null}
        </div>
        <form className="composer" onSubmit={submit}>
          <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="输入要写入浏览器的内容" />
          <button type="submit" disabled={stream.isLoading}>发送</button>
        </form>
      </section>
      <aside className="side">
        <section className="panel browserMemoryPanel">
          <div className="panelTitle"><h2>Browser localStorage</h2><span className={`badge ${phase === "success" ? "done" : phase}`}>{phase}</span></div>
          <dl>
            <dt>key</dt><dd>{BROWSER_MEMORY_KEY}</dd>
            <dt>value</dt><dd data-testid="browser-memory-value">{browserValue || "尚未写入"}</dd>
          </dl>
          <p className="empty">可见人工中断：{stream.interrupts.length}</p>
        </section>
        <section className="panel toolCallingPanel">
          <div className="panelTitle"><h2>Tool calls</h2><span className="count">{toolCalls.length}</span></div>
          <div className="toolList">
            {toolCalls.length ? toolCalls.map((toolCall: any) => <ToolCallCard key={toolCall.callId} toolCall={toolCall} />) : <p className="empty">等待浏览器工具调用</p>}
          </div>
        </section>
      </aside>
    </section>
  );
}

function reviewCardOf(message: any): RefundReviewCard | undefined {
  return message.response_metadata?.review_card ?? message.responseMetadata?.review_card;
}

function ResolvedReviewCard({ card }: { card: RefundReviewCard }) {
  return (
    <article className={`resolvedReviewCard ${card.decision?.approved ? "approved" : "declined"}`}>
      <div className="toolHead">
        <strong>{card.title}</strong>
        <span className={`badge ${card.decision?.approved ? "done" : "error"}`}>
          {card.decision?.approved ? "approved" : "declined"}
        </span>
      </div>
      <p>{card.context.order_id} / ¥{card.decision?.values?.amount ?? card.context.amount}</p>
      {card.decision?.values?.note && <small>{card.decision.values.note}</small>}
    </article>
  );
}

function CustomHitlPage() {
  const [threadId, setThreadId] = useState<string | null>(
    () => sessionStorage.getItem(CUSTOM_HITL_THREAD_KEY),
  );
  const [input, setInput] = useState(ASSISTANTS.custom_hitl.prompt);
  const [amount, setAmount] = useState("188");
  const [note, setNote] = useState("已核对订单与退款原因");
  const [formError, setFormError] = useState("");
  const [recentCard, setRecentCard] = useState<RefundReviewCard>();

  const updateThreadId = useCallback((id: string | null) => {
    setThreadId(id);
    if (id) sessionStorage.setItem(CUSTOM_HITL_THREAD_KEY, id);
    else sessionStorage.removeItem(CUSTOM_HITL_THREAD_KEY);
  }, []);
  const stream = useStream<any>({
    apiUrl: API_URL,
    assistantId: "custom_hitl",
    threadId,
    onThreadId: updateThreadId,
  });
  const card = stream.interrupt?.value as RefundReviewCard | undefined;

  useEffect(() => {
    if (threadId) return;
    stream.client.threads.create().then((thread) => updateThreadId(thread.thread_id));
  }, [stream.client, threadId, updateThreadId]);

  useEffect(() => {
    if (!card) return;
    setAmount(String(card.context.amount));
    setFormError("");
  }, [stream.interrupt?.id]);

  function submit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content || !threadId || stream.interrupt) return;
    stream.submit({ messages: [{ type: "human", content }] });
    setInput("");
  }

  async function resolveReview(approved: boolean) {
    if (!stream.interrupt || !card) return;
    const parsedAmount = Number(amount);
    if (approved && (!Number.isFinite(parsedAmount) || parsedAmount <= 0)) {
      setFormError("退款金额必须是大于 0 的数字");
      return;
    }
    const decision: ReviewDecision = {
      approved,
      values: { amount: parsedAmount, note: note.trim() },
    };
    setRecentCard({ ...card, resolved: true, decision });
    try {
      await stream.respond(decision, { interruptId: stream.interrupt.id });
    } catch (error) {
      setRecentCard(undefined);
      setFormError(error instanceof Error ? error.message : String(error));
    }
  }

  const historyMessages = stream.values?.messages ?? stream.messages ?? [];
  const hasPersistedCard = historyMessages.some((message: any) => reviewCardOf(message));

  return (
    <section className="hitlLayout">
      <section className="panel hitlChat">
        <div className="panelTitle"><h2>Refund workflow</h2><span className={`live ${stream.isLoading ? "on" : ""}`}>{stream.isLoading ? "running" : card ? "waiting review" : "idle"}</span></div>
        <div className="messages">
          {historyMessages.map((message: any, index: number) => {
            const resolvedCard = reviewCardOf(message);
            if (resolvedCard) return <ResolvedReviewCard card={resolvedCard} key={message.id ?? index} />;
            return isConversationMessage(message) ? <MessageBubble message={message} key={message.id ?? index} /> : null;
          })}
          {recentCard && !hasPersistedCard && <ResolvedReviewCard card={recentCard} />}
          {stream.error ? <pre className="errorBox">{pretty(stream.error)}</pre> : null}
        </div>
        <form className="composer" onSubmit={submit}>
          <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="输入退款原因" />
          <button type="submit" disabled={!threadId || stream.isLoading || Boolean(card)}>发送</button>
        </form>
      </section>
      <aside className="panel approvalPanel">
        <div className="panelTitle"><h2>Custom interrupt form</h2><span className={`badge ${card ? "running" : "done"}`}>{card ? "pending" : "clear"}</span></div>
        {card?.form_type === "refund_approval" ? (
          <>
            <div className="reviewContext">
              <strong>{card.title}</strong>
              <span>{card.context.order_id}</span>
              <p>{card.context.reason}</p>
            </div>
            <label>退款金额<input inputMode="decimal" value={amount} onChange={(event) => setAmount(event.target.value)} /></label>
            <label>审核备注<textarea rows={4} value={note} onChange={(event) => setNote(event.target.value)} /></label>
            {formError && <p className="fileError">{formError}</p>}
            <div className="approvalButtons">
              <button type="button" onClick={() => void resolveReview(true)}>Approve</button>
              <button className="rejectButton" type="button" onClick={() => void resolveReview(false)}>Decline</button>
            </div>
          </>
        ) : (
          <p className="empty">提交退款原因后，工具会在这里请求自定义审核表单。</p>
        )}
      </aside>
    </section>
  );
}

function BranchingMessage({ stream, message, historyCheckpointId }: { stream: any; message: any; historyCheckpointId?: string }) {
  const metadata = useMessageMetadata(stream, message.id);
  const checkpointId = historyCheckpointId ?? metadata?.parentCheckpointId;
  const human = messageType(message) === "human";
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(textOf(message));

  function submitEdit(event: FormEvent) {
    event.preventDefault();
    const content = draft.trim();
    if (!checkpointId || !content) return;
    stream.submit(
      { messages: [{ type: "human", content }] },
      { forkFrom: checkpointId },
    );
    setEditing(false);
  }

  return (
    <div className="branchMessage">
      <MessageBubble message={message} />
      {editing ? (
        <form className="branchEdit" onSubmit={submitEdit}>
          <textarea rows={3} value={draft} onChange={(event) => setDraft(event.target.value)} />
          <div>
            <button type="submit" disabled={!checkpointId || draft.trim() === textOf(message).trim()}>创建分支</button>
            <button className="secondaryButton" type="button" onClick={() => setEditing(false)}>取消</button>
          </div>
        </form>
      ) : (
        <div className="branchActions">
          {human ? (
            <button className="secondaryButton" type="button" disabled={!checkpointId} onClick={() => setEditing(true)}>编辑并分叉</button>
          ) : (
            <button
              className="secondaryButton"
              type="button"
              disabled={!checkpointId || stream.isLoading}
              onClick={() => stream.submit(undefined, { forkFrom: checkpointId })}
            >
              重新生成
            </button>
          )}
          <small>{checkpointId ? `fork ${checkpointId.slice(0, 8)}` : "等待 checkpoint"}</small>
        </div>
      )}
    </div>
  );
}

function BranchingChatPage() {
  const [threadId, setThreadId] = useState<string | null>(
    () => sessionStorage.getItem(BRANCHING_THREAD_KEY),
  );
  const [input, setInput] = useState(ASSISTANTS.branching_chat.prompt);
  const [historyCheckpoints, setHistoryCheckpoints] = useState<Map<string, string>>(new Map());
  const [checkpointError, setCheckpointError] = useState<string | null>(null);
  const updateThreadId = useCallback((id: string | null) => {
    setThreadId(id);
    if (id) sessionStorage.setItem(BRANCHING_THREAD_KEY, id);
    else sessionStorage.removeItem(BRANCHING_THREAD_KEY);
  }, []);
  const stream = useStream<any>({
    apiUrl: API_URL,
    assistantId: "branching_chat",
    threadId,
    onThreadId: updateThreadId,
  });
  const lastMessageId = stream.messages.at(-1)?.id;

  useEffect(() => {
    if (!threadId || stream.isLoading || !lastMessageId) return;
    let cancelled = false;
    stream.client.threads.getHistory<{ messages: any[] }>(threadId, { limit: 50 }).then((history) => {
      if (cancelled) return;
      const checkpoints = new Map<string, string>();
      for (const state of [...history].reverse()) {
        const checkpointId = state.parent_checkpoint?.checkpoint_id;
        if (!checkpointId) continue;
        for (const message of state.values?.messages ?? []) {
          if (message.id && !checkpoints.has(message.id)) checkpoints.set(message.id, checkpointId);
        }
      }
      setHistoryCheckpoints(checkpoints);
      setCheckpointError(null);
    }).catch((error) => {
      if (!cancelled) setCheckpointError(error instanceof Error ? error.message : String(error));
    });
    return () => { cancelled = true; };
  }, [lastMessageId, stream.client, stream.isLoading, threadId]);

  useEffect(() => {
    if (threadId) return;
    stream.client.threads.create().then((thread) => updateThreadId(thread.thread_id));
  }, [stream.client, threadId, updateThreadId]);

  function submit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content || !threadId) return;
    stream.submit({ messages: [{ type: "human", content }] });
    setInput("");
  }

  return (
    <section className="layout branchingLayout">
      <section className="panel">
        <div className="panelTitle"><h2>Checkpointed conversation</h2><span className={`live ${stream.isLoading ? "on" : ""}`}>{stream.isLoading ? "running" : "idle"}</span></div>
        <div className="messages">
          {(stream.messages ?? []).filter(isConversationMessage).map((message: any) => (
            <BranchingMessage key={message.id} stream={stream} message={message} historyCheckpointId={historyCheckpoints.get(message.id)} />
          ))}
          {stream.error ? <pre className="errorBox">{pretty(stream.error)}</pre> : null}
          {checkpointError ? <pre className="errorBox">{checkpointError}</pre> : null}
        </div>
        <form className="composer" onSubmit={submit}>
          <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="输入新问题" />
          <button type="submit" disabled={!threadId || stream.isLoading}>发送</button>
        </form>
      </section>
      <aside className="panel branchGuide">
        <div className="panelTitle"><h2>Fork controls</h2><span className="count">checkpoint</span></div>
        <div className="graphNodes">
          <article className="graphNode complete"><strong>Edit</strong><p>从 HumanMessage 的父 checkpoint 提交修改后的消息。</p></article>
          <article className="graphNode complete"><strong>Regenerate</strong><p>从 AIMessage 的父 checkpoint 重新执行，不追加用户消息。</p></article>
        </div>
      </aside>
    </section>
  );
}

type CheckpointState = {
  checkpoint: { checkpoint_id: string };
  values: { messages?: any[]; draft?: string };
  tasks?: { name?: string }[];
  next?: string[];
};

function TimeTravelPage() {
  const [threadId, setThreadId] = useState<string | null>(
    () => sessionStorage.getItem(TIME_TRAVEL_THREAD_KEY),
  );
  const [input, setInput] = useState(ASSISTANTS.time_travel.prompt);
  const [history, setHistory] = useState<CheckpointState[]>([]);
  const [selected, setSelected] = useState<CheckpointState>();
  const [historyError, setHistoryError] = useState<string>();
  const updateThreadId = useCallback((id: string | null) => {
    setThreadId(id);
    if (id) sessionStorage.setItem(TIME_TRAVEL_THREAD_KEY, id);
    else sessionStorage.removeItem(TIME_TRAVEL_THREAD_KEY);
  }, []);
  const stream = useStream<any>({
    apiUrl: API_URL,
    assistantId: "time_travel",
    threadId,
    onThreadId: updateThreadId,
  });
  const lastMessageId = stream.messages.at(-1)?.id;

  useEffect(() => {
    if (threadId) return;
    stream.client.threads.create().then((thread) => updateThreadId(thread.thread_id));
  }, [stream.client, threadId, updateThreadId]);

  useEffect(() => {
    if (!threadId || stream.isLoading || !lastMessageId) return;
    let cancelled = false;
    stream.client.threads.getHistory(threadId, { limit: 50 }).then((states) => {
      if (cancelled) return;
      const checkpoints = states as CheckpointState[];
      setHistory(checkpoints);
      setSelected((current) => checkpoints.find(
        (state) => state.checkpoint.checkpoint_id === current?.checkpoint.checkpoint_id,
      ) ?? checkpoints.find((state) => state.next?.includes("finalize")) ?? checkpoints[0]);
      setHistoryError(undefined);
    }).catch((error) => {
      if (!cancelled) setHistoryError(error instanceof Error ? error.message : String(error));
    });
    return () => { cancelled = true; };
  }, [lastMessageId, stream.client, stream.isLoading, threadId]);

  function submit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content || !threadId) return;
    stream.submit({ messages: [{ type: "human", content }] });
    setInput("");
  }

  function replay() {
    const checkpointId = selected?.checkpoint.checkpoint_id;
    if (!checkpointId || !selected.next?.length || stream.isLoading) return;
    if (!window.confirm(`从 checkpoint ${checkpointId.slice(-8)} 重放后续节点？`)) return;
    stream.submit({}, { forkFrom: checkpointId });
  }

  return (
    <section className="timeTravelLayout">
      <aside className="panel checkpointPanel">
        <div className="panelTitle"><h2>Checkpoint history</h2><span className="count">{history.length}</span></div>
        <div className="checkpointList">
          {history.map((state) => {
            const id = state.checkpoint.checkpoint_id;
            return (
              <button className={selected?.checkpoint.checkpoint_id === id ? "selected" : ""} key={id} type="button" onClick={() => setSelected(state)}>
                <strong>{id.slice(-8)}</strong>
                <span>{state.tasks?.[0]?.name ?? "checkpoint"}</span>
                <small>next: {state.next?.join(", ") || "END"} / messages: {state.values?.messages?.length ?? 0}</small>
              </button>
            );
          })}
          {!history.length && <p className="empty">提交一次任务后读取 checkpoint 历史。</p>}
        </div>
      </aside>
      <section className="panel timeTravelConversation">
        <div className="panelTitle"><h2>Conversation</h2><span className={`live ${stream.isLoading ? "on" : ""}`}>{stream.isLoading ? "replaying" : "idle"}</span></div>
        <div className="messages">
          {(stream.messages ?? []).filter(isConversationMessage).map((message: any, index: number) => <MessageBubble message={message} key={message.id ?? index} />)}
          {stream.error ? <pre className="errorBox">{pretty(stream.error)}</pre> : null}
          {historyError ? <pre className="errorBox">{historyError}</pre> : null}
        </div>
        <form className="composer" onSubmit={submit}>
          <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="输入需要生成草稿的问题" />
          <button type="submit" disabled={!threadId || stream.isLoading}>发送</button>
        </form>
      </section>
      <aside className="panel checkpointInspector">
        <div className="panelTitle"><h2>State inspector</h2><span className="count">values</span></div>
        {selected ? (
          <>
            <dl>
              <dt>checkpoint</dt><dd>{selected.checkpoint.checkpoint_id}</dd>
              <dt>next</dt><dd>{selected.next?.join(", ") || "END"}</dd>
            </dl>
            <section className="stateOutput"><pre>{JSON.stringify(selected.values, null, 2)}</pre></section>
            <button type="button" disabled={!selected.next?.length || stream.isLoading} onClick={replay}>从这里重放</button>
          </>
        ) : <p className="empty">选择 checkpoint 查看完整 state。</p>}
      </aside>
    </section>
  );
}

function ReasoningResponse({ message, isStreaming }: { message: any; isStreaming: boolean }) {
  const blocks = message.contentBlocks ?? [];
  const reasoning = blocks
    .filter((block: any) => block.type === "reasoning" && block.reasoning?.trim())
    .map((block: any) => block.reasoning)
    .join("");
  const text = blocks
    .filter((block: any) => block.type === "text" && block.text?.trim())
    .map((block: any) => block.text)
    .join("");

  if (!reasoning) return <MessageBubble message={message} />;

  return (
    <article className="reasoningResponse">
      <details className="thinkingBlock">
        <summary>
          <span>{isStreaming && !text ? "推理中" : "推理过程"}</span>
          <small>{reasoning.length} 字符</small>
        </summary>
        <p>{reasoning}</p>
      </details>
      {text ? (
        <div className="finalAnswer">
          <span className="role">final answer</span>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
        </div>
      ) : null}
    </article>
  );
}

function ReasoningTokensPage() {
  const [input, setInput] = useState(ASSISTANTS.reasoning_tokens.prompt);
  const stream = useStream<any>({
    apiUrl: API_URL,
    assistantId: "reasoning_tokens",
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content) return;
    stream.submit({ messages: [{ type: "human", content }] });
    setInput("");
  }

  return (
    <section className="layout reasoningLayout">
      <section className="panel">
        <div className="panelTitle"><h2>Reasoning conversation</h2><span className={`live ${stream.isLoading ? "on" : ""}`}>{stream.isLoading ? "streaming" : "idle"}</span></div>
        <div className="messages">
          {(stream.messages ?? []).filter(isConversationMessage).map((message: any, index: number) => {
            const isLast = index === stream.messages.length - 1;
            return messageType(message) === "ai"
              ? <ReasoningResponse key={message.id ?? index} message={message} isStreaming={stream.isLoading && isLast} />
              : <MessageBubble key={message.id ?? index} message={message} />;
          })}
          {stream.error ? <pre className="errorBox">{pretty(stream.error)}</pre> : null}
        </div>
        <form className="composer" onSubmit={submit}>
          <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="输入需要分析的问题" />
          <button type="submit" disabled={stream.isLoading}>发送</button>
        </form>
      </section>
    </section>
  );
}

function learningPlanOf(messages: any[]): { plan?: LearningPlan; error?: string } {
  for (const message of [...messages].reverse()) {
    if (!["ai", "AIMessage"].includes(messageType(message))) continue;
    const toolCalls = message.tool_calls ?? message.toolCalls ?? [];
    const call = toolCalls.find((toolCall: any) => toolCall.name === "render_learning_plan");
    if (!call) continue;
    const parsed = LearningPlanSchema.safeParse(call.args);
    if (parsed.success) return { plan: parsed.data };
    return { error: parsed.error.issues.map((issue) => issue.message).join("; ") };
  }
  return {};
}

function LearningPlanView({ plan }: { plan: LearningPlan }) {
  return (
    <div className="learningPlan">
      <header>
        <div><span className="role">learning plan</span><h2>{plan.topic}</h2></div>
        <span className="badge done">{plan.level}</span>
      </header>
      <dl className="planMetrics">
        <div><dt>总时长</dt><dd>{plan.total_minutes} 分钟</dd></div>
        <div><dt>课程</dt><dd>{plan.lessons.length} 节</dd></div>
        <div><dt>目标</dt><dd>{plan.objectives.length} 项</dd></div>
      </dl>
      <section className="planObjectives">
        <h3>学习目标</h3>
        <ul>{plan.objectives.map((objective) => <li key={objective}>{objective}</li>)}</ul>
      </section>
      <section className="planLessons">
        <h3>课程安排</h3>
        <ol>
          {plan.lessons.map((lesson, index) => (
            <li key={lesson.title}>
              <span>{index + 1}</span>
              <strong>{lesson.title}</strong>
              <small>{lesson.duration_minutes} 分钟</small>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

function StructuredOutputPage() {
  const [input, setInput] = useState(ASSISTANTS.structured_output.prompt);
  const stream = useStream<any>({ apiUrl: API_URL, assistantId: "structured_output" });
  const result = useMemo(() => learningPlanOf(stream.messages ?? []), [stream.messages]);

  function submit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content) return;
    stream.submit({ messages: [{ type: "human", content }] });
    setInput("");
  }

  return (
    <section className="structuredLayout">
      <section className="panel structuredPromptPanel">
        <div className="panelTitle"><h2>Plan request</h2><span className={`live ${stream.isLoading ? "on" : ""}`}>{stream.isLoading ? "generating" : "idle"}</span></div>
        <div className="structuredPrompts">
          {(stream.messages ?? []).filter((message: any) => messageType(message) === "human").map((message: any, index: number) => <MessageBubble message={message} compact key={message.id ?? index} />)}
        </div>
        <form className="composer" onSubmit={submit}>
          <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="输入学习主题" />
          <button type="submit" disabled={stream.isLoading}>生成</button>
        </form>
      </section>
      <section className="panel structuredResultPanel">
        <div className="panelTitle"><h2>Structured result</h2><span className="count">validated</span></div>
        {result.plan ? <LearningPlanView plan={result.plan} /> : stream.isLoading ? <p className="empty planning">正在生成结构化计划...</p> : result.error ? <pre className="errorBox">{result.error}</pre> : <p className="empty">尚无结构化结果</p>}
        {stream.error ? <pre className="errorBox">{pretty(stream.error)}</pre> : null}
      </section>
    </section>
  );
}

function generatedSpecOf(messages: any[]): Spec | null {
  for (const message of [...messages].reverse()) {
    if (!["ai", "AIMessage"].includes(messageType(message))) continue;
    const call = (message.tool_calls ?? message.toolCalls ?? []).find(
      (toolCall: any) => toolCall.name === "render_ui",
    );
    const raw = call?.args;
    if (!raw?.root || !raw?.elements?.[raw.root]) continue;
    const elements = Object.fromEntries(
      Object.entries(raw.elements).filter(([, element]: [string, any]) => element?.type && element?.props != null),
    ) as Spec["elements"];
    if (!elements[raw.root]) continue;
    return { root: raw.root, elements };
  }
  return null;
}

function GenerativeUIPage() {
  const [input, setInput] = useState(ASSISTANTS.generative_ui.prompt);
  const stream = useStream<any>({ apiUrl: API_URL, assistantId: "generative_ui" });
  const spec = useMemo(() => generatedSpecOf(stream.messages ?? []), [stream.messages]);

  function submit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content) return;
    stream.submit({ messages: [{ type: "human", content }] });
    setInput("");
  }

  return (
    <section className="generativeLayout">
      <aside className="panel generativePromptPanel">
        <div className="panelTitle"><h2>UI prompt</h2><span className={`live ${stream.isLoading ? "on" : ""}`}>{stream.isLoading ? "generating" : "idle"}</span></div>
        <div className="generativePrompts">
          {(stream.messages ?? []).filter((message: any) => messageType(message) === "human").map((message: any, index: number) => <MessageBubble message={message} compact key={message.id ?? index} />)}
        </div>
        <form className="composer" onSubmit={submit}>
          <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="描述要生成的界面" />
          <button type="submit" disabled={stream.isLoading}>生成</button>
        </form>
      </aside>
      <section className="panel generativeCanvas">
        <div className="panelTitle"><h2>Generated interface</h2><span className="count">catalog: 4</span></div>
        {spec ? (
          <JSONUIProvider registry={generativeRegistry}>
            <Renderer spec={spec} registry={generativeRegistry} loading={stream.isLoading} />
          </JSONUIProvider>
        ) : stream.isLoading ? <p className="empty planning">正在生成 UI spec...</p> : <p className="empty">提交描述后，Agent 将在组件白名单中组合界面。</p>}
        {stream.error ? <pre className="errorBox">{pretty(stream.error)}</pre> : null}
      </section>
    </section>
  );
}

function queuedMessage(entry: any) {
  const message = entry.values?.messages?.at(-1);
  return message ? textOf(message) : "等待处理";
}

function MessageQueuesPage() {
  const [input, setInput] = useState(ASSISTANTS.message_queues.prompt);
  const stream = useStream<any>({ apiUrl: API_URL, assistantId: "message_queues" });
  const queue = useSubmissionQueue(stream);

  function submit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content) return;
    stream.submit(
      { messages: [{ type: "human", content }] },
      { multitaskStrategy: "enqueue" },
    );
    setInput("");
  }

  return (
    <section className="messageQueueLayout">
      <section className="panel queueConversation">
        <div className="panelTitle">
          <h2>Conversation</h2>
          <span className={`live ${stream.isLoading ? "on" : ""}`}>{stream.isLoading ? "running" : "idle"}</span>
        </div>
        <div className="messages">
          {(stream.messages ?? []).filter(isConversationMessage).map((message: any, index: number) => <MessageBubble message={message} key={message.id ?? index} />)}
          {stream.error ? <pre className="errorBox">{pretty(stream.error)}</pre> : null}
        </div>
        <form className="composer" onSubmit={submit}>
          <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="运行中仍可继续提交" />
          <button type="submit">排队</button>
        </form>
      </section>
      <aside className="panel queuePanel">
        <div className="panelTitle"><h2>Pending queue</h2><span className="count">{queue.size}</span></div>
        <div className="queueActions">
          <button type="button" disabled={!stream.isLoading} onClick={() => void stream.stop()}>停止当前运行</button>
          <button className="secondaryButton" type="button" disabled={!queue.size} onClick={() => void queue.clear()}>清空等待项</button>
        </div>
        <ol className="queueEntries">
          {queue.entries.map((entry, index) => (
            <li key={entry.id}>
              <span className="queuePosition">{index + 1}</span>
              <span><strong>{queuedMessage(entry)}</strong><small>FIFO / pending</small></span>
              <button className="secondaryButton" type="button" aria-label={`取消 ${queuedMessage(entry)}`} onClick={() => void queue.cancel(entry.id)}>取消</button>
            </li>
          ))}
        </ol>
        {!queue.size ? <p className="empty">当前没有等待中的提交。</p> : null}
      </aside>
    </section>
  );
}

function JoinRejoinStream({
  threadId,
  onThreadId,
  onDisconnect,
}: {
  threadId: string | null;
  onThreadId: (id: string | null) => void;
  onDisconnect: () => void;
}) {
  const [input, setInput] = useState(ASSISTANTS.join_rejoin.prompt);
  const stream = useStream<any>({
    apiUrl: API_URL,
    assistantId: "join_rejoin",
    threadId,
    onThreadId,
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content || stream.isLoading) return;
    stream.submit({ messages: [{ type: "human", content }] });
    setInput("");
  }

  async function disconnect() {
    await stream.disconnect();
    onDisconnect();
  }

  return (
    <>
      <section className="panel rejoinConversation">
        <div className="panelTitle"><h2>Live stream</h2><span className={`live ${stream.isLoading ? "on" : ""}`}>{stream.isLoading ? "running" : "connected"}</span></div>
        <div className="messages">
          {(stream.messages ?? []).filter(isConversationMessage).map((message: any, index: number) => <MessageBubble message={message} key={message.id ?? index} />)}
          {stream.error ? <pre className="errorBox">{pretty(stream.error)}</pre> : null}
        </div>
        <form className="composer" onSubmit={submit}>
          <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="输入长任务" />
          <button type="submit" disabled={stream.isLoading}>发送</button>
        </form>
      </section>
      <aside className="panel connectionPanel">
        <div className="panelTitle"><h2>Connection</h2><span className="badge done">attached</span></div>
        <dl><dt>threadId</dt><dd>{threadId ?? stream.threadId ?? "首次提交后创建"}</dd><dt>run</dt><dd>{stream.isLoading ? "服务端执行中" : "空闲"}</dd></dl>
        <button type="button" disabled={!stream.isLoading || !(threadId ?? stream.threadId)} onClick={() => void disconnect()}>断开但继续运行</button>
        <p className="empty">这里调用 disconnect()，不会取消服务端 run。</p>
      </aside>
    </>
  );
}

function JoinRejoinPage() {
  const [threadId, setThreadId] = useState<string | null>(() => sessionStorage.getItem(JOIN_REJOIN_THREAD_KEY));
  const [connected, setConnected] = useState(true);
  const [mountKey, setMountKey] = useState(0);

  const updateThreadId = useCallback((id: string | null) => {
    setThreadId(id);
    if (id) sessionStorage.setItem(JOIN_REJOIN_THREAD_KEY, id);
    else sessionStorage.removeItem(JOIN_REJOIN_THREAD_KEY);
  }, []);

  function rejoin() {
    setMountKey((key) => key + 1);
    setConnected(true);
  }

  return (
    <section className="joinRejoinLayout">
      {connected ? (
        <JoinRejoinStream key={mountKey} threadId={threadId} onThreadId={updateThreadId} onDisconnect={() => setConnected(false)} />
      ) : (
        <section className="panel disconnectedPanel">
          <span className="badge error">disconnected</span>
          <h2>客户端已离开，服务端仍在运行</h2>
          <p>{threadId}</p>
          <button type="button" onClick={rejoin}>重新加入</button>
        </section>
      )}
    </section>
  );
}

function MessageBubble({ message, compact = false }: { message: any; compact?: boolean }) {
  const type = messageType(message);
  const text = textOf(message);
  if (!text.trim()) return null;

  return (
    <article className={`message ${type} ${compact ? "compact" : ""}`}>
      <span className="role">{type}</span>
      {type === "ai" || type === "AIMessage" ? (
        <div className="markdownContent">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
        </div>
      ) : (
        <div className="messageText">{text}</div>
      )}
    </article>
  );
}

function SubagentCard({
  stream,
  subagent,
}: {
  stream: AnyStream;
  subagent: SubagentDiscoverySnapshot;
}) {
  const [expanded, setExpanded] = useState(true);
  const messages = useMessages(stream, subagent);
  const toolCalls = useToolCalls(stream, subagent);
  const lastMessage = messages.at(-1);

  return (
    <article className={`subagentCard ${subagent.status ?? "unknown"}`}>
      <button className="cardButton" type="button" onClick={() => setExpanded(!expanded)}>
        <span>
          <strong>{subagent.name ?? subagent.id}</strong>
          <small>{messages.length} messages / {toolCalls.length} tools</small>
        </span>
        <span className={`badge ${subagent.status ?? "unknown"}`}>{subagent.status ?? "unknown"}</span>
      </button>
      {expanded && (
        <div className="subagentBody">
          {toolCalls.length > 0 && (
            <div className="toolList">
              {toolCalls.map((toolCall: any, index: number) => (
                <ToolCallCard key={toolCall.id ?? index} toolCall={toolCall} />
              ))}
            </div>
          )}
          {lastMessage ? (
            <MessageBubble message={lastMessage} compact />
          ) : (
            <p className="empty">等待 scoped messages...</p>
          )}
          <details>
            <summary>snapshot</summary>
            <pre>{JSON.stringify(subagent, null, 2)}</pre>
          </details>
        </div>
      )}
    </article>
  );
}

function TodoPanel({ todos, isLoading }: { todos: Todo[]; isLoading: boolean }) {
  const completed = todos.filter((todo) => todo.status === "completed").length;
  const percentage = todos.length ? Math.round((completed / todos.length) * 100) : 0;

  return (
    <section className="panel todoPanel">
      <div className="panelTitle">
        <h2>Agent Progress</h2>
        <span className="count">{completed}/{todos.length}</span>
      </div>
      {todos.length > 0 ? (
        <>
          <div className="progress" aria-label={`任务进度 ${percentage}%`}>
            <span style={{ width: `${percentage}%` }} />
          </div>
          <ul className="todoList">
            {todos.map((todo, index) => (
              <li className={`todoItem ${todo.status}`} key={`${todo.content}-${index}`}>
                <span className="todoMarker" aria-hidden="true">
                  {todo.status === "completed" ? "✓" : ""}
                </span>
                <span>{todo.content}</span>
                <small>{todo.status}</small>
              </li>
            ))}
          </ul>
        </>
      ) : (
        <p className={`empty ${isLoading ? "planning" : ""}`}>
          {isLoading ? "Agent 正在创建计划..." : "提交一个多步骤任务以生成计划"}
        </p>
      )}
    </section>
  );
}

async function fetchWorkspace(threadId: string) {
  const treeResponse = await fetch(`${API_URL}/sandbox/${encodeURIComponent(threadId)}/tree`);
  if (!treeResponse.ok) throw new Error(`加载文件树失败：${treeResponse.status}`);
  const tree = await treeResponse.json();
  const entries = tree.entries as FileEntry[];
  const files = Object.fromEntries(
    await Promise.all(
      entries.filter((entry) => entry.type === "file").map(async (entry) => {
        const response = await fetch(
          `${API_URL}/sandbox/${encodeURIComponent(threadId)}/file?filePath=${encodeURIComponent(entry.path)}`,
        );
        if (!response.ok) throw new Error(`读取 ${entry.path} 失败：${response.status}`);
        const data = await response.json();
        return [entry.path, data.content as string] as const;
      }),
    ),
  );
  return { entries, files };
}

function SandboxPage() {
  const [threadId, setThreadId] = useState<string | null>(
    () => sessionStorage.getItem(SANDBOX_THREAD_KEY),
  );
  const [input, setInput] = useState(ASSISTANTS.sandbox_agent.prompt);
  const [entries, setEntries] = useState<FileEntry[]>([]);
  const [files, setFiles] = useState<Record<string, string>>({});
  const [originalFiles, setOriginalFiles] = useState<Record<string, string>>({});
  const [selectedPath, setSelectedPath] = useState("/src/app.py");
  const [viewMode, setViewMode] = useState<"current" | "diff">("current");
  const [fileError, setFileError] = useState("");

  const updateThreadId = useCallback((id: string | null) => {
    setThreadId(id);
    if (id) sessionStorage.setItem(SANDBOX_THREAD_KEY, id);
    else sessionStorage.removeItem(SANDBOX_THREAD_KEY);
  }, []);

  const stream = useStream<any>({
    apiUrl: API_URL,
    assistantId: "sandbox_agent",
    threadId,
    onThreadId: updateThreadId,
  });

  const refreshWorkspace = useCallback(async () => {
    if (!threadId) return null;
    try {
      const snapshot = await fetchWorkspace(threadId);
      setEntries(snapshot.entries);
      setFiles(snapshot.files);
      setOriginalFiles((current) => Object.keys(current).length ? current : snapshot.files);
      setSelectedPath((current) => current in snapshot.files ? current : Object.keys(snapshot.files)[0] ?? "");
      setFileError("");
      return snapshot.files;
    } catch (error) {
      setFileError(error instanceof Error ? error.message : String(error));
      return null;
    }
  }, [threadId]);

  useEffect(() => {
    if (threadId) return;
    stream.client.threads.create().then((thread) => updateThreadId(thread.thread_id));
  }, [stream.client, threadId, updateThreadId]);

  useEffect(() => {
    void refreshWorkspace();
  }, [refreshWorkspace]);

  const fileToolCalls = (stream.toolCalls ?? []).filter((toolCall: any) =>
    ["read_file", "write_file", "edit_file"].includes(toolName(toolCall)),
  );
  const completedMutationKey = fileToolCalls
    .filter((toolCall: any) => FILE_MUTATING_TOOLS.has(toolName(toolCall)) && toolResult(toolCall))
    .map((toolCall: any) => toolCall.id ?? pretty(toolArgs(toolCall)))
    .join("|");

  useEffect(() => {
    if (completedMutationKey) void refreshWorkspace();
  }, [completedMutationKey, refreshWorkspace]);

  const changedFiles = new Set([
    ...Object.keys(files).filter((path) => files[path] !== originalFiles[path]),
    ...Object.keys(originalFiles).filter((path) => !(path in files)),
  ]);
  const fileEntries = entries.filter((entry) => entry.type === "file");
  const selectedChanged = changedFiles.has(selectedPath);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content || !threadId) return;
    const before = await refreshWorkspace();
    if (before) setOriginalFiles(before);
    setViewMode("diff");
    stream.submit({ messages: [{ type: "human", content }] });
    setInput("");
  }

  function newWorkspace() {
    updateThreadId(null);
    window.location.reload();
  }

  return (
    <section className="sandboxLayout">
      <aside className="panel filePanel">
        <div className="panelTitle">
          <h2>Files</h2>
          <span className="count">{fileEntries.length}</span>
        </div>
        <button className="secondaryButton" type="button" onClick={newWorkspace}>New workspace</button>
        <div className="fileTree">
          {entries.map((entry) => entry.type === "directory" ? (
            <div className="folderRow" key={entry.path}>▾ {entry.path}</div>
          ) : (
            <button
              className={`fileRow ${selectedPath === entry.path ? "selected" : ""}`}
              key={entry.path}
              type="button"
              onClick={() => {
                setSelectedPath(entry.path);
                setViewMode(changedFiles.has(entry.path) ? "diff" : "current");
              }}
            >
              <span>{entry.path}</span>
              {changedFiles.has(entry.path) && <small>M</small>}
            </button>
          ))}
        </div>
        {fileError && <p className="fileError">{fileError}</p>}
      </aside>

      <section className="panel editorPanel">
        <div className="editorHead">
          <div>
            <h2>{selectedPath || "Select a file"}</h2>
            {selectedChanged && <span className="changedLabel">modified</span>}
          </div>
          <div className="viewTabs">
            <button className={viewMode === "current" ? "active" : ""} type="button" onClick={() => setViewMode("current")}>Code</button>
            <button className={viewMode === "diff" ? "active" : ""} type="button" onClick={() => setViewMode("diff")} disabled={!selectedChanged}>Diff</button>
          </div>
        </div>
        {viewMode === "diff" && selectedChanged ? (
          <div className="diffView">
            <div><span>Before</span><pre>{originalFiles[selectedPath] ?? "(new file)"}</pre></div>
            <div><span>After</span><pre>{files[selectedPath] ?? "(deleted)"}</pre></div>
          </div>
        ) : (
          <pre className="codeViewer">{files[selectedPath] ?? "文件加载中..."}</pre>
        )}
      </section>

      <section className="panel sandboxChat">
        <div className="panelTitle">
          <h2>Agent</h2>
          <span className={`live ${stream.isLoading ? "on" : ""}`}>{stream.isLoading ? "working" : "idle"}</span>
        </div>
        <div className="sandboxMessages">
          {(stream.messages ?? []).filter(isConversationMessage).map((message: any, index: number) => (
            <MessageBubble message={message} compact key={message.id ?? index} />
          ))}
          {fileToolCalls.map((toolCall: any, index: number) => (
            <ToolCallCard key={toolCall.id ?? index} toolCall={toolCall} />
          ))}
          {stream.error ? <pre className="errorBox">{pretty(stream.error)}</pre> : null}
        </div>
        <form className="composer" onSubmit={submit}>
          <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="描述代码修改" />
          <button type="submit" disabled={stream.isLoading || !threadId}>发送</button>
        </form>
      </section>
    </section>
  );
}

function HitlPage() {
  const [threadId, setThreadId] = useState<string | null>(
    () => sessionStorage.getItem(HITL_THREAD_KEY),
  );
  const [input, setInput] = useState(ASSISTANTS.hitl_agent.prompt);
  const [channel, setChannel] = useState("");
  const [message, setMessage] = useState("");
  const [rejectReason, setRejectReason] = useState("本次通知暂不发送，请勿重试。");
  const endRef = useRef<HTMLDivElement | null>(null);

  const updateThreadId = useCallback((id: string | null) => {
    setThreadId(id);
    if (id) sessionStorage.setItem(HITL_THREAD_KEY, id);
    else sessionStorage.removeItem(HITL_THREAD_KEY);
  }, []);

  const stream = useStream<any>({
    apiUrl: API_URL,
    assistantId: "hitl_agent",
    threadId,
    onThreadId: updateThreadId,
  });
  const request = stream.interrupt?.value as HitlRequest | undefined;
  const action = request?.action_requests?.[0];
  const allowed = new Set(request?.review_configs?.[0]?.allowed_decisions ?? []);

  useEffect(() => {
    if (!action) return;
    setChannel(String(action.args.channel ?? ""));
    setMessage(String(action.args.message ?? ""));
  }, [stream.interrupt?.id]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [stream.messages, stream.toolCalls, stream.interrupt, stream.isLoading]);

  function submit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content || stream.interrupt) return;
    stream.submit({ messages: [{ type: "human", content }] });
    setInput("");
  }

  async function respond(decision: Record<string, unknown>) {
    if (!stream.interrupt) return;
    await stream.respond(
      { decisions: [decision] },
      stream.interrupt.id ? { interruptId: stream.interrupt.id } : undefined,
    );
  }

  const announcementCalls = (stream.toolCalls ?? []).filter(
    (toolCall: any) => toolName(toolCall) === "send_release_announcement",
  );

  return (
    <section className="hitlLayout">
      <section className="panel hitlChat">
        <div className="panelTitle">
          <h2>Agent run</h2>
          <span className={`live ${stream.isLoading ? "on" : ""}`}>
            {stream.isLoading ? "running" : stream.interrupt ? "waiting review" : "idle"}
          </span>
        </div>
        <div className="messages">
          {(stream.messages ?? []).filter(isConversationMessage).map((item: any, index: number) => (
            <MessageBubble message={item} key={item.id ?? index} />
          ))}
          {announcementCalls.map((toolCall: any, index: number) => (
            <ToolCallCard key={toolCall.id ?? index} toolCall={toolCall} />
          ))}
          {stream.error ? <pre className="errorBox">{pretty(stream.error)}</pre> : null}
          <div ref={endRef} />
        </div>
        <form className="composer" onSubmit={submit}>
          <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="描述要发送的通知" />
          <button type="submit" disabled={stream.isLoading || Boolean(stream.interrupt)}>发送</button>
        </form>
      </section>

      <aside className="panel approvalPanel">
        <div className="panelTitle">
          <h2>Human review</h2>
          <span className={`badge ${action ? "running" : "done"}`}>{action ? "pending" : "clear"}</span>
        </div>
        {action ? (
          <>
            <div className="approvalAction">
              <span>Requested tool</span>
              <strong>{action.name}</strong>
              {action.description && <p>{action.description}</p>}
            </div>
            <label>
              Channel
              <input value={channel} onChange={(event) => setChannel(event.target.value)} />
            </label>
            <label>
              Message
              <textarea rows={5} value={message} onChange={(event) => setMessage(event.target.value)} />
            </label>
            <div className="approvalButtons">
              {allowed.has("approve") && (
                <button type="button" onClick={() => void respond({ type: "approve" })}>Approve</button>
              )}
              {allowed.has("edit") && (
                <button
                  className="secondaryButton"
                  type="button"
                  onClick={() => void respond({
                    type: "edit",
                    edited_action: { name: action.name, args: { channel, message } },
                  })}
                >
                  Edit &amp; approve
                </button>
              )}
            </div>
            {allowed.has("reject") && (
              <label>
                Rejection reason
                <textarea rows={3} value={rejectReason} onChange={(event) => setRejectReason(event.target.value)} />
                <button className="rejectButton" type="button" onClick={() => void respond({ type: "reject", message: rejectReason })}>
                  Reject
                </button>
              </label>
            )}
          </>
        ) : (
          <p className="empty">提交通知请求后，待审批工具会暂停在这里。</p>
        )}
      </aside>
    </section>
  );
}

function DynamicToolsPage() {
  const [input, setInput] = useState(ASSISTANTS.dynamic_tools_agent.prompt);
  const [enabledTools, setEnabledTools] = useState<string[]>(
    DYNAMIC_TOOL_OPTIONS.map((item) => item.name),
  );
  const endRef = useRef<HTMLDivElement | null>(null);
  const stream = useStream<any>({
    apiUrl: API_URL,
    assistantId: "dynamic_tools_agent",
  });

  const selectedCalls = (stream.toolCalls ?? []).filter((toolCall: any) =>
    DYNAMIC_TOOL_OPTIONS.some((item) => item.name === toolName(toolCall)),
  );

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [stream.messages, stream.toolCalls, stream.isLoading]);

  function toggleTool(name: string) {
    setEnabledTools((current) =>
      current.includes(name)
        ? current.filter((item) => item !== name)
        : [...current, name],
    );
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content) return;
    stream.submit(
      { messages: [{ type: "human", content }], enabled_tools: enabledTools },
    );
    setInput("");
  }

  return (
    <section className="dynamicToolsLayout">
      <aside className="panel toolSelectorPanel">
        <div className="panelTitle">
          <h2>Run capabilities</h2>
          <span className="count">{enabledTools.length}/{DYNAMIC_TOOL_OPTIONS.length}</span>
        </div>
        <div className="toolOptions">
          {DYNAMIC_TOOL_OPTIONS.map((item) => (
            <label className="toolOption" key={item.name}>
              <input
                type="checkbox"
                checked={enabledTools.includes(item.name)}
                disabled={stream.isLoading}
                onChange={() => toggleTool(item.name)}
              />
              <span>
                <strong>{item.label}</strong>
                <small>{item.name}</small>
                <small>{item.description}</small>
              </span>
            </label>
          ))}
        </div>
      </aside>

      <section className="panel dynamicToolsChat">
        <div className="panelTitle">
          <h2>Agent run</h2>
          <span className={`live ${stream.isLoading ? "on" : ""}`}>
            {stream.isLoading ? "running" : "idle"}
          </span>
        </div>
        <div className="messages">
          {(stream.messages ?? []).filter(isConversationMessage).map((message: any, index: number) => (
            <MessageBubble message={message} key={message.id ?? index} />
          ))}
          {selectedCalls.map((toolCall: any, index: number) => (
            <ToolCallCard key={toolCall.id ?? index} toolCall={toolCall} />
          ))}
          {stream.error ? <pre className="errorBox">{pretty(stream.error)}</pre> : null}
          <div ref={endRef} />
        </div>
        <form className="composer" onSubmit={submit}>
          <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="输入需要工具完成的任务" />
          <button type="submit" disabled={stream.isLoading}>发送</button>
        </form>
      </section>
    </section>
  );
}

function McpSkillsPage() {
  const [strategy, setStrategy] = useState<"factory" | "isolated" | "static">("factory");
  const [input, setInput] = useState(ASSISTANTS.mcp_skills_agent.prompt);
  const [enabledMcpTools, setEnabledMcpTools] = useState<string[]>(MCP_TOOL_OPTIONS.map((item) => item.id));
  const [enabledSkills, setEnabledSkills] = useState<string[]>(SKILL_OPTIONS.map((item) => item.id));
  const endRef = useRef<HTMLDivElement | null>(null);
  const assistantId = strategy === "factory"
    ? "mcp_skills_factory_agent"
    : strategy === "isolated"
      ? "mcp_skills_isolated_agent"
      : "mcp_skills_static_agent";
  const stream = useStream<any>({ apiUrl: API_URL, assistantId });

  const visibleCalls = (stream.toolCalls ?? []).filter((toolCall: any) =>
    toolName(toolCall).startsWith("teaching_")
      || toolName(toolCall) === "read_file"
      || toolName(toolCall) === "load_skill",
  );

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [stream.messages, stream.toolCalls, stream.isLoading]);

  function toggle(value: string, current: string[], setter: (next: string[]) => void) {
    setter(current.includes(value) ? current.filter((item) => item !== value) : [...current, value]);
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content) return;
    if (strategy === "static") {
      stream.submit({
        messages: [{ type: "human", content }],
        enabled_capabilities: enabledMcpTools.length ? ["currency"] : [],
      });
    } else {
      stream.submit(
        { messages: [{ type: "human", content }], enabled_mcp_tools: enabledMcpTools },
        { config: { configurable: { enabled_skills: enabledSkills } } },
      );
    }
    setInput("");
  }

  return (
    <section className="mcpSkillsLayout">
      <aside className="panel toolSelectorPanel">
        <div className="panelTitle"><h2>Strict strategy</h2></div>
        <div className="strategySwitch" role="group" aria-label="Skill strict strategy">
          <button type="button" className={strategy === "factory" ? "active" : ""} disabled={stream.isLoading} onClick={() => setStrategy("factory")}>1 Factory</button>
          <button type="button" className={strategy === "isolated" ? "active" : ""} disabled={stream.isLoading} onClick={() => setStrategy("isolated")}>2 Isolation</button>
          <button type="button" className={strategy === "static" ? "active" : ""} disabled={stream.isLoading} onClick={() => setStrategy("static")}>3 Static</button>
        </div>
        <p className="strategyHint">{strategy === "factory"
          ? "只把选中的 Skill 注册进本轮 Agent"
          : strategy === "isolated"
            ? "未选 Skill 同时从 discovery 消失并被文件权限拒绝"
            : "静态 Agent：选择 MCP Tool 后自动启用关联 Skill"}</p>
        <div className="panelTitle"><h2>MCP Tools</h2><span className="count">{enabledMcpTools.length}/{MCP_TOOL_OPTIONS.length}</span></div>
        <div className="toolOptions">
          {MCP_TOOL_OPTIONS.map((item) => (
            <label className="toolOption" key={item.id}>
              <input type="checkbox" checked={enabledMcpTools.includes(item.id)} disabled={stream.isLoading} onChange={() => toggle(item.id, enabledMcpTools, setEnabledMcpTools)} />
              <span><strong>{item.label}</strong><small>{item.id}</small><small>{item.description}</small></span>
            </label>
          ))}
        </div>
        <div className="panelTitle selectorGroupTitle"><h2>Skills</h2><span className="count">{strategy === "static" ? Number(enabledMcpTools.length > 0) : enabledSkills.length}/{SKILL_OPTIONS.length}</span></div>
        <div className="toolOptions">
          {SKILL_OPTIONS.map((item) => (
            <label className="toolOption" key={item.id}>
              <input
                type="checkbox"
                checked={strategy === "static" ? enabledMcpTools.length > 0 : enabledSkills.includes(item.id)}
                disabled={stream.isLoading || strategy === "static"}
                onChange={() => toggle(item.id, enabledSkills, setEnabledSkills)}
              />
              <span><strong>{item.label}</strong><small>{item.id}</small><small>{item.description}</small></span>
            </label>
          ))}
        </div>
      </aside>
      <section className="panel dynamicToolsChat">
        <div className="panelTitle"><h2>Agent run</h2><span className={`live ${stream.isLoading ? "on" : ""}`}>{stream.isLoading ? "running" : "idle"}</span></div>
        <div className="messages">
          {(stream.messages ?? []).filter(isConversationMessage).map((message: any, index: number) => <MessageBubble message={message} key={message.id ?? index} />)}
          {visibleCalls.map((toolCall: any, index: number) => <ToolCallCard key={toolCall.id ?? index} toolCall={toolCall} />)}
          {stream.error ? <pre className="errorBox">{pretty(stream.error)}</pre> : null}
          <div ref={endRef} />
        </div>
        <form className="composer" onSubmit={submit}>
          <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="输入需要 MCP 与 Skill 完成的任务" />
          <button type="submit" disabled={stream.isLoading}>发送</button>
        </form>
      </section>
    </section>
  );
}

type GraphExecutionStep = { name: string; output: string };
type ExecutionProgressEvent = GraphExecutionStep & { kind: "node_complete" };

function GraphExecutionNode({ step }: { step: GraphExecutionStep }) {

  return (
    <article className="graphNode complete">
      <div className="toolHead">
        <span>{step.name}</span>
        <span className="badge complete">complete</span>
      </div>
      <p>{step.output}</p>
    </article>
  );
}

function GraphExecutionPage() {
  const [input, setInput] = useState(ASSISTANTS.graph_execution.prompt);
  const stream = useStream<any>({ apiUrl: API_URL, assistantId: "graph_execution" });
  const steps = (stream.values?.execution_steps ?? []) as GraphExecutionStep[];

  function submit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content) return;
    stream.submit({ messages: [{ type: "human", content }] });
    setInput("");
  }

  return (
    <section className="graphExecutionLayout">
      <aside className="panel graphProgressPanel">
        <div className="panelTitle"><h2>Graph nodes</h2><span className="count">{steps.length}/3</span></div>
        <div className="graphSteps">
          {steps.length ? steps.map((step) => (
            <div className="graphStep complete" key={step.name}>
              <span aria-hidden="true" />
              <strong>{step.name}</strong>
              <small>complete</small>
            </div>
          )) : <p className="empty">提交请求后写入节点进度</p>}
        </div>
      </aside>
      <section className="panel graphExecutionPanel">
        <div className="panelTitle"><h2>Graph execution</h2><span className={`live ${stream.isLoading ? "on" : ""}`}>{stream.isLoading ? "running" : "idle"}</span></div>
        <div className="graphNodes">
          {steps.map((step) => <GraphExecutionNode key={step.name} step={step} />)}
          {stream.error ? <pre className="errorBox">{pretty(stream.error)}</pre> : null}
        </div>
        <section className="stateOutput">
          <h3>Graph state</h3>
          <pre>{JSON.stringify({
            classification: stream.values?.classification,
            analysis: stream.values?.analysis,
            synthesis: stream.values?.synthesis,
            execution_steps: steps,
          }, null, 2)}</pre>
        </section>
        <form className="composer" onSubmit={submit}>
          <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="输入要由图执行的任务" />
          <button type="submit" disabled={stream.isLoading}>发送</button>
        </form>
      </section>
    </section>
  );
}

function CustomStreamChannelsPage() {
  const [input, setInput] = useState(ASSISTANTS.custom_stream_channels.prompt);
  const stream = useStream<any>({ apiUrl: API_URL, assistantId: "custom_stream_channels" });
  const latest = useExtension<ExecutionProgressEvent>(stream, "execution-progress");
  const rawEvents = useChannel(stream, ["custom:execution-progress"], undefined, {
    bufferSize: 10,
    replay: true,
  });
  const history = rawEvents
    .map((event: any) => {
      const data = event.params?.data;
      return data?.payload?.payload ?? data?.payload ?? data;
    })
    .filter((payload: unknown): payload is ExecutionProgressEvent => (
      typeof payload === "object" && payload !== null && (payload as ExecutionProgressEvent).kind === "node_complete"
    ));

  function submit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content) return;
    stream.submit({ messages: [{ type: "human", content }] });
    setInput("");
  }

  return (
    <section className="graphExecutionLayout">
      <aside className="panel graphProgressPanel">
        <div className="panelTitle"><h2>Latest payload</h2><span className="count">useExtension</span></div>
        {latest ? <GraphExecutionNode step={latest} /> : <p className="empty">等待 execution-progress 事件</p>}
      </aside>
      <section className="panel graphExecutionPanel">
        <div className="panelTitle"><h2>Custom channel</h2><span className={`live ${stream.isLoading ? "on" : ""}`}>{stream.isLoading ? "streaming" : "idle"}</span></div>
        <p className="channelHint">`useChannel` 的 `custom:execution-progress` 原始事件历史。</p>
        <div className="graphNodes">
          {history.map((payload, index) => <GraphExecutionNode key={`${payload.name}-${index}`} step={payload} />)}
          {!history.length && !stream.error ? <p className="empty">提交请求后将收到三个独立 channel payload</p> : null}
          {stream.error ? <pre className="errorBox">{pretty(stream.error)}</pre> : null}
        </div>
        <form className="composer" onSubmit={submit}>
          <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="输入要由图执行的任务" />
          <button type="submit" disabled={stream.isLoading}>发送</button>
        </form>
      </section>
    </section>
  );
}

function StreamPage({ assistantId }: { assistantId: keyof typeof ASSISTANTS }) {
  const [input, setInput] = useState(ASSISTANTS[assistantId].prompt);
  const endRef = useRef<HTMLDivElement | null>(null);
  const stream = useStream<any>({
    apiUrl: API_URL,
    assistantId,
  });

  const subagents = useMemo(
    () => [...(stream.subagents?.values?.() ?? [])],
    [stream.subagents],
  );
  const completed = subagents.filter((subagent: SubagentDiscoverySnapshot) => subagent.status === "complete").length;
  const total = subagents.length;
  const progress = total ? Math.round((completed / total) * 100) : 0;
  const todos = (stream.values?.todos ?? []) as Todo[];
  const rootToolCalls = (stream.toolCalls ?? []).filter(
    (toolCall: any) => toolName(toolCall) === "task",
  );

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [stream.messages, stream.toolCalls, subagents.length, stream.isLoading]);

  function submit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content) return;
    stream.submit(
      { messages: [{ type: "human", content }] },
      { config: { recursion_limit: 100 } },
    );
    setInput("");
  }

  return (
    <section className="layout">
      <div className="panel">
        <div className="panelTitle">
          <h2>Coordinator</h2>
          <span className={`live ${stream.isLoading ? "on" : ""}`}>
            {stream.isLoading ? "streaming" : "idle"}
          </span>
        </div>
        <div className="messages">
          {(stream.messages ?? []).filter(isConversationMessage).map((message: any, index: number) => (
            <MessageBubble message={message} key={message.id ?? index} />
          ))}
          {rootToolCalls.length > 0 && (
            <div className="rootTools">
              <h3>Root tool calls</h3>
              {rootToolCalls.map((toolCall: any, index: number) => (
                <ToolCallCard key={toolCall.id ?? index} toolCall={toolCall} />
              ))}
            </div>
          )}
          {stream.error ? <pre className="errorBox">{pretty(stream.error)}</pre> : null}
          <div ref={endRef} />
        </div>
        <form className="composer" onSubmit={submit}>
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="输入问题"
          />
          <button type="submit" disabled={stream.isLoading}>发送</button>
        </form>
      </div>

      <aside className="side">
        {assistantId === "todo_agent" ? (
          <TodoPanel todos={todos} isLoading={stream.isLoading} />
        ) : (
          <section className="panel">
            <div className="panelTitle">
              <h2>Subagents</h2>
              <span className="count">{completed}/{total}</span>
            </div>
            <div className="progress">
              <span style={{ width: `${progress}%` }} />
            </div>
            {subagents.length === 0 ? (
              <p className="empty">暂无 subagent 快照</p>
            ) : (
              subagents.map((subagent: SubagentDiscoverySnapshot) => (
                <SubagentCard key={subagent.id} stream={stream} subagent={subagent} />
              ))
            )}
          </section>
        )}

        <section className="panel">
          <div className="panelTitle">
            <h2>Values</h2>
            <span className="count">state</span>
          </div>
          <pre className="valuesBox">{JSON.stringify(stream.values ?? {}, null, 2)}</pre>
        </section>
      </aside>
    </section>
  );
}

function FrontendIntegrationsPage() {
  const [scenario, setScenario] = useState<IntegrationScenario>("keep-control");
  const recommendation = recommendedIntegration(scenario);
  const selected = INTEGRATIONS.find((item) => item.id === recommendation)!;

  return (
    <section className="integrationsLayout">
      <aside className="panel integrationSelector">
        <div className="panelTitle"><h2>你的接入目标</h2><span className="count">decision</span></div>
        <div className="toolOptions">
          {INTEGRATION_SCENARIOS.map((item) => (
            <label className="toolOption" key={item.id}>
              <input type="radio" name="integration-scenario" checked={scenario === item.id} onChange={() => setScenario(item.id)} />
              <span><strong>{item.label}</strong><small>{item.detail}</small></span>
            </label>
          ))}
        </div>
        <section className="projectDecision">
          <h3>当前课程项目</h3>
          <p>继续使用 <code>@langchain/react useStream</code> + 自定义 UI。现有 Sandbox、HITL、分支、队列和 Time Travel 已经需要精确控制状态，替换完整 runtime 只会重复建设。</p>
        </section>
      </aside>

      <section className="panel integrationComparison">
        <div className="integrationRecommendation">
          <span>本场景推荐</span>
          <h2 data-testid="integration-recommendation">{selected.name}</h2>
          <p>{selected.position}；{selected.connection}。</p>
        </div>
        <div className="integrationTable" role="table" aria-label="前端集成方案比较">
          <div className="integrationRow integrationHeader" role="row">
            <strong role="columnheader">方案</strong><strong role="columnheader">定位</strong><strong role="columnheader">接入</strong><strong role="columnheader">后端变化</strong>
          </div>
          {INTEGRATIONS.map((item) => (
            <div className={`integrationRow ${item.id === recommendation ? "recommended" : ""}`} role="row" key={item.id}>
              <strong role="cell">{item.name}{item.id === recommendation && <span className="badge done">推荐</span>}</strong>
              <span role="cell">{item.position}</span><span role="cell">{item.connection}</span><span role="cell">{item.backend}</span>
            </div>
          ))}
        </div>
      </section>
    </section>
  );
}

function IntegrationComposer({ onSubmit, loading }: { onSubmit: (text: string) => void; loading: boolean }) {
  const [input, setInput] = useState("查询上海天气");
  return (
    <form className="composer integrationComposer" onSubmit={(event) => {
      event.preventDefault();
      const text = input.trim();
      if (!text) return;
      onSubmit(text);
      setInput("");
    }}>
      <input aria-label="Integration message" value={input} onChange={(event) => setInput(event.target.value)} />
      <button type="submit" disabled={loading}>发送</button>
    </form>
  );
}

function AIElementsExample() {
  const stream = useStream<any>({ apiUrl: API_URL, assistantId: "tool_calling" });
  const toolCalls = useToolCalls(stream);
  const messages = (stream.messages ?? []).filter(isConversationMessage);
  return (
    <section className="panel realIntegration" data-testid="ai-elements-example">
      <div className="panelTitle"><h2>AI Elements + useStream</h2><span className="badge done">gpt-5.5 + tool</span><span className={`live ${stream.isLoading ? "on" : ""}`}>{stream.isLoading ? "streaming" : "idle"}</span></div>
      <Conversation className="integrationConversation">
        <ConversationContent>
          {!messages.length && <ConversationEmptyState title="等待真实 LangGraph run" description="发送消息后会执行天气工具" />}
          {messages.map((message: any, index: number) => {
            const role = messageType(message);
            const from = role === "human" || role === "HumanMessage" ? "user" : "assistant";
            return <Message from={from} key={message.id ?? index}><MessageContent>{from === "assistant" ? <MessageResponse>{textOf(message)}</MessageResponse> : textOf(message)}</MessageContent></Message>;
          })}
          {toolCalls.map((call: any) => (
            <Tool defaultOpen key={call.callId}>
              <ToolHeader type="dynamic-tool" toolName={toolName(call)} state={toolResult(call) ? "output-available" : "input-available"} />
              <ToolContent><ToolInput input={toolArgs(call) ?? {}} /><ToolOutput output={toolResult(call)} errorText={undefined} /></ToolContent>
            </Tool>
          ))}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>
      <IntegrationComposer loading={stream.isLoading} onSubmit={(content) => stream.submit({ messages: [{ type: "human", content }] })} />
      {stream.error ? <pre className="errorBox">{pretty(stream.error)}</pre> : null}
    </section>
  );
}

type AssistantStoreMessage = { id: string; role: "user" | "assistant"; text: string };

function AssistantMessage() {
  return <MessagePrimitive.Root className="assistantMessage"><MessagePrimitive.Content /></MessagePrimitive.Root>;
}

function AssistantUIExample() {
  const stream = useStream<any>({ apiUrl: API_URL, assistantId: "tool_calling" });
  const messages = useMemo<AssistantStoreMessage[]>(() => (stream.messages ?? []).filter(isConversationMessage).map((message: any, index: number) => ({
    id: message.id ?? `message-${index}`,
    role: ["human", "HumanMessage"].includes(messageType(message)) ? "user" : "assistant",
    text: textOf(message),
  })), [stream.messages]);
  const runtime = useExternalStoreRuntime<AssistantStoreMessage>({
    messages,
    isRunning: stream.isLoading,
    convertMessage: (message): ThreadMessageLike => ({ id: message.id, role: message.role, content: [{ type: "text", text: message.text }] }),
    onNew: async (message) => {
      const text = message.content.filter((part) => part.type === "text").map((part) => part.text).join("");
      await stream.submit({ messages: [{ type: "human", content: text }] });
    },
    onCancel: async () => stream.stop(),
  });
  return (
    <section className="panel realIntegration" data-testid="assistant-ui-example">
      <div className="panelTitle"><h2>assistant-ui External Store</h2><span className="badge done">gpt-5.5 + tool</span><span className={`live ${stream.isLoading ? "on" : ""}`}>{stream.isLoading ? "streaming" : "idle"}</span></div>
      <AssistantRuntimeProvider runtime={runtime}>
        <ThreadPrimitive.Root className="assistantThread">
          <ThreadPrimitive.Viewport className="assistantViewport">
            <ThreadPrimitive.Messages components={{ Message: AssistantMessage }} />
            <ComposerPrimitive.Root className="assistantComposer">
              <ComposerPrimitive.Input aria-label="assistant-ui message" placeholder="查询上海天气" />
              <ComposerPrimitive.Send>发送</ComposerPrimitive.Send>
            </ComposerPrimitive.Root>
          </ThreadPrimitive.Viewport>
        </ThreadPrimitive.Root>
      </AssistantRuntimeProvider>
      {stream.error ? <pre className="errorBox">{pretty(stream.error)}</pre> : null}
    </section>
  );
}

function CopilotKitExample() {
  return (
    <section className="panel realIntegration copilotIntegration" data-testid="copilotkit-example">
      <div className="panelTitle"><h2>CopilotKit AG-UI</h2><span className="badge done">gpt-5.5 · /api/copilotkit</span></div>
      <CopilotKit selfManagedAgents={{ copilotkit_integration: COPILOTKIT_AGENT }} agent="copilotkit_integration" enableInspector={false}>
        <CopilotChat suggestions="manual" labels={{ title: "真实 AG-UI Agent", initial: "输入任意内容，后端会执行天气工具。", placeholder: "查询上海天气" }} />
      </CopilotKit>
    </section>
  );
}

function OpenUIExample() {
  const stream = useStream<any>({ apiUrl: API_URL, assistantId: "openui_integration" });
  const response = [...(stream.messages ?? [])].reverse().find((message: any) => ["ai", "AIMessage"].includes(messageType(message)));
  return (
    <section className="panel realIntegration" data-testid="openui-example">
      <div className="panelTitle"><h2>OpenUI Renderer</h2><span className="badge done">gpt-5.5 + tool</span><span className={`live ${stream.isLoading ? "on" : ""}`}>{stream.isLoading ? "streaming" : "idle"}</span></div>
      <div className="openuiCanvas">{response ? <OpenUIRenderer response={textOf(response)} library={openuiLibrary} isStreaming={stream.isLoading} /> : <p className="empty">发送消息，渲染后端返回的 openui-lang。</p>}</div>
      <IntegrationComposer loading={stream.isLoading} onSubmit={(content) => stream.submit({ messages: [{ type: "human", content }] })} />
      {stream.error ? <pre className="errorBox">{pretty(stream.error)}</pre> : null}
    </section>
  );
}

function IntegrationExamplesPage() {
  const [integration, setIntegration] = useState<IntegrationId>("ai-elements");

  return (
    <section className="integrationExamplesLayout">
      <nav className="integrationExampleTabs" aria-label="Integration examples">
        {INTEGRATIONS.map((item) => (
          <button type="button" className={integration === item.id ? "active" : ""} onClick={() => setIntegration(item.id)} key={item.id}>
            {item.name}
          </button>
        ))}
      </nav>

      <section className="integrationExampleBody">
        {integration === "ai-elements" ? <AIElementsExample /> : integration === "assistant-ui" ? <AssistantUIExample /> : integration === "copilotkit" ? <CopilotKitExample /> : <OpenUIExample />}
      </section>
    </section>
  );
}

function App() {
  const [assistantId, setAssistantId] =
    useState<keyof typeof ASSISTANTS>("frontend_agent");

  return (
    <main className="app">
      <header className="topbar">
        <div>
          <h1>Deep Agents Frontend Teach</h1>
          <p>{["frontend_integrations", "integration_examples"].includes(assistantId)
            ? "local integration lab"
            : assistantId === "mcp_skills_agent"
              ? `${API_URL} / mcp_skills_factory_agent | mcp_skills_isolated_agent | mcp_skills_static_agent`
              : `${API_URL} / ${assistantId}`}</p>
        </div>
        <div className="tabs">
          {Object.entries(ASSISTANTS).map(([id, item]) => (
            <button
              className={assistantId === id ? "tab activeTab" : "tab"}
              key={id}
              type="button"
              onClick={() => setAssistantId(id as keyof typeof ASSISTANTS)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </header>
      {assistantId === "sandbox_agent" ? (
        <SandboxPage />
      ) : assistantId === "hitl_agent" ? (
        <HitlPage />
      ) : assistantId === "dynamic_tools_agent" ? (
        <DynamicToolsPage />
      ) : assistantId === "mcp_skills_agent" ? (
        <McpSkillsPage />
      ) : assistantId === "graph_execution" ? (
        <GraphExecutionPage />
      ) : assistantId === "custom_stream_channels" ? (
        <CustomStreamChannelsPage />
      ) : assistantId === "tool_calling" ? (
        <ToolCallingPage />
      ) : assistantId === "headless_tools" ? (
        <HeadlessToolsPage />
      ) : assistantId === "custom_hitl" ? (
        <CustomHitlPage />
      ) : assistantId === "branching_chat" ? (
        <BranchingChatPage />
      ) : assistantId === "reasoning_tokens" ? (
        <ReasoningTokensPage />
      ) : assistantId === "structured_output" ? (
        <StructuredOutputPage />
      ) : assistantId === "message_queues" ? (
        <MessageQueuesPage />
      ) : assistantId === "join_rejoin" ? (
        <JoinRejoinPage />
      ) : assistantId === "time_travel" ? (
        <TimeTravelPage />
      ) : assistantId === "generative_ui" ? (
        <GenerativeUIPage />
      ) : assistantId === "frontend_integrations" ? (
        <FrontendIntegrationsPage />
      ) : assistantId === "integration_examples" ? (
        <IntegrationExamplesPage />
      ) : (
        <StreamPage key={assistantId} assistantId={assistantId} />
      )}
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
