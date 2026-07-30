from __future__ import annotations

from deepagents import FilesystemPermission, create_deep_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from _hitl_output import print_graph_output, require_interrupt, tool_messages
from _model import get_real_model


def main() -> None:
    agent = create_deep_agent(
        model=get_real_model(),
        permissions=[
            FilesystemPermission(
                operations=["write"],
                paths=["/secrets/**"],
                mode="interrupt",
            )
        ],
        checkpointer=MemorySaver(),
        system_prompt=(
            "When asked to save content to a path, call write_file exactly once."
        ),
    )
    config = {"configurable": {"thread_id": "hitl-filesystem-permission"}}
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "把内容 demo 写入 /secrets/key.txt",
                }
            ]
        },
        config=config,
        version="v2",
    )
    print_graph_output(result)
    interrupt_value = require_interrupt(result)
    assert interrupt_value["action_requests"][0]["name"] == "write_file"

    result = agent.invoke(
        Command(resume={"decisions": [{"type": "approve"}]}),
        config=config,
        version="v2",
    )
    print_graph_output(result)

    assert any("/secrets/key.txt" in output for output in tool_messages(result, name="write_file"))
    print("filesystem permission interrupt HITL real agent ok")


if __name__ == "__main__":
    main()

