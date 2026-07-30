from __future__ import annotations

import json

from deepagents import create_deep_agent
from pydantic import BaseModel, Field

from _model import get_real_model
from deepagent_src.agent_output import invoke_and_pretty_print


class LessonFinding(BaseModel):
    """Structured result returned by a subagent."""

    summary: str = Field(description="Short summary")
    confidence: float = Field(description="Confidence from 0 to 1")
    sources: list[str] = Field(description="Source names")


structured_subagent = {
    "name": "structured-reporter",
    "description": "Use this subagent when the parent needs JSON findings.",
    "system_prompt": (
        "Return structured data with summary exactly 'structured-subagent-summary', "
        "confidence exactly 0.91, and sources exactly ['subagent-docs']."
    ),
    "tools": [],
    "response_format": LessonFinding,
}


def main() -> None:
    agent = create_deep_agent(
        model=get_real_model(),
        system_prompt=(
            "You are a coordinator. Delegate JSON finding requests to "
            "structured-reporter with the task tool. Do not ask clarification "
            "for this lesson."
        ),
        subagents=[structured_subagent],
    )
    result = invoke_and_pretty_print(
        agent,
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "必须调用 task 工具，subagent_type 必须是 structured-reporter。"
                        "任务描述：返回本课固定结构化 findings。"
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
    parsed = json.loads(task_outputs[-1])

    assert parsed["summary"] == "structured-subagent-summary"
    assert parsed["confidence"] == 0.91
    assert parsed["sources"] == ["subagent-docs"]
    print("subagent structured output real agent ok")


if __name__ == "__main__":
    main()
