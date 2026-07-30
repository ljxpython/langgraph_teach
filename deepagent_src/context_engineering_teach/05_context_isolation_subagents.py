from __future__ import annotations

from dataclasses import dataclass

from deepagents import create_deep_agent
from langchain.tools import ToolRuntime, tool

from _model import get_real_model
from deepagent_src.agent_output import invoke_and_pretty_print


@dataclass
class RunContext:
    user_id: str
    thread_id: str


@tool
def get_user_marker(runtime: ToolRuntime[RunContext]) -> str:
    """Return the user marker from runtime context."""
    return f"{runtime.context.user_id}@{runtime.context.thread_id}"


research_subagent = {
    "name": "researcher",
    "description": "Do heavy research and return only a concise summary.",
    "system_prompt": "Keep the final answer under 120 words. Do not return raw tool logs.",
    "tools": [get_user_marker],
}


def main() -> None:
    agent = create_deep_agent(
        model=get_real_model(),
        subagents=[research_subagent],
        context_schema=RunContext,
    )
    result = invoke_and_pretty_print(
        agent,
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "把任务交给 researcher subagent。"
                        "要求 subagent 调用 get_user_marker 工具，并返回工具结果。"
                    ),
                }
            ]
        },
        context=RunContext(user_id="u-123", thread_id="t-1"),
    )

    assert agent is not None
    assert research_subagent["tools"] == [get_user_marker]
    assert "u-123@t-1" in result["messages"][-1].content
    print("context isolation subagent real agent ok")


if __name__ == "__main__":
    main()
