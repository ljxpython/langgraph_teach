from __future__ import annotations

from deepagents import create_deep_agent
from langchain.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from _hitl_output import print_graph_output, require_interrupt, tool_messages
from _model import get_real_model


@tool
def read_secret(path: str) -> str:
    """Read a sensitive secret path."""
    return f"secret-from:{path}"


secret_reader_subagent = {
    "name": "secret-reader",
    "description": "Reads sensitive paths after human approval.",
    "system_prompt": (
        "You are secret-reader. Always call read_secret exactly once and return "
        "only the tool result."
    ),
    "tools": [read_secret],
    "interrupt_on": {
        "read_secret": {"allowed_decisions": ["approve", "reject"]},
    },
}


def main() -> None:
    agent = create_deep_agent(
        model=get_real_model(),
        subagents=[secret_reader_subagent],
        checkpointer=MemorySaver(),
        system_prompt="Delegate secret reads to secret-reader.",
    )
    config = {"configurable": {"thread_id": "hitl-subagent-interrupt"}}
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "委派 secret-reader 读取 /secrets/token.txt",
                }
            ]
        },
        config=config,
        version="v2",
    )
    print_graph_output(result)
    interrupt_value = require_interrupt(result)
    assert interrupt_value["action_requests"][0]["name"] == "read_secret"

    result = agent.invoke(
        Command(resume={"decisions": [{"type": "approve"}]}),
        config=config,
        version="v2",
    )
    print_graph_output(result)

    assert any("secret-from:/secrets/token.txt" in output for output in tool_messages(result, name="task"))
    print("subagent interrupt HITL real agent ok")


if __name__ == "__main__":
    main()

