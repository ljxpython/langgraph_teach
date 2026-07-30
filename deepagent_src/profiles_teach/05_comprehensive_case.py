from __future__ import annotations

from deepagents import (
    GeneralPurposeSubagentProfile,
    HarnessProfile,
    ProviderProfile,
    create_deep_agent,
    register_harness_profile,
    register_provider_profile,
)
from deepagents.profiles.provider.provider_profiles import apply_provider_profile
from langchain.tools import tool

from _model import MODEL_PROFILE_KEY, get_real_model
from deepagent_src.agent_output import invoke_and_pretty_print


@tool
def profile_summary_tool() -> str:
    """Return the profile summary marker."""
    return "profiles connect harness behavior and provider construction"


def main() -> None:
    register_provider_profile(
        "profiledemo",
        ProviderProfile(init_kwargs={"temperature": 0}),
    )
    register_provider_profile(
        "profiledemo:lesson",
        ProviderProfile(init_kwargs={"timeout": 8}),
    )
    provider_kwargs = apply_provider_profile(
        "profiledemo:lesson",
        {"timeout": 3},
        run_pre_init=False,
    )

    register_harness_profile(
        MODEL_PROFILE_KEY,
        HarnessProfile(
            system_prompt_suffix="Keep the final answer to one sentence.",
            tool_description_overrides={
                "profile_summary_tool": "Use this for the profiles lesson summary."
            },
            excluded_tools=frozenset({"execute"}),
            general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
        ),
    )

    agent = create_deep_agent(model=get_real_model(), tools=[profile_summary_tool])
    result = invoke_and_pretty_print(
        agent,
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "必须调用 profile_summary_tool，"
                        "然后用一句中文总结工具返回值。"
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

    assert provider_kwargs["temperature"] == 0
    assert provider_kwargs["timeout"] == 3
    assert any("profiles connect harness behavior" in output for output in tool_outputs)
    print("profiles comprehensive real agent ok")


if __name__ == "__main__":
    main()

