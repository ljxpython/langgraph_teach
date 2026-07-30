from __future__ import annotations

from deepagents import HarnessProfile, create_deep_agent, register_harness_profile

from _model import MODEL_PROFILE_KEY, get_real_model
from deepagent_src.agent_output import invoke_and_pretty_print


PROFILE_TOKEN = "PROFILE_SUFFIX_ACTIVE"


def main() -> None:
    register_harness_profile(
        MODEL_PROFILE_KEY,
        HarnessProfile(
            system_prompt_suffix=(
                "When the user asks for profile status, answer exactly "
                f"{PROFILE_TOKEN}."
            ),
        ),
    )

    agent = create_deep_agent(model=get_real_model())
    result = invoke_and_pretty_print(
        agent,
        {
            "messages": [
                {
                    "role": "user",
                    "content": "profile status",
                }
            ]
        },
    )

    assert PROFILE_TOKEN in result["messages"][-1].content
    print("harness prompt suffix real agent ok")


if __name__ == "__main__":
    main()

