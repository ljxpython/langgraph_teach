import asyncio
import json
import operator
from typing import Annotated
from uuid import uuid4

from langchain.messages import AIMessage, SystemMessage, ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolCallTransformer, ToolNode, tools_condition
from langgraph.stream import ProtocolEvent, StreamChannel, StreamTransformer
from langgraph.types import interrupt

from deepagent_src.llms import get_gpt_model


class GraphExecutionState(MessagesState):
    classification: str
    analysis: str
    synthesis: str
    execution_steps: Annotated[list[dict[str, str]], operator.add]


class ExecutionProgressTransformer(StreamTransformer):
    """将节点完成状态投影为前端可订阅的独立事件流。"""

    def __init__(self, scope: tuple[str, ...] = ()) -> None:
        super().__init__(scope)
        self.channel = StreamChannel("execution-progress")
        self.step_count = 0

    def init(self) -> dict[str, StreamChannel]:
        return {"executionProgress": self.channel}

    def process(self, event: ProtocolEvent) -> bool:
        if event.get("method") != "values":
            return True
        data = event.get("params", {}).get("data", {})
        if not isinstance(data, dict):
            return True
        steps = data.get("execution_steps", [])
        for step in steps[self.step_count :]:
            self.channel.push(
                {
                    "name": "execution-progress",
                    "payload": {"kind": "node_complete", **step},
                }
            )
        self.step_count = len(steps)
        return True


async def classify_node(state: GraphExecutionState) -> dict:
    await asyncio.sleep(0.4)
    request = str(state["messages"][-1].content)
    classification = "frontend" if "前端" in request else "general"
    return {
        "classification": classification,
        "messages": [AIMessage(content=f"分类完成：{classification}")],
        "execution_steps": [{"name": "classify", "output": f"分类完成：{classification}"}],
    }


async def analyze_node(state: GraphExecutionState) -> dict:
    await asyncio.sleep(0.4)
    analysis = f"分析分类 {state['classification']} 的执行状态与节点输出"
    return {
        "analysis": analysis,
        "messages": [AIMessage(content=analysis)],
        "execution_steps": [{"name": "analyze", "output": analysis}],
    }


async def synthesize_node(state: GraphExecutionState) -> dict:
    await asyncio.sleep(0.4)
    synthesis = f"执行完成：{state['analysis']}"
    return {
        "synthesis": synthesis,
        "messages": [AIMessage(content=synthesis)],
        "execution_steps": [{"name": "synthesize", "output": synthesis}],
    }


builder = StateGraph(GraphExecutionState)
builder.add_node("classify", classify_node)
builder.add_node("analyze", analyze_node)
builder.add_node("synthesize", synthesize_node)
builder.add_edge(START, "classify")
builder.add_edge("classify", "analyze")
builder.add_edge("analyze", "synthesize")
builder.add_edge("synthesize", END)

graph_execution = builder.compile(name="graph_execution")
custom_stream_channels = builder.compile(
    name="custom_stream_channels",
    transformers=[ExecutionProgressTransformer],
)


async def render_markdown_node(_state: MessagesState) -> dict:
    content = """# Markdown 渲染

Agent 消息可以包含 **粗体**、`行内代码` 和 [LangChain 文档](https://docs.langchain.com)。

- 普通列表
- ~~删除线~~
- [x] GFM 任务项

| 数据源 | 前端用途 |
| --- | --- |
| `messages` | 对话内容 |
| `values` | Graph state |

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

> 原始 HTML 默认不会执行：<script>window.markdownXss = true</script>
"""
    return {"messages": [AIMessage(content=content)]}


markdown_builder = StateGraph(MessagesState)
markdown_builder.add_node("render_markdown", render_markdown_node)
markdown_builder.add_edge(START, "render_markdown")
markdown_builder.add_edge("render_markdown", END)
markdown_messages = markdown_builder.compile(name="markdown_messages")


@tool
async def get_teaching_weather(city: str) -> dict[str, str | int]:
    """Get deterministic teaching weather for a city."""
    await asyncio.sleep(0.6)
    return {"city": city, "temperature": 24, "condition": "晴"}


weather_model = get_gpt_model(disable_tool_streaming=True).bind_tools(
    [get_teaching_weather]
)


async def call_weather_model(state: MessagesState) -> dict:
    response = await weather_model.ainvoke(
        [
            SystemMessage(
                content=(
                    "你是前端集成教学天气助手。用户查询天气时必须调用 "
                    "get_teaching_weather，并使用工具返回值给出简洁中文回答；"
                    "城市必须从用户消息中提取，禁止固定为上海。"
                )
            ),
            *state["messages"],
        ]
    )
    return {"messages": [response]}


tool_calling_builder = StateGraph(MessagesState)
tool_calling_builder.add_node("model", call_weather_model)
tool_calling_builder.add_node("tools", ToolNode([get_teaching_weather]))
tool_calling_builder.add_edge(START, "model")
tool_calling_builder.add_conditional_edges("model", tools_condition)
tool_calling_builder.add_edge("tools", "model")
tool_calling = tool_calling_builder.compile(
    name="tool_calling",
    transformers=[ToolCallTransformer],
)


openui_model = get_gpt_model(disable_tool_streaming=True).bind_tools(
    [get_teaching_weather]
)
OPENUI_SYSTEM_PROMPT = """你是 OpenUI 天气面板生成器。
用户查询天气时必须先调用 get_teaching_weather，城市必须来自用户消息。
拿到工具结果后，只输出可执行的 openui-lang 程序，不要 Markdown 代码围栏或解释。
仅使用 Stack、TextContent、Card、CardHeader；root 必须是第一行。示例：
root = Stack([title, cards], "column", "m")
title = TextContent("天气概览")
weather = Card([CardHeader("北京天气", "实时工具结果"), TextContent("24°C · 晴")])
cards = Stack([weather], "row", "m")
"""


async def call_openui_model(state: MessagesState) -> dict:
    response = await openui_model.ainvoke(
        [SystemMessage(content=OPENUI_SYSTEM_PROMPT), *state["messages"]]
    )
    return {"messages": [response]}


openui_integration_builder = StateGraph(MessagesState)
openui_integration_builder.add_node("model", call_openui_model)
openui_integration_builder.add_node("tools", ToolNode([get_teaching_weather]))
openui_integration_builder.add_edge(START, "model")
openui_integration_builder.add_conditional_edges("model", tools_condition)
openui_integration_builder.add_edge("tools", "model")
openui_integration = openui_integration_builder.compile(name="openui_integration")


@tool
def browser_memory_put(key: str, value: str, runtime: ToolRuntime) -> dict:
    """Store a teaching value in browser localStorage."""
    return interrupt(
        {
            "type": "tool",
            "tool_call": {
                "id": runtime.tool_call_id,
                "name": "browser_memory_put",
                "args": {"key": key, "value": value},
            },
        }
    )


async def request_browser_memory_node(state: MessagesState) -> dict:
    value = str(state["messages"][-1].content)
    return {
        "messages": [
            AIMessage(
                content="正在请求浏览器写入本地存储。",
                tool_calls=[
                    {
                        "name": "browser_memory_put",
                        "args": {"key": "lesson-12", "value": value},
                        "id": f"browser-memory-{uuid4()}",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    }


async def summarize_browser_memory_node(state: MessagesState) -> dict:
    result = next(
        message.content
        for message in reversed(state["messages"])
        if isinstance(message, ToolMessage)
    )
    return {"messages": [AIMessage(content=f"浏览器工具执行完成：{result}")]}


headless_tools_builder = StateGraph(MessagesState)
headless_tools_builder.add_node("request_browser_memory", request_browser_memory_node)
headless_tools_builder.add_node("tools", ToolNode([browser_memory_put]))
headless_tools_builder.add_node("summarize_browser_memory", summarize_browser_memory_node)
headless_tools_builder.add_edge(START, "request_browser_memory")
headless_tools_builder.add_edge("request_browser_memory", "tools")
headless_tools_builder.add_edge("tools", "summarize_browser_memory")
headless_tools_builder.add_edge("summarize_browser_memory", END)
headless_tools = headless_tools_builder.compile(
    name="headless_tools",
    transformers=[ToolCallTransformer],
)


@tool
def review_refund(order_id: str, amount: float, reason: str) -> dict:
    """Review a teaching refund with a custom frontend form."""
    decision = interrupt(
        {
            "form_type": "refund_approval",
            "title": "审核退款申请",
            "context": {"order_id": order_id, "amount": amount, "reason": reason},
            "fields": [
                {"name": "amount", "label": "退款金额", "type": "currency"},
                {"name": "note", "label": "审核备注", "type": "textarea"},
            ],
        }
    )
    if not isinstance(decision, dict) or decision.get("approved") is not True:
        return {
            "status": "declined",
            "order_id": order_id,
            "requested_amount": amount,
            "reason": reason,
        }

    values = decision.get("values", {})
    approved_amount = float(values.get("amount", amount))
    if approved_amount <= 0:
        raise ValueError("approved refund amount must be positive")
    return {
        "status": "approved",
        "order_id": order_id,
        "amount": approved_amount,
        "note": str(values.get("note", "")),
        "requested_amount": amount,
        "reason": reason,
    }


async def request_refund_review_node(state: MessagesState) -> dict:
    reason = str(state["messages"][-1].content)
    return {
        "messages": [
            AIMessage(
                content="退款申请需要人工审核。",
                tool_calls=[
                    {
                        "name": "review_refund",
                        "args": {
                            "order_id": "ORDER-2026-0713",
                            "amount": 188.0,
                            "reason": reason,
                        },
                        "id": f"refund-review-{uuid4()}",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    }


async def summarize_refund_review_node(state: MessagesState) -> dict:
    result = next(
        message.content
        for message in reversed(state["messages"])
        if isinstance(message, ToolMessage)
    )
    payload = json.loads(str(result))
    approved = payload["status"] == "approved"
    decision = {"approved": approved}
    if approved:
        decision["values"] = {
            "amount": payload["amount"],
            "note": payload["note"],
        }
    card = {
        "form_type": "refund_approval",
        "title": "审核退款申请",
        "context": {
            "order_id": payload["order_id"],
            "amount": payload["requested_amount"],
            "reason": payload["reason"],
        },
        "fields": [
            {"name": "amount", "label": "退款金额", "type": "currency"},
            {"name": "note", "label": "审核备注", "type": "textarea"},
        ],
        "resolved": True,
        "decision": decision,
    }
    return {
        "messages": [
            AIMessage(
                content=f"退款审核流程完成：{result}",
                response_metadata={"review_card": card},
            )
        ]
    }


custom_hitl_builder = StateGraph(MessagesState)
custom_hitl_builder.add_node("request_refund_review", request_refund_review_node)
custom_hitl_builder.add_node("tools", ToolNode([review_refund]))
custom_hitl_builder.add_node("summarize_refund_review", summarize_refund_review_node)
custom_hitl_builder.add_edge(START, "request_refund_review")
custom_hitl_builder.add_edge("request_refund_review", "tools")
custom_hitl_builder.add_edge("tools", "summarize_refund_review")
custom_hitl_builder.add_edge("summarize_refund_review", END)
custom_hitl = custom_hitl_builder.compile(
    name="custom_hitl",
    transformers=[ToolCallTransformer],
)


async def branching_reply_node(state: MessagesState) -> dict:
    prompt = next(
        message.content
        for message in reversed(state["messages"])
        if message.type == "human"
    )
    variant = uuid4().hex[:6]
    return {"messages": [AIMessage(content=f"分支回答 [{variant}]：{prompt}")]}


branching_chat_builder = StateGraph(MessagesState)
branching_chat_builder.add_node("reply", branching_reply_node)
branching_chat_builder.add_edge(START, "reply")
branching_chat_builder.add_edge("reply", END)
branching_chat = branching_chat_builder.compile(name="branching_chat")


async def reasoning_tokens_node(state: MessagesState) -> dict:
    prompt = next(
        message.content
        for message in reversed(state["messages"])
        if message.type == "human"
    )
    return {
        "messages": [
            AIMessage(
                content_blocks=[
                    {
                        "type": "reasoning",
                        "reasoning": (
                            "先识别用户问题，再区分推理过程与面向用户的最终回答，"
                            "最后用标准 content blocks 返回两部分内容。"
                        ),
                    },
                    {
                        "type": "text",
                        "text": f"最终回答：已使用独立内容块处理“{prompt}”。",
                    },
                ]
            )
        ]
    }


reasoning_tokens_builder = StateGraph(MessagesState)
reasoning_tokens_builder.add_node("reply", reasoning_tokens_node)
reasoning_tokens_builder.add_edge(START, "reply")
reasoning_tokens_builder.add_edge("reply", END)
reasoning_tokens = reasoning_tokens_builder.compile(name="reasoning_tokens")


async def structured_output_node(state: MessagesState) -> dict:
    topic = str(state["messages"][-1].content)
    plan = {
        "topic": topic,
        "level": "intermediate",
        "objectives": [
            "识别结构化响应的 tool call",
            "在渲染前验证 tool arguments",
        ],
        "lessons": [
            {"title": "定义响应 schema", "duration_minutes": 20},
            {"title": "提取并验证 args", "duration_minutes": 25},
            {"title": "渲染领域组件", "duration_minutes": 30},
        ],
        "total_minutes": 75,
    }
    return {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "render_learning_plan",
                        "args": plan,
                        "id": f"learning-plan-{uuid4()}",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    }


structured_output_builder = StateGraph(MessagesState)
structured_output_builder.add_node("reply", structured_output_node)
structured_output_builder.add_edge(START, "reply")
structured_output_builder.add_edge("reply", END)
structured_output = structured_output_builder.compile(name="structured_output")


async def message_queues_node(state: MessagesState) -> dict:
    await asyncio.sleep(1.2)
    prompt = next(
        message.content
        for message in reversed(state["messages"])
        if message.type == "human"
    )
    return {"messages": [AIMessage(content=f"已处理：{prompt}")]}


message_queues_builder = StateGraph(MessagesState)
message_queues_builder.add_node("reply", message_queues_node)
message_queues_builder.add_edge(START, "reply")
message_queues_builder.add_edge("reply", END)
message_queues = message_queues_builder.compile(name="message_queues")


async def join_rejoin_node(state: MessagesState) -> dict:
    await asyncio.sleep(2.5)
    prompt = next(
        message.content
        for message in reversed(state["messages"])
        if message.type == "human"
    )
    return {"messages": [AIMessage(content=f"后台运行完成：{prompt}")]}


join_rejoin_builder = StateGraph(MessagesState)
join_rejoin_builder.add_node("reply", join_rejoin_node)
join_rejoin_builder.add_edge(START, "reply")
join_rejoin_builder.add_edge("reply", END)
join_rejoin = join_rejoin_builder.compile(name="join_rejoin")


class TimeTravelState(MessagesState):
    draft: str


async def time_travel_draft_node(state: TimeTravelState) -> dict:
    prompt = next(
        message.content
        for message in reversed(state["messages"])
        if message.type == "human"
    )
    return {"draft": f"草稿：{prompt}"}


async def time_travel_finalize_node(state: TimeTravelState) -> dict:
    variant = uuid4().hex[:6]
    return {
        "messages": [AIMessage(content=f"最终版本 [{variant}]：{state['draft']}")]
    }


time_travel_builder = StateGraph(TimeTravelState)
time_travel_builder.add_node("draft", time_travel_draft_node)
time_travel_builder.add_node("finalize", time_travel_finalize_node)
time_travel_builder.add_edge(START, "draft")
time_travel_builder.add_edge("draft", "finalize")
time_travel_builder.add_edge("finalize", END)
time_travel = time_travel_builder.compile(name="time_travel")


async def generative_ui_node(state: MessagesState) -> dict:
    prompt = next(
        message.content
        for message in reversed(state["messages"])
        if message.type == "human"
    )
    spec = {
        "root": "dashboard",
        "elements": {
            "dashboard": {
                "type": "Card",
                "props": {
                    "title": "Agent 运行概览",
                    "description": str(prompt),
                },
                "children": ["metrics", "steps"],
            },
            "metrics": {
                "type": "Stack",
                "props": {"direction": "horizontal"},
                "children": ["runs", "success"],
            },
            "runs": {
                "type": "Metric",
                "props": {"label": "今日运行", "value": "24"},
                "children": [],
            },
            "success": {
                "type": "Metric",
                "props": {"label": "成功率", "value": "96%"},
                "children": [],
            },
            "steps": {
                "type": "List",
                "props": {
                    "title": "最近步骤",
                    "items": ["读取上下文", "执行工具", "生成结果"],
                },
                "children": [],
            },
        },
    }
    return {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "render_ui",
                        "args": spec,
                        "id": f"generative-ui-{uuid4()}",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    }


generative_ui_builder = StateGraph(MessagesState)
generative_ui_builder.add_node("generate_ui", generative_ui_node)
generative_ui_builder.add_edge(START, "generate_ui")
generative_ui_builder.add_edge("generate_ui", END)
generative_ui = generative_ui_builder.compile(name="generative_ui")
