from __future__ import annotations

from deepagents import HarnessProfile, create_deep_agent, register_harness_profile
from langchain.tools import tool

from _model import MODEL_PROFILE_KEY, get_real_model
from deepagent_src.agent_output import invoke_and_pretty_print


@tool
def visible_profile_tool() -> str:
    """Return the visible profile marker."""
    return "visible-profile-tool-called"


@tool
def hidden_profile_tool() -> str:
    """Return the hidden profile marker."""
    return "hidden-profile-tool-called"


def main() -> None:
    register_harness_profile(
        MODEL_PROFILE_KEY,
        HarnessProfile(
            tool_description_overrides={
                "visible_profile_tool": (
                    "Use this tool when the user asks for the visible profile marker."
                )
            },
            excluded_tools=frozenset({"hidden_profile_tool"}),
        ),
    )

    agent = create_deep_agent(
        model=get_real_model(),
        tools=[visible_profile_tool, hidden_profile_tool],
    )
    result = invoke_and_pretty_print(
        agent,
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "必须调用 visible_profile_tool，并只复述工具返回值。"
                    ),
                }
            ]
        },
    )

    tool_outputs = [
        getattr(message, "content", "")
        for message in result["messages"]
        if message.__class__.__name__ == "ToolMessage"
    ]

    assert any("visible-profile-tool-called" in output for output in tool_outputs)
    assert not any("hidden-profile-tool-called" in output for output in tool_outputs)
    print("tool visibility profile real agent ok")


if __name__ == "__main__":
    main()

