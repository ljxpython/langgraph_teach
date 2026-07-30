from __future__ import annotations

from deepagents import create_deep_agent
from langchain.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from _hitl_output import print_graph_output, require_interrupt, tool_messages
from _model import get_real_model


@tool
def delete_record(record_id: str) -> str:
    """Delete a record."""
    return f"Deleted record {record_id}"


@tool
def notify_email(to: str, subject: str) -> str:
    """Send a notification email."""
    return f"Sent notification to {to}: {subject}"


def main() -> None:
    agent = create_deep_agent(
        model=get_real_model(),
        tools=[delete_record, notify_email],
        interrupt_on={
            "delete_record": {"allowed_decisions": ["approve", "reject"]},
            "notify_email": {"allowed_decisions": ["approve", "reject"]},
        },
        checkpointer=MemorySaver(),
        system_prompt=(
            "When asked for the batch approval demo, call delete_record and "
            "notify_email in the same response. Do not call other tools."
        ),
    )
    config = {"configurable": {"thread_id": "hitl-multiple-tools"}}
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "批量审批演示：调用 delete_record(record_id=42)，"
                        "并调用 notify_email(to=admin@example.com, subject=Deleted)"
                    ),
                }
            ]
        },
        config=config,
        version="v2",
    )
    print_graph_output(result)
    interrupt_value = require_interrupt(result)
    actions = interrupt_value["action_requests"]
    assert [action["name"] for action in actions] == ["delete_record", "notify_email"]

    result = agent.invoke(
        Command(
            resume={
                "decisions": [
                    {"type": "approve"},
                    {
                        "type": "reject",
                        "message": "Human rejected sending notification email.",
                    },
                ]
            }
        ),
        config=config,
        version="v2",
    )
    print_graph_output(result)

    assert any("Deleted record 42" in output for output in tool_messages(result, name="delete_record"))
    assert not any(output.startswith("Sent notification") for output in tool_messages(result, name="notify_email"))
    print("multiple tool calls HITL real agent ok")


if __name__ == "__main__":
    main()

