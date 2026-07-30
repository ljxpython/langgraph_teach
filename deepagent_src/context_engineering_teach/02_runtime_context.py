from __future__ import annotations

from dataclasses import dataclass

from deepagents import create_deep_agent
from langchain.tools import ToolRuntime, tool

from _model import get_real_model
from deepagent_src.agent_output import invoke_and_pretty_print


@dataclass
class RunContext:
    user_id: str
    role: str


@tool
def current_user_note(query: str, runtime: ToolRuntime[RunContext]) -> str:
    """Return a note scoped to the invoking user."""
    return f"{runtime.context.user_id}:{runtime.context.role}:{query}"


def main() -> None:
    agent = create_deep_agent(
        model=get_real_model(),
        tools=[current_user_note],
        context_schema=RunContext,
    )

    result = invoke_and_pretty_print(
        agent,
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "必须调用 current_user_note 工具，query 参数填 recent activity，"
                        "然后只用一句话复述工具结果。"
                    ),
                }
            ]
        },
        context=RunContext(user_id="u-123", role="readonly"),
    )

    tool_outputs = [
        getattr(message, "content", "")
        for message in result["messages"]
        if message.__class__.__name__ == "ToolMessage"
    ]

    assert any("u-123:readonly:recent activity" in output for output in tool_outputs)
    print("runtime context real agent ok")


if __name__ == "__main__":
    main()
