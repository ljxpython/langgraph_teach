from __future__ import annotations

import os
from typing import Any

from deepagents import RubricMiddleware, create_deep_agent
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from deepagent_src.llms import get_gpt_model


RUBRIC = (
    "- The answer has the exact title `Deployment readiness`\n"
    "- The answer has exactly two hyphen bullets\n"
    "- One bullet mentions thread_id and one mentions context"
)

GRADER_PROMPT = (
    "You are a strict rubric grader. Return only structured output matching "
    "this exact schema. Top level fields: result, explanation, criteria. "
    "criteria items MUST use name and passed. If passed is false, include gap. "
    "Never use criterion or satisfied fields. "
    "Use result=satisfied only when all criteria pass."
)


def main() -> None:
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    evaluations: list[dict[str, Any]] = []

    def on_evaluation(event: dict[str, Any]) -> None:
        evaluations.append(event)
        print(f"grader iteration {event['iteration']}: {event['result']}")

    agent = create_deep_agent(
        model=get_gpt_model(disable_tool_streaming=True),
        middleware=[
            RubricMiddleware(
                model=get_gpt_model(disable_tool_streaming=True),
                system_prompt=GRADER_PROMPT,
                max_iterations=2,
                on_evaluation=on_evaluation,
            )
        ],
        subagents=[],
        checkpointer=InMemorySaver(),
        system_prompt=(
            "Reply with exactly a title `Deployment readiness` and exactly two "
            "hyphen bullets. The first bullet must include thread_id and the "
            "second must include context."
        ),
    )

    state = agent.invoke(
        {
            "messages": [HumanMessage(content="Write the deployment readiness summary.")],
            "rubric": RUBRIC,
        },
        config={"configurable": {"thread_id": "rubric-teach"}},
    )

    final_text = state["messages"][-1].text
    evaluation = evaluations[-1]
    print("final:", final_text)
    print("criteria:", evaluation["criteria"])

    assert len(evaluations) == 1, evaluations
    assert evaluation["result"] == "satisfied", evaluation
    assert len(evaluation["criteria"]) == 3, evaluation
    assert all(item["passed"] for item in evaluation["criteria"]), evaluation
    assert final_text.splitlines()[0] == "Deployment readiness", final_text
    assert len([line for line in final_text.splitlines() if line.startswith("- ")]) == 2
    assert "thread_id" in final_text
    assert "context" in final_text
    print("rubric runtime evaluation real call ok")


if __name__ == "__main__":
    main()
