from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from langchain.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from deepagent_src.llms import get_gpt_model


@dataclass
class ThreadBackendRegistry:
    root_dir: Path
    backends: dict[str, LocalShellBackend] = field(default_factory=dict)

    async def get_or_create(self, thread_id: str) -> LocalShellBackend:
        if not thread_id:
            raise ValueError("configurable.thread_id is required")
        if thread_id not in self.backends:
            workspace = self.root_dir / f"thread-{thread_id}"
            workspace.mkdir(parents=True, exist_ok=True)
            self.backends[thread_id] = LocalShellBackend(
                root_dir=workspace,
                virtual_mode=True,
                env={"PATH": "/usr/bin:/bin"},
                timeout=10,
            )
        return self.backends[thread_id]


def get_thread_id(config: RunnableConfig) -> str:
    configurable = config.get("configurable", {})
    thread_id = configurable.get("thread_id")
    if not isinstance(thread_id, str) or not thread_id:
        raise ValueError("configurable.thread_id is required")
    return thread_id


async def build_agent(
    config: RunnableConfig,
    registry: ThreadBackendRegistry,
) -> Any:
    thread_id = get_thread_id(config)
    backend = await registry.get_or_create(thread_id)
    return create_deep_agent(
        model=get_gpt_model(disable_tool_streaming=True),
        backend=backend,
        subagents=[],
        system_prompt=(
            "You are a graph-factory teaching assistant. "
            f"You are serving thread {thread_id}. "
            "You must call write_file once with path /thread-note.txt and "
            f"content thread={thread_id}. Then reply with stored {thread_id}."
        ),
    )


def read_text(backend: LocalShellBackend, path: str) -> str:
    result = backend.read(path)
    if result.error:
        raise AssertionError(result.error)
    return result.file_data["content"]


def tool_call_names(messages: list[Any]) -> list[str]:
    names: list[str] = []
    for message in messages:
        for call in getattr(message, "tool_calls", None) or []:
            names.append(call.get("name", ""))
    return names


async def main() -> None:
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

    with TemporaryDirectory(prefix="deepagents-production-factory-") as tmp:
        registry = ThreadBackendRegistry(Path(tmp))
        alpha_config: RunnableConfig = {"configurable": {"thread_id": "alpha"}}
        beta_config: RunnableConfig = {"configurable": {"thread_id": "beta"}}

        alpha_agent = await build_agent(alpha_config, registry)
        alpha_backend = registry.backends["alpha"]
        _ = await build_agent(alpha_config, registry)
        beta_agent = await build_agent(beta_config, registry)
        beta_backend = registry.backends["beta"]

        assert registry.backends["alpha"] is alpha_backend
        assert alpha_backend is not beta_backend

        state = await alpha_agent.ainvoke(
            {"messages": [HumanMessage(content="Store this thread note now.")]}
        )
        alpha_messages = state["messages"]
        assert "write_file" in tool_call_names(alpha_messages)
        assert read_text(alpha_backend, "/thread-note.txt") == "thread=alpha"

        beta_backend.write("/thread-note.txt", "thread=beta")
        assert read_text(alpha_backend, "/thread-note.txt") == "thread=alpha"
        assert read_text(beta_backend, "/thread-note.txt") == "thread=beta"

        assert beta_agent is not alpha_agent
        print(f"alpha backend id: {alpha_backend.id}")
        print(f"beta backend id: {beta_backend.id}")
        print("graph factory thread-scoped production pattern ok")


if __name__ == "__main__":
    asyncio.run(main())
