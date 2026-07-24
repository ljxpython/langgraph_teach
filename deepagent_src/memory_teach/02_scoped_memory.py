from __future__ import annotations

from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from deepagents.backends.utils import create_file_data
from langgraph.store.memory import InMemoryStore


MEMORY_SOURCE = "/memories/AGENTS.md"
ROUTED_STORE_KEY = "/AGENTS.md"


def read_memory(backend: CompositeBackend) -> str:
    response = backend.download_files([MEMORY_SOURCE])[0]
    assert response.error is None
    assert response.content is not None
    return response.content.decode("utf-8")


def main() -> None:
    store = InMemoryStore()
    store.put(("agent-memory",), ROUTED_STORE_KEY, create_file_data("agent shared memory"))
    store.put(("user-alice",), ROUTED_STORE_KEY, create_file_data("alice prefers Python"))
    store.put(("user-bob",), ROUTED_STORE_KEY, create_file_data("bob prefers TypeScript"))

    agent_backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/memories/": StoreBackend(
                store=store,
                namespace=lambda _rt: ("agent-memory",),
            )
        },
    )
    alice_backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/memories/": StoreBackend(
                store=store,
                namespace=lambda _rt: ("user-alice",),
            )
        },
    )
    bob_backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/memories/": StoreBackend(
                store=store,
                namespace=lambda _rt: ("user-bob",),
            )
        },
    )

    assert read_memory(agent_backend) == "agent shared memory"
    assert read_memory(alice_backend) == "alice prefers Python"
    assert read_memory(bob_backend) == "bob prefers TypeScript"
    print("scoped memory ok")


if __name__ == "__main__":
    main()
