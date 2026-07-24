from __future__ import annotations

import os

from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from deepagents.backends.utils import create_file_data
from deepagents.middleware.filesystem import _check_fs_permission
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from deepagent_src.agent_output import stream_debug_trace
from deepagent_src.llms import get_gpt_model


USER_NAMESPACE = ("memory-teach-user",)
ORG_NAMESPACE = ("memory-teach-org",)
MEMORY_SOURCE = "/memories/AGENTS.md"
POLICY_SOURCE = "/policies/AGENTS.md"
ROUTED_STORE_KEY = "/AGENTS.md"


def main() -> None:
    os.environ["LANGSMITH_TRACING"] = "false"

    store = InMemoryStore()
    store.put(
        USER_NAMESPACE,
        ROUTED_STORE_KEY,
        create_file_data(
            """# User Memory

## Response style

- 用户喜欢中文解释。
- 用户希望 DeepAgent 教学尽量给可运行代码。
"""
        ),
    )
    store.put(
        ORG_NAMESPACE,
        ROUTED_STORE_KEY,
        create_file_data(
            """# Organization Policy

## Memory safety

- 不要把 API key、token、密码写进 memory。
- 共享 policy memory 只能读，不能让 Agent 修改。
"""
        ),
    )

    backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/memories/": StoreBackend(
                store=store,
                namespace=lambda _rt: USER_NAMESPACE,
            ),
            "/policies/": StoreBackend(
                store=store,
                namespace=lambda _rt: ORG_NAMESPACE,
            ),
        },
    )
    permissions = [
        FilesystemPermission(
            operations=["write"],
            paths=["/policies/**"],
            mode="deny",
        )
    ]

    assert backend.download_files([MEMORY_SOURCE])[0].error is None
    assert backend.download_files([POLICY_SOURCE])[0].error is None
    assert _check_fs_permission(permissions, "write", POLICY_SOURCE) == "deny"
    assert _check_fs_permission(permissions, "read", POLICY_SOURCE) == "allow"

    graph = create_deep_agent(
        model=get_gpt_model(),
        backend=backend,
        memory=[MEMORY_SOURCE, POLICY_SOURCE],
        permissions=permissions,
        store=store,
        checkpointer=InMemorySaver(),
    )

    messages = [
        HumanMessage(
            content=(
                "请根据已加载的长期 memory，说明我学习 DeepAgent memory 时应该注意什么。"
                "要求：用中文，提到用户偏好和组织安全规则。不要写文件。"
            )
        )
    ]
    stream_debug_trace(
        graph,
        {"messages": messages},
        {"configurable": {"thread_id": "memory-comprehensive-case"}},
    )


if __name__ == "__main__":
    main()
