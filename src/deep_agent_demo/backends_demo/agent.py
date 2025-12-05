import os
import sqlite3
from collections.abc import Callable
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import (
    CompositeBackend,
    FilesystemBackend,
    StateBackend,
    StoreBackend,
)
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.store.sqlite import SqliteStore

from src.llms import get_default_model

DEFAULT_SYSTEM_PROMPT = "你是一个后端演示向导，帮助用户体验不同的文件系统后端。"


def _default_config(thread_id: str = "backends-demo") -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}}


def build_state_backend_agent() -> Callable[..., Any]:
    """仅使用内存态存储（StateBackend），适合临时文件。"""
    return create_deep_agent(
        model=get_default_model(),
        backend=lambda rt: StateBackend(rt),
        checkpointer=MemorySaver(),
        system_prompt=DEFAULT_SYSTEM_PROMPT,
    )


def build_filesystem_backend_agent(root_dir: str, virtual_mode: bool = True) -> Callable[..., Any]:
    """映射真实磁盘目录，使用虚拟模式规范路径。"""
    resolved_root = os.path.abspath(root_dir)
    return create_deep_agent(
        model=get_default_model(),
        backend=FilesystemBackend(root_dir=resolved_root, virtual_mode=virtual_mode),
        checkpointer=MemorySaver(),
        system_prompt=DEFAULT_SYSTEM_PROMPT,
    )


def build_store_backend_agent(store: Any | None = None) -> Callable[..., Any]:
    """使用 LangGraph Store 跨线程持久化，默认 InMemoryStore。"""
    selected_store = store or InMemoryStore()
    return create_deep_agent(
        model=get_default_model(),
        backend=lambda rt: StoreBackend(rt),
        store=selected_store,
        checkpointer=MemorySaver(),
        system_prompt=DEFAULT_SYSTEM_PROMPT,
    )


def build_sqlite_store_backend_agent(db_path: str = "src/data/backends.sqlite") -> Callable[..., Any]:
    """使用 SqliteStore 持久化跨线程数据，便于落盘保存。"""
    resolved_path = os.path.abspath(db_path)
    os.makedirs(os.path.dirname(resolved_path), exist_ok=True)
    # 允许多线程访问，并开启 autocommit（避免嵌套事务报错）
    conn = sqlite3.connect(
        resolved_path,
        check_same_thread=False,
        timeout=30.0,
        isolation_level=None,
    )
    conn.execute("PRAGMA journal_mode=WAL;")
    store = SqliteStore(conn)
    store.setup()
    return build_store_backend_agent(store)


def build_composite_backend_agent(root_dir: str, store: Any | None = None) -> Callable[..., Any]:
    """组合路由：默认内存态，/memories/ 持久化，/workspace/ 映射本地磁盘。"""
    resolved_root = os.path.abspath(root_dir)
    selected_store = store or InMemoryStore()

    composite_backend = lambda rt: CompositeBackend(
        default=StateBackend(rt),
        routes={
            "/memories/": StoreBackend(rt),
            "/workspace/": FilesystemBackend(root_dir=resolved_root, virtual_mode=True),
        },
    )

    return create_deep_agent(
        model=get_default_model(),
        backend=composite_backend,
        store=selected_store,
        checkpointer=MemorySaver(),
        system_prompt=DEFAULT_SYSTEM_PROMPT,
    )


def run_demo_request(agent: Callable[..., Any], user_message: str, thread_id: str = "backends-demo") -> Any:
    """统一的调用入口，使用 HumanMessage 并打印对话。"""
    messages = [HumanMessage(content=user_message)]
    result = agent.invoke(
        {"messages": messages},
        config=_default_config(thread_id),
    )
    for message in result["messages"]:
        message.pretty_print()
    return result


if __name__ == "__main__":
    # demo_agent = build_composite_backend_agent(root_dir=".")
    demo_agent = build_sqlite_store_backend_agent()
    run_demo_request(
        demo_agent,
        "在 /workspace/notes.txt 写一句话，并把摘要放到 /memories/summary.txt，然后列出根目录文件。",
    )
