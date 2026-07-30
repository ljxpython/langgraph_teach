from __future__ import annotations

import os
from typing import Any

from deepagents import create_deep_agent
from langchain.agents.middleware import ToolErrorMiddleware
from langchain.messages import HumanMessage
from langchain_core.tools import tool

from deepagent_src.llms import get_gpt_model


@tool
def lookup_invoice(invoice_id: str) -> str:
    """Look up an invoice by invoice id."""
    if invoice_id != "inv_1001":
        raise ValueError("invoice_id must be inv_1001 for this demo")
    return "invoice inv_1001 total is 42 USD"


def recover_tool_error(exc: Exception, request: Any) -> str | None:
    if not isinstance(exc, ValueError):
        return None
    tool_call = getattr(request, "tool_call", {})
    tool_name = tool_call.get("name", "unknown_tool")
    return (
        f"Tool `{tool_name}` failed: {exc}. "
        "Retry with invoice_id=inv_1001."
    )


def tool_call_args(messages: list[Any]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for message in messages:
        for call in getattr(message, "tool_calls", None) or []:
            calls.append({"name": call.get("name", ""), "args": call.get("args", {})})
    return calls


def main() -> None:
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

    agent = create_deep_agent(
        model=get_gpt_model(disable_tool_streaming=True),
        tools=[lookup_invoice],
        middleware=[ToolErrorMiddleware(recover_tool_error)],
        subagents=[],
        system_prompt=(
            "你是 Fault Tolerance 教学助手。必须先调用 lookup_invoice，"
            "第一次 invoice_id 填 bad-id。"
            "如果工具返回错误消息，必须按错误消息修正参数重试。"
            "最终用一句中文回答，必须包含 inv_1001 和 42 USD。"
        ),
    )

    state = agent.invoke({"messages": [HumanMessage(content="查询教学发票。")]})
    messages = state["messages"]

    for message in messages:
        message.pretty_print()

    calls = tool_call_args(messages)
    invoice_ids = [call["args"].get("invoice_id") for call in calls]
    tool_messages = [message.text for message in messages if message.type == "tool"]
    final_text = messages[-1].text

    assert invoice_ids == ["bad-id", "inv_1001"], calls
    assert any("Retry with invoice_id=inv_1001" in item for item in tool_messages)
    assert any("invoice inv_1001 total is 42 USD" in item for item in tool_messages)
    assert "inv_1001" in final_text, final_text
    assert "42 USD" in final_text, final_text
    print("fault tolerance tool error recovery real call ok")


if __name__ == "__main__":
    main()
