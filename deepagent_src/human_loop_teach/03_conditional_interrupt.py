from __future__ import annotations

from deepagents import create_deep_agent
from langchain.agents.middleware import ToolCallRequest
from langchain.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from _hitl_output import print_graph_output, require_interrupt, tool_messages
from _model import get_real_model


@tool
def write_note(file_path: str, content: str) -> str:
    """Write a note to a path."""
    return f"Wrote {content} to {file_path}"


def writes_outside_workspace(request: ToolCallRequest) -> bool:
    path = request.tool_call["args"].get("file_path", "")
    return not path.startswith("/workspace/")


def main() -> None:
    agent = create_deep_agent(
        model=get_real_model(),
        tools=[write_note],
        interrupt_on={
            "write_note": {
                "allowed_decisions": ["approve", "reject"],
                "when": writes_outside_workspace,
            }
        },
        checkpointer=MemorySaver(),
        system_prompt="When asked to write a note, call write_note exactly once.",
    )

    safe_config = {"configurable": {"thread_id": "hitl-conditional-safe"}}
    safe = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "调用 write_note，file_path=/workspace/a.txt，content=safe",
                }
            ]
        },
        config=safe_config,
        version="v2",
    )
    print_graph_output(safe)
    assert not safe.interrupts
    assert any("/workspace/a.txt" in output for output in tool_messages(safe, name="write_note"))

    risky_config = {"configurable": {"thread_id": "hitl-conditional-risky"}}
    risky = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "调用 write_note，file_path=/secrets/a.txt，content=risky",
                }
            ]
        },
        config=risky_config,
        version="v2",
    )
    print_graph_output(risky)
    require_interrupt(risky)
    risky = agent.invoke(
        Command(resume={"decisions": [{"type": "reject", "message": "Outside workspace."}]}),
        config=risky_config,
        version="v2",
    )
    print_graph_output(risky)
    assert not any("/secrets/a.txt" in output and output.startswith("Wrote") for output in tool_messages(risky, name="write_note"))
    print("conditional interrupt HITL real agent ok")


if __name__ == "__main__":
    main()

