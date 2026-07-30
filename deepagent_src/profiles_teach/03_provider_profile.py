from __future__ import annotations

from deepagents import ProviderProfile, create_deep_agent, register_provider_profile
from deepagents.profiles.provider.provider_profiles import apply_provider_profile
from langchain.tools import tool

from _model import get_real_model
from deepagent_src.agent_output import invoke_and_pretty_print


DEMO_PROVIDER_KEY = "profiledemo"
DEMO_MODEL_SPEC = "profiledemo:tiny"


@tool
def provider_profile_note() -> str:
    """Return the ProviderProfile lesson note."""
    return "ProviderProfile controls model construction kwargs."


def main() -> None:
    register_provider_profile(
        DEMO_PROVIDER_KEY,
        ProviderProfile(init_kwargs={"temperature": 0, "timeout": 30}),
    )
    register_provider_profile(
        DEMO_MODEL_SPEC,
        ProviderProfile(init_kwargs={"timeout": 5}),
    )

    merged_kwargs = apply_provider_profile(DEMO_MODEL_SPEC, run_pre_init=False)

    agent = create_deep_agent(model=get_real_model(), tools=[provider_profile_note])
    result = invoke_and_pretty_print(
        agent,
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "必须调用 provider_profile_note，"
                        "然后用一句中文复述工具返回值。"
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

    assert merged_kwargs["temperature"] == 0
    assert merged_kwargs["timeout"] == 5
    assert any("model construction kwargs" in output for output in tool_outputs)
    print("provider profile merge plus real agent ok")


if __name__ == "__main__":
    main()
