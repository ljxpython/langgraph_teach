from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallRequest, wrap_tool_call
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool

tool_events: list[str] = []


class ToolCallingFakeModel(FakeMessagesListChatModel):
    def bind_tools(
        self,
        tools: Any,
        *,
        tool_choice: Any = None,
        **kwargs: Any,
    ) -> ToolCallingFakeModel:
        return self


@tool
def add_one(value: int) -> str:
    """Add one to a number."""
    return str(value + 1)


@wrap_tool_call(name="audit_tool_call")
def audit_tool_call(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage],
) -> ToolMessage:
    tool_events.append(f"before:{request.tool_call['name']}:{request.tool_call['args']}")
    result = handler(request)
    tool_events.append(f"after:{result.content}")
    return ToolMessage(
        content=f"AUDITED:{result.content}",
        tool_call_id=request.tool_call["id"],
        name=request.tool_call["name"],
    )


def main() -> None:
    tool_events.clear()
    model = ToolCallingFakeModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "add_one",
                        "args": {"value": 2},
                        "id": "call_1",
                    }
                ],
            ),
            AIMessage(content="TOOL_DONE"),
        ]
    )
    agent = create_agent(
        model=model,
        tools=[add_one],
        middleware=[audit_tool_call],
    )
    state = agent.invoke({"messages": [{"role": "user", "content": "run tool"}]})

    tool_messages = [message for message in state["messages"] if message.type == "tool"]
    final_text = state["messages"][-1].text

    print("tool_events:", tool_events)
    print("tool_message:", tool_messages[0].text)
    print("final:", final_text)

    assert tool_events == ["before:add_one:{'value': 2}", "after:3"], tool_events
    assert tool_messages[0].text == "AUDITED:3", tool_messages[0].text
    assert final_text == "TOOL_DONE", final_text
    print("wrap_tool_call local check ok")


if __name__ == "__main__":
    main()
