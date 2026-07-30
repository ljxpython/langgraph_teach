from __future__ import annotations

import json
from pathlib import Path

from deepagents import (
    GeneralPurposeSubagentProfile,
    HarnessProfileConfig,
    create_deep_agent,
    register_harness_profile,
)

from _model import MODEL_PROFILE_KEY, get_real_model
from deepagent_src.agent_output import invoke_and_pretty_print


ROOT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = ROOT_DIR / "workspace" / "openai_profile.json"


def main() -> None:
    config = HarnessProfileConfig.from_dict(json.loads(CONFIG_PATH.read_text()))
    register_harness_profile(MODEL_PROFILE_KEY, config)

    agent = create_deep_agent(model=get_real_model())
    result = invoke_and_pretty_print(
        agent,
        {
            "messages": [
                {
                    "role": "user",
                    "content": "config profile status",
                }
            ]
        },
    )

    assert config.to_dict()["excluded_tools"] == ["execute"]
    assert config.general_purpose_subagent == GeneralPurposeSubagentProfile(
        enabled=False
    )
    assert "CONFIG_PROFILE_ACTIVE" in result["messages"][-1].content
    print("config profile real agent ok")


if __name__ == "__main__":
    main()
