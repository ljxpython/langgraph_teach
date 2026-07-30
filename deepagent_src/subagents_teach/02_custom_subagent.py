from __future__ import annotations

from deepagents import create_deep_agent
from langchain.tools import tool

from _model import get_real_model
from deepagent_src.agent_output import invoke_and_pretty_print


@tool
def specialist_marker() -> str:
    """Return the specialist subagent marker."""
    return "custom-specialist-subagent-called"


specialist_subagent = {
    "name": "specialist",
    "description": "Use this subagent when the task asks for the specialist marker.",
    "system_prompt": (
        "You are the specialist subagent. Always call specialist_marker and "
        "return only the tool result."
    ),
    "tools": [specialist_marker],
}


def main() -> None:
    agent = create_deep_agent(
        model=get_real_model(),
        system_prompt=(
            "You are a coordinator. For specialist marker requests, call the "
            "task tool with subagent_type='specialist'."
        ),
        subagents=[specialist_subagent],
    )
    result = invoke_and_pretty_print(
        agent,
        {
            "messages": [
                {
                    "role": "user",
                    "content": "请委派 specialist subagent 获取 specialist marker。",
                }
            ]
        },
    )

    task_outputs = [
        getattr(message, "content", "")
        for message in result["messages"]
        if getattr(message, "name", "") == "task"
    ]

    assert any("custom-specialist-subagent-called" in output for output in task_outputs)
    print("custom subagent real agent ok")


if __name__ == "__main__":
    main()

