from __future__ import annotations

from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from deepagents.backends.utils import create_file_data
from langgraph.store.memory import InMemoryStore


MEMORY_SOURCE = "/memories/AGENTS.md"
ROUTED_STORE_KEY = "/AGENTS.md"


def create_backend_for_user(store: InMemoryStore, user_id: str) -> CompositeBackend:
    return CompositeBackend(
        default=StateBackend(),
        routes={
            "/memories/": StoreBackend(
                store=store,
                namespace=lambda _rt: ("users", user_id),
            )
        },
    )


def ensure_user_memory(store: InMemoryStore, user_id: str) -> None:
    namespace = ("users", user_id)
    if store.get(namespace, ROUTED_STORE_KEY) is None:
        store.put(
            namespace,
            ROUTED_STORE_KEY,
            create_file_data("# User Memory\n\n## Preferences\n\n"),
        )


def read_memory(backend: CompositeBackend) -> str:
    response = backend.download_files([MEMORY_SOURCE])[0]
    assert response.error is None
    assert response.content is not None
    return response.content.decode("utf-8")


def main() -> None:
    store = InMemoryStore()

    for user_id in ["alice", "bob", "new-user-42"]:
        ensure_user_memory(store, user_id)

    store.put(
        ("users", "alice"),
        ROUTED_STORE_KEY,
        create_file_data("# User Memory\n\n## Preferences\n\n- Prefers Python\n"),
    )
    store.put(
        ("users", "bob"),
        ROUTED_STORE_KEY,
        create_file_data("# User Memory\n\n## Preferences\n\n- Prefers TypeScript\n"),
    )

    alice_backend = create_backend_for_user(store, "alice")
    bob_backend = create_backend_for_user(store, "bob")
    new_user_backend = create_backend_for_user(store, "new-user-42")

    assert "Prefers Python" in read_memory(alice_backend)
    assert "Prefers TypeScript" in read_memory(bob_backend)
    assert read_memory(new_user_backend).startswith("# User Memory")
    print("production user memory design ok")


if __name__ == "__main__":
    main()
