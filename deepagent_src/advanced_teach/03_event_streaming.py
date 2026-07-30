from __future__ import annotations

import os
from typing import Any

from deepagents import create_deep_agent
from langchain.messages import HumanMessage
from langchain_core.tools import tool

from deepagent_src.llms import get_gpt_model


@tool
def echo_topic(topic: str) -> str:
    """Echo a short topic for event streaming teaching."""
    return f"工具已收到主题: {topic}"


def message_text(message: Any) -> str:
    text = getattr(message, "text", None)
    if isinstance(text, str):
        return text
    content = getattr(message, "content", "")
    return content if isinstance(content, str) else str(content)


def collect_stream_events() -> dict[str, Any]:
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

    agent = create_deep_agent(
        model=get_gpt_model(disable_tool_streaming=True),
        tools=[echo_topic],
        subagents=[],
        system_prompt=(
            "你是 Deep Agents Event Streaming 教学助手。必须先调用 echo_topic 工具，"
            "topic 填 event streaming，然后用一句中文回答。最终回答必须包含：event streaming 前端。"
        ),
    )

    stream = agent.stream_events(
        {
            "messages": [
                HumanMessage(
                    content="请调用工具，然后说明 event streaming 能给前端带来什么。"
                )
            ]
        },
        version="v3",
    )

    methods: list[str] = []
    tool_calls: list[str] = []
    tool_results: list[str] = []
    final_text = ""

    for event in stream:
        method = event.get("method")
        if method:
            methods.append(method)

        params = event.get("params", {})
        data = params.get("data")

        if method == "messages" and isinstance(data, tuple):
            message = data[0]
            for call in getattr(message, "tool_calls", None) or []:
                tool_calls.append(call.get("name", ""))
            text = message_text(message)
            if text:
                final_text = text

        if method == "tools" and isinstance(data, dict):
            if data.get("event") == "tool-finished":
                output = data.get("output")
                tool_results.append(message_text(output))

    output = stream.output or {}
    return {
        "methods": methods,
        "tool_calls": tool_calls,
        "tool_results": tool_results,
        "final_text": final_text,
        "message_count": len(output.get("messages", [])),
    }


def main() -> None:
    result = collect_stream_events()
    print("methods:", ", ".join(result["methods"]))
    print("tool_calls:", ", ".join(result["tool_calls"]))
    print("tool_results:", " | ".join(result["tool_results"]))
    print("final:", result["final_text"])
    print("message_count:", result["message_count"])

    assert "messages" in result["methods"], result
    assert "tools" in result["methods"], result
    assert "values" in result["methods"], result
    assert "echo_topic" in result["tool_calls"], result
    assert any("event streaming" in item for item in result["tool_results"]), result
    assert "event streaming" in result["final_text"].lower(), result
    assert "前端" in result["final_text"], result
    assert result["message_count"] >= 3, result
    print("event streaming real call ok")


if __name__ == "__main__":
    main()
