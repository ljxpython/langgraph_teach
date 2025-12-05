import os
import sqlite3
from collections.abc import Callable
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.store.sqlite import SqliteStore

from src.llms import get_default_model

DEFAULT_SYSTEM_PROMPT = """你是长期记忆演示助手。
- 临时文件放默认路径（例：/draft.txt）
- 持久文件统一放 /memories/ 前缀（例：/memories/preferences.txt、/memories/notes/）
每次对话开始若需要历史信息，请先检查 /memories/ 下的文件。"""


def _default_config(thread_id: str = "long-term-memory-demo") -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}}


def build_store(store: Any | None = None) -> Any:
    """选择 Store，实现跨线程持久化。默认 InMemoryStore，可替换为 SqliteStore。"""
    if store is not None:
        return store
    return InMemoryStore()


def build_sqlite_store(db_path: str = "src/data/long_term_memory.sqlite") -> SqliteStore:
    """构建 SQLite Store，启用多线程与 WAL，适合本地持久化。"""
    resolved_path = os.path.abspath(db_path)
    os.makedirs(os.path.dirname(resolved_path), exist_ok=True)
    conn = sqlite3.connect(
        resolved_path,
        check_same_thread=False,
        timeout=30.0,
        isolation_level=None,  # autocommit，避免嵌套事务问题
    )
    conn.execute("PRAGMA journal_mode=WAL;")
    store = SqliteStore(conn)
    store.setup()
    return store


def build_long_term_memory_agent(store: Any | None = None) -> Callable[..., Any]:
    """创建同时具备短期与长期记忆的 Deep Agent。"""
    selected_store = build_store(store)

    composite_backend = lambda rt: CompositeBackend(
        default=StateBackend(rt),
        routes={"/memories/": StoreBackend(rt)},
    )

    return create_deep_agent(
        model=get_default_model(),
        backend=composite_backend,
        store=selected_store,
        checkpointer=MemorySaver(),
        system_prompt=DEFAULT_SYSTEM_PROMPT,
    )


def run_demo_request(agent: Callable[..., Any], user_message: str, thread_id: str = "long-term-memory-demo") -> Any:
    """统一调用入口，使用 HumanMessage 并 pretty_print 输出。"""
    messages = [HumanMessage(content=user_message)]
    result = agent.invoke(
        {"messages": messages},
        config=_default_config(thread_id),
    )
    for message in result["messages"]:
        message.pretty_print()
    return result


if __name__ == "__main__":
    # 默认使用 InMemoryStore，如需持久化到磁盘可改为 build_sqlite_store()
    agent = build_long_term_memory_agent()
    run_demo_request(
        agent,
        "请把我的偏好写入 /memories/preferences.txt：喜欢精简答案；再在 /notes.txt 写一段临时草稿。",
    )
