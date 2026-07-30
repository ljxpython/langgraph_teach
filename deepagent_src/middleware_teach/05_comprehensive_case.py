from __future__ import annotations

from collections.abc import Callable
from time import sleep

from deepagents import create_deep_agent
from langchain.agents.middleware import (
    ModelRequest,
    ModelResponse,
    ToolCallRequest,
    wrap_model_call,
    wrap_tool_call,
)
from langchain.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool

from deepagent_src.llms import get_gpt_model

model_events: list[str] = []
tool_events: list[str] = []


@tool
def lookup_invoice(invoice_id: str) -> str:
    """Look up an invoice by invoice id."""
    if invoice_id != "mw-5001":
        return f"invoice {invoice_id} not found"
    return "invoice mw-5001 total is 88 USD"


@wrap_model_call(name="record_model_call")
def record_model_call(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    model_events.append(f"model_call:{len(request.state['messages'])}")
    for attempt in range(3):
        try:
            return handler(request)
        except Exception as exc:
            model_events.append(f"retry:{attempt + 1}:{type(exc).__name__}")
            if attempt == 2:
                raise
            sleep(1)
    raise AssertionError("unreachable")


@wrap_tool_call(name="audit_invoice_tool")
def audit_invoice_tool(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage],
) -> ToolMessage:
    tool_events.append(f"before:{request.tool_call['name']}:{request.tool_call['args']}")
    result = handler(request)
    tool_events.append(f"after:{result.content}")
    return ToolMessage(
        content=f"AUDITED_TOOL:{result.content}",
        tool_call_id=request.tool_call["id"],
        name=request.tool_call["name"],
    )


def main() -> None:
    model_events.clear()
    tool_events.clear()

    agent = create_deep_agent(
        model=get_gpt_model(disable_tool_streaming=True),
        tools=[lookup_invoice],
        middleware=[record_model_call, audit_invoice_tool],
        subagents=[],
        system_prompt=(
            "你是 middleware 综合案例助手。"
            "必须调用 lookup_invoice，invoice_id 必须是 mw-5001。"
            "看到工具结果后，只回复 `MIDDLEWARE_CASE_OK: <工具结果>`。"
        ),
    )
    state = agent.invoke({"messages": [HumanMessage(content="查询教学发票。")]})
    messages = state["messages"]
    tool_messages = [message for message in messages if message.type == "tool"]
    final_text = messages[-1].text

    print("model_events:", model_events)
    print("tool_events:", tool_events)
    print("tool_message:", tool_messages[-1].text)
    print("final:", final_text)

    assert len(model_events) >= 2, model_events
    assert tool_events == [
        "before:lookup_invoice:{'invoice_id': 'mw-5001'}",
        "after:invoice mw-5001 total is 88 USD",
    ], tool_events
    assert tool_messages[-1].text == "AUDITED_TOOL:invoice mw-5001 total is 88 USD"
    assert "MIDDLEWARE_CASE_OK" in final_text, final_text
    assert "mw-5001" in final_text and "88 USD" in final_text, final_text
    print("middleware comprehensive real call ok")


if __name__ == "__main__":
    main()
