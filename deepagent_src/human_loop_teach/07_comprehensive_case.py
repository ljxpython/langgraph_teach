from __future__ import annotations

from deepagents import FilesystemPermission, create_deep_agent
from langchain.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from _hitl_output import print_graph_output, require_interrupt
from _model import get_real_model


@tool
def notify_email(to: str, subject: str, body: str) -> str:
    """Send an email."""
    return f"Sent email to {to} with subject {subject}: {body}"


def ask_terminal_decisions(interrupt_value: dict) -> list[dict]:
    review_configs = {
        config["action_name"]: config
        for config in interrupt_value.get("review_configs", [])
    }
    decisions = []
    for action in interrupt_value["action_requests"]:
        allowed = review_configs[action["name"]]["allowed_decisions"]
        choices = [choice for choice in ("approve", "edit", "reject") if choice in allowed]

        print("\n需要人工审核：")
        print(f"tool: {action['name']}")
        print(f"args: {action['args']}")
        print(f"可选: {', '.join(choices)}")

        while True:
            decision_type = input("请输入决策: ").strip()
            if decision_type in choices:
                break
            print("输入不合法，重新输。")

        if decision_type == "approve":
            decisions.append({"type": "approve"})
            continue

        if decision_type == "reject":
            message = input("拒绝原因（回车用默认）: ").strip()
            decisions.append(
                {
                    "type": "reject",
                    "message": message or f"Human rejected {action['name']}. Do not retry.",
                }
            )
            continue

        edited_args = {}
        for key, value in action["args"].items():
            new_value = input(f"{key} [{value}]: ").strip()
            edited_args[key] = new_value or value
        decisions.append(
            {
                "type": "edit",
                "edited_action": {"name": action["name"], "args": edited_args},
            }
        )

    return decisions


def main() -> None:
    agent = create_deep_agent(
        model=get_real_model(),
        tools=[notify_email],
        interrupt_on={
            "notify_email": {"allowed_decisions": ["approve", "edit", "reject"]},
        },
        permissions=[
            FilesystemPermission(
                operations=["write"],
                paths=["/secrets/**"],
                mode="interrupt",
            )
        ],
        checkpointer=MemorySaver(),
        system_prompt=(
            "For the comprehensive HITL demo, call exactly the requested tool "
            "once. Do not call other tools."
        ),
    )

    email_config = {"configurable": {"thread_id": "hitl-comprehensive-email"}}
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "调用 notify_email(to=wrong@example.com, subject=Deploy, body=Ready)",
                }
            ]
        },
        config=email_config,
        version="v2",
    )
    print_graph_output(result)
    interrupt_value = require_interrupt(result)
    action = interrupt_value["action_requests"][0]
    assert action["name"] == "notify_email"

    result = agent.invoke(
        Command(resume={"decisions": ask_terminal_decisions(interrupt_value)}),
        config=email_config,
        version="v2",
    )
    print_graph_output(result)

    file_config = {"configurable": {"thread_id": "hitl-comprehensive-file"}}
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "把内容 demo 写入 /secrets/deploy.txt"}]},
        config=file_config,
        version="v2",
    )
    print_graph_output(result)
    interrupt_value = require_interrupt(result)
    action = interrupt_value["action_requests"][0]
    assert action["name"] == "write_file"

    result = agent.invoke(
        Command(resume={"decisions": ask_terminal_decisions(interrupt_value)}),
        config=file_config,
        version="v2",
    )
    print_graph_output(result)

    print("interactive comprehensive HITL demo completed")


if __name__ == "__main__":
    main()
