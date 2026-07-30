from __future__ import annotations

from typing import get_type_hints

from deepagents import DeepAgentState, create_deep_agent
from langchain.tools import ToolRuntime, tool

from _model import get_real_model
from deepagent_src.agent_output import invoke_and_pretty_print


class ResearchState(DeepAgentState):
    page_url: str
    file_urls: list[str]


@tool
def cite_page(runtime: ToolRuntime) -> str:
    """Return the page URL stored in mutable agent state."""
    return runtime.state["page_url"]


def main() -> None:
    agent = create_deep_agent(
        model=get_real_model(),
        tools=[cite_page],
        state_schema=ResearchState,
    )

    result = invoke_and_pretty_print(
        agent,
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "必须调用 cite_page 工具读取当前页面 URL，"
                        "然后只输出这个 URL。"
                    ),
                }
            ],
            "page_url": "https://example.com/report",
            "file_urls": [],
        }
    )

    state_hints = get_type_hints(ResearchState)
    tool_outputs = [
        getattr(message, "content", "")
        for message in result["messages"]
        if message.__class__.__name__ == "ToolMessage"
    ]

    assert state_hints["page_url"] is str
    assert state_hints["file_urls"] == list[str]
    assert any("https://example.com/report" in output for output in tool_outputs)
    print("custom state schema real agent ok")


if __name__ == "__main__":
    main()
