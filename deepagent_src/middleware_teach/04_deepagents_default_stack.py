from __future__ import annotations

from typing import Any

from deepagents import create_deep_agent
from langchain.agents.middleware import AgentState, before_model
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langgraph.runtime import Runtime

BASE_STACK = [
    "SkillsMiddleware",
    "FilesystemMiddleware",
    "SubAgentMiddleware",
    "SummarizationMiddleware",
    "PatchToolCallsMiddleware",
    "AsyncSubAgentMiddleware",
    "your middleware",
]

TAIL_STACK = [
    "harness profile extras",
    "tool exclusion",
    "prompt caching",
    "MemoryMiddleware",
    "HumanInTheLoopMiddleware",
]


@before_model(name="custom_probe")
def custom_probe(
    state: AgentState,
    runtime: Runtime[Any],
) -> dict[str, Any] | None:
    return None


def main() -> None:
    agent = create_deep_agent(
        model=FakeListChatModel(responses=["OK"]),
        subagents=[],
        middleware=[custom_probe],
    )
    graph_nodes = list(agent.get_graph().nodes.keys())

    print("base_stack:", " -> ".join(BASE_STACK))
    print("tail_stack:", " -> ".join(TAIL_STACK))
    print("graph_nodes:", graph_nodes)

    patch_node = "PatchToolCallsMiddleware.before_agent"
    custom_node = "custom_probe.before_model"
    assert patch_node in graph_nodes, graph_nodes
    assert custom_node in graph_nodes, graph_nodes
    assert graph_nodes.index(patch_node) < graph_nodes.index(custom_node), graph_nodes
    print("deepagents default stack local check ok")


if __name__ == "__main__":
    main()
