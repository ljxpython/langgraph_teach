from __future__ import annotations

from deepagents import create_deep_agent
from langchain.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from _hitl_output import print_graph_output, require_interrupt, tool_messages
from _model import get_real_model


@tool
def remove_file(path: str) -> str:
    """Delete a file by path."""
    return f"Deleted {path}"


def main() -> None:
    agent = create_deep_agent(
        model=get_real_model(),
        tools=[remove_file],
        interrupt_on={"remove_file": True},
        checkpointer=MemorySaver(),
        system_prompt="When asked to remove a file, call remove_file exactly once.",
    )
    config = {"configurable": {"thread_id": "hitl-basic-approve"}}

    result = agent.invoke(
        {"messages": [{"role": "user", "content": "请调用 remove_file 删除 /tmp/a.txt"}]},
        config=config,
        version="v2",
    )
    print_graph_output(result)
    interrupt_value = require_interrupt(result)
    assert interrupt_value["action_requests"][0]["name"] == "remove_file"

    result = agent.invoke(
        Command(resume={"decisions": [{"type": "approve"}]}),
        config=config,
        version="v2",
    )
    print_graph_output(result)

    assert any("Deleted /tmp/a.txt" in output for output in tool_messages(result, name="remove_file"))
    print("basic approve HITL real agent ok")


if __name__ == "__main__":
    main()

