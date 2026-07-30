from __future__ import annotations

from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from deepagents.middleware.summarization import create_summarization_tool_middleware

from _model import get_real_model
from deepagent_src.agent_output import invoke_and_pretty_print


def main() -> None:
    model = get_real_model()
    compaction_middleware = create_summarization_tool_middleware(model, StateBackend)
    agent = create_deep_agent(model=model, middleware=[compaction_middleware])

    tool_names = [tool.name for tool in compaction_middleware.tools]
    result = invoke_and_pretty_print(
        agent,
        {
            "messages": [
                {
                    "role": "user",
                    "content": "用一句中文回答：compact_conversation 工具什么时候适合使用？",
                }
            ]
        }
    )

    assert agent is not None
    assert "compact_conversation" in tool_names
    assert result["messages"][-1].content
    print("context compression real agent ok")


if __name__ == "__main__":
    main()
