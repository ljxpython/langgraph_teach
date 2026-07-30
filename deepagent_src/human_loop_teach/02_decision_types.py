from __future__ import annotations

from deepagents import create_deep_agent
from langchain.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from _hitl_output import print_graph_output, require_interrupt, tool_messages
from _model import get_real_model


@tool
def notify_email(to: str, subject: str, body: str) -> str:
    """Send an email."""
    return f"Sent email to {to} with subject {subject}: {body}"


@tool
def ask_user(question: str) -> str:
    """Ask the human user a question."""
    return f"tool-executed:{question}"


def build_agent():
    return create_deep_agent(
        model=get_real_model(),
        tools=[notify_email, ask_user],
        interrupt_on={
            "notify_email": {"allowed_decisions": ["approve", "edit", "reject"]},
            "ask_user": {"allowed_decisions": ["respond"]},
        },
        checkpointer=MemorySaver(),
        system_prompt=(
            "Call exactly the requested tool once. Do not use any other tools."
        ),
    )


def run_edit_case() -> None:
    agent = build_agent()
    config = {"configurable": {"thread_id": "hitl-decision-edit"}}
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "调用 notify_email，to=wrong@example.com，"
                        "subject=Demo，body=Hello"
                    ),
                }
            ]
        },
        config=config,
        version="v2",
    )
    print_graph_output(result)
    action = require_interrupt(result)["action_requests"][0]
    result = agent.invoke(
        Command(
            resume={
                "decisions": [
                    {
                        "type": "edit",
                        "edited_action": {
                            "name": action["name"],
                            "args": {
                                "to": "team@example.com",
                                "subject": "Demo",
                                "body": "Hello",
                            },
                        },
                    }
                ]
            }
        ),
        config=config,
        version="v2",
    )
    print_graph_output(result)
    assert any("team@example.com" in output for output in tool_messages(result, name="notify_email"))


def run_reject_case() -> None:
    agent = build_agent()
    config = {"configurable": {"thread_id": "hitl-decision-reject"}}
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "调用 notify_email，to=admin@example.com，subject=Risk，body=Stop",
                }
            ]
        },
        config=config,
        version="v2",
    )
    print_graph_output(result)
    require_interrupt(result)
    result = agent.invoke(
        Command(
            resume={
                "decisions": [
                    {
                        "type": "reject",
                        "message": "Human rejected sending this email. Do not retry.",
                    }
                ]
            }
        ),
        config=config,
        version="v2",
    )
    print_graph_output(result)
    assert not tool_messages(result, name="notify_email") or not any(
        output.startswith("Sent email") for output in tool_messages(result, name="notify_email")
    )


def run_respond_case() -> None:
    agent = build_agent()
    config = {"configurable": {"thread_id": "hitl-decision-respond"}}
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "调用 ask_user，question=继续吗？"}]},
        config=config,
        version="v2",
    )
    print_graph_output(result)
    require_interrupt(result)
    result = agent.invoke(
        Command(resume={"decisions": [{"type": "respond", "message": "继续"}]}),
        config=config,
        version="v2",
    )
    print_graph_output(result)
    assert any("继续" in output for output in tool_messages(result, name="ask_user"))
    assert not any("tool-executed" in output for output in tool_messages(result, name="ask_user"))


def main() -> None:
    run_edit_case()
    run_reject_case()
    run_respond_case()
    print("decision types HITL real agent ok")


if __name__ == "__main__":
    main()

