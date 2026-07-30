from __future__ import annotations

from deepagents import create_deep_agent

from _model import get_real_model
from deepagent_src.agent_output import invoke_and_pretty_print


def main() -> None:
    agent = create_deep_agent(
        model=get_real_model(),
        system_prompt=(
            "You are a coordinator. For the user's request, delegate to the "
            "general-purpose subagent with the task tool and return its result."
        ),
    )
    result = invoke_and_pretty_print(
        agent,
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "请委派 general-purpose subagent 返回这句话："
                        "default-general-purpose-subagent-called"
                    ),
                }
            ]
        },
    )

    task_outputs = [
        getattr(message, "content", "")
        for message in result["messages"]
        if getattr(message, "name", "") == "task"
    ]

    assert any("default-general-purpose-subagent-called" in output for output in task_outputs)
    print("default general-purpose subagent real agent ok")


if __name__ == "__main__":
    main()

