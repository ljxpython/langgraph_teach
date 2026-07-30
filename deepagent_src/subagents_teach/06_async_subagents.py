from __future__ import annotations

from deepagents import AsyncSubAgent, create_deep_agent

from _model import get_real_model
from deepagent_src.agent_output import invoke_and_pretty_print


async_researcher: AsyncSubAgent = {
    "name": "async-researcher",
    "description": "Background research agent for long-running work.",
    "graph_id": "researcher",
}


def main() -> None:
    agent = create_deep_agent(
        model=get_real_model(),
        system_prompt=(
            "You are a supervisor. For async status requests, call "
            "list_async_tasks."
        ),
        subagents=[async_researcher],
    )
    result = invoke_and_pretty_print(
        agent,
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "必须调用 list_async_tasks 工具查看当前异步任务列表，"
                        "然后只复述工具结果。"
                    ),
                }
            ]
        },
    )

    tool_outputs = [
        getattr(message, "content", "")
        for message in result["messages"]
        if getattr(message, "name", "") == "list_async_tasks"
    ]

    assert async_researcher["graph_id"] == "researcher"
    assert any("No async subagent tasks tracked" in output for output in tool_outputs)
    print("async subagent tool real agent ok")


if __name__ == "__main__":
    main()

