from __future__ import annotations

from typing import Any, Sequence

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend, StateBackend, StoreBackend
from deepagents.backends.utils import create_file_data
from deepagents.middleware.skills import _list_skills_with_errors
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent / "workspace"
SKILL_SOURCE = "/skills/"
SKILL_PATH = "/skills/langgraph-docs/SKILL.md"
STORE_NAMESPACE = ("skills-teach",)


class ToolReadyFakeChatModel(FakeMessagesListChatModel):
    def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | BaseTool],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> "ToolReadyFakeChatModel":
        return self


def assert_langgraph_docs_loaded(skills: list[dict[str, Any]], error: str | None) -> None:
    assert error is None
    assert len(skills) == 1
    assert skills[0]["name"] == "langgraph-docs"
    assert skills[0]["path"] == SKILL_PATH


def discover_from_filesystem() -> None:
    backend = FilesystemBackend(root_dir=ROOT_DIR, virtual_mode=True)
    skills, error = _list_skills_with_errors(backend, SKILL_SOURCE)
    assert_langgraph_docs_loaded(skills, error)


def discover_from_store() -> None:
    skill_content = (ROOT_DIR / SKILL_PATH.lstrip("/")).read_text(encoding="utf-8")
    store = InMemoryStore()
    store.put(STORE_NAMESPACE, SKILL_PATH, create_file_data(skill_content))

    backend = StoreBackend(store=store, namespace=lambda _rt: STORE_NAMESPACE)
    skills, error = _list_skills_with_errors(backend, SKILL_SOURCE)
    assert_langgraph_docs_loaded(skills, error)


def invoke_with_state_backend() -> None:
    skill_content = (ROOT_DIR / SKILL_PATH.lstrip("/")).read_text(encoding="utf-8")
    agent = create_deep_agent(
        model=ToolReadyFakeChatModel(responses=[AIMessage(content="state backend ok")]),
        backend=StateBackend(),
        skills=[SKILL_SOURCE],
        checkpointer=InMemorySaver(),
    )
    result = agent.invoke(
        {
            "messages": [{"role": "user", "content": "hello"}],
            "files": {SKILL_PATH: create_file_data(skill_content)},
        },
        {"configurable": {"thread_id": "skills-state-backend-demo"}},
    )

    assert result["messages"][-1].content == "state backend ok"


def main() -> None:
    discover_from_filesystem()
    discover_from_store()
    invoke_with_state_backend()
    print("backend loading ok")


if __name__ == "__main__":
    main()
