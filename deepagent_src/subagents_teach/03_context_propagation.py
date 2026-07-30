from __future__ import annotations

from dataclasses import dataclass

from deepagents import create_deep_agent
from langchain.tools import ToolRuntime, tool

from _model import get_real_model
from deepagent_src.agent_output import invoke_and_pretty_print


@dataclass
class UserContext:
    user_id: str
    session_id: str


@tool
def read_context_marker(runtime: ToolRuntime[UserContext]) -> str:
    """Return the runtime context marker visible inside a subagent."""
    return f"{runtime.context.user_id}@{runtime.context.session_id}"


context_subagent = {
    "name": "context-reader",
    "description": "Use this subagent to read runtime context through a tool.",
    "system_prompt": (
        "You are the context-reader subagent. Always call read_context_marker "
        "and return only the tool result."
    ),
    "tools": [read_context_marker],
}


def main() -> None:
    agent = create_deep_agent(
        model=get_real_model(),
        system_prompt=(
            "You are a coordinator. Delegate context checks to context-reader."
        ),
        subagents=[context_subagent],
        context_schema=UserContext,
    )
    result = invoke_and_pretty_print(
        agent,
        {
            "messages": [
                {
                    "role": "user",
                    "content": "请委派 context-reader subagent 读取 runtime context。",
                }
            ]
        },
        context=UserContext(user_id="user-123", session_id="session-abc"),
    )

    task_outputs = [
        getattr(message, "content", "")
        for message in result["messages"]
        if getattr(message, "name", "") == "task"
    ]

    assert any("user-123@session-abc" in output for output in task_outputs)
    print("subagent context propagation real agent ok")


if __name__ == "__main__":
    main()

