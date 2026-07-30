from __future__ import annotations

from deepagents import (
    GeneralPurposeSubagentProfile,
    HarnessProfile,
    create_deep_agent,
    register_harness_profile,
)

from _model import MODEL_PROFILE_KEY, get_real_model
from deepagent_src.agent_output import invoke_and_pretty_print


def main() -> None:
    register_harness_profile(
        MODEL_PROFILE_KEY,
        HarnessProfile(
            general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
        ),
    )

    agent = create_deep_agent(
        model=get_real_model(),
        system_prompt="Answer directly. No synchronous subagents are available.",
    )
    result = invoke_and_pretty_print(
        agent,
        {
            "messages": [
                {
                    "role": "user",
                    "content": "用一句中文回答：当前没有同步 subagent 时会怎样？",
                }
            ]
        },
    )

    assert result["messages"][-1].content
    assert not any(getattr(message, "name", "") == "task" for message in result["messages"])
    print("disable synchronous subagents real agent ok")


if __name__ == "__main__":
    main()

