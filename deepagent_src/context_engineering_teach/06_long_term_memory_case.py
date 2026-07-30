from __future__ import annotations

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from deepagents.backends.utils import create_file_data
from langgraph.store.memory import InMemoryStore

from _model import get_real_model
from deepagent_src.agent_output import invoke_and_pretty_print


MEMORY_PATH = "/memories/user_preferences.txt"
ROUTED_STORE_KEY = "/user_preferences.txt"


def main() -> None:
    store = InMemoryStore()
    store.put(
        ("deepagents-context", "u-123"),
        ROUTED_STORE_KEY,
        create_file_data("prefers short Chinese answers"),
    )

    backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/memories/": StoreBackend(
                store=store,
                namespace=lambda _rt: ("deepagents-context", "u-123"),
            )
        },
    )

    agent = create_deep_agent(
        model=get_real_model(),
        store=store,
        backend=backend,
        system_prompt=(
            "Save stable user preferences under /memories/user_preferences.txt."
        ),
    )

    stored_file = backend.download_files([MEMORY_PATH])[0]

    assert agent is not None
    assert stored_file.error is None
    assert stored_file.content is not None
    assert "short Chinese answers" in stored_file.content.decode("utf-8")

    result = invoke_and_pretty_print(
        agent,
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "读取 /memories/user_preferences.txt，"
                        "然后用一句中文说出里面记录的偏好。"
                    ),
                }
            ]
        }
    )

    assert result["messages"][-1].content
    print("long-term memory real agent ok")


if __name__ == "__main__":
    main()
