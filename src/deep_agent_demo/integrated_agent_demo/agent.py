import asyncio
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
from langchain.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.store.sqlite import SqliteStore

from src.llms import get_default_model

DEFAULT_SYSTEM_PROMPT = """你是综合演示代理，负责规划、记忆与委派。
- 先写 TODO（默认中间件提供），长输出写到文件系统
- 临时内容放默认根目录，长期记忆放 /memories/ 前缀；工作区用 /workspace/ 前缀
- 需要深入调研/写作时委派子智能体，主回复保持简洁"""


def get_zhipu_search_mcp_tools():
    """获取智谱搜索 MCP 工具列表，依赖环境变量 zhipu_search_mcp_url。"""
    url = os.environ.get("zhipu_search_mcp_url")
    if not url:
        raise RuntimeError("缺少环境变量 zhipu_search_mcp_url，无法初始化搜索工具")
    client = MultiServerMCPClient(
        {
            "search": {
                "url": url,
                "transport": "sse",
            }
        }
    )
    return asyncio.run(client.get_tools())


@tool
def write_outline(title: str) -> str:
    """生成简短提纲，便于写作子智能体使用。"""
    return f"Outline for {title}: 背景/要点/总结"


def build_subagents() -> list[dict[str, Any]]:
    search_tools = get_zhipu_search_mcp_tools()
    research_subagent = {
        "name": "research-agent",
        "description": "负责检索与信息汇总，适合复杂研究型问题",
        "system_prompt": """你是研究专家：
1) 拆分查询并调用 search 工具收集要点
2) 整理 150-200 字摘要，给出关键发现""",
        "tools": search_tools,
    }

    writer_subagent = {
        "name": "writer-agent",
        "description": "负责提纲与成稿，突出行动项和结论",
        "system_prompt": """你是写作助手：
1) 若缺少结构先生成提纲（可调用 write_outline）
2) 输出 150-200 字报告，提炼行动项""",
        "tools": [write_outline],
    }

    return [research_subagent, writer_subagent]


def build_store(store: Any | None = None) -> Any:
    if store is not None:
        return store
    return InMemoryStore()


def build_sqlite_store(db_path: str = "src/data/integrated_agent.sqlite") -> SqliteStore:
    """SQLite 持久化，启用 WAL 与多线程访问。"""
    resolved_path = os.path.abspath(db_path)
    os.makedirs(os.path.dirname(resolved_path), exist_ok=True)
    conn = sqlite3.connect(
        resolved_path,
        check_same_thread=False,
        timeout=30.0,
        isolation_level=None,
    )
    conn.execute("PRAGMA journal_mode=WAL;")
    store = SqliteStore(conn)
    store.setup()
    return store


def build_backend(root_dir: str = ".") -> Callable[[Any], Any]:
    """组合后端：默认临时态；/memories/ 持久化；/workspace/ 映射本地磁盘。"""
    resolved_root = os.path.abspath(root_dir)
    os.makedirs(resolved_root, exist_ok=True)
    return lambda rt: CompositeBackend(
        default=StateBackend(rt),
        routes={
            "/memories/": StoreBackend(rt),
            "/workspace/": FilesystemBackend(root_dir=resolved_root, virtual_mode=True),
        },
    )


def build_integrated_agent(
    *,
    store: Any | None = None,
    root_dir: str = ".",
) -> Callable[..., Any]:
    """创建综合演示 deep agent：默认中间件 + 自定义子智能体 + 路由式后端。"""
    selected_store = build_store(store)
    backend_factory = build_backend(root_dir)

    return create_deep_agent(
        model=get_default_model(),
        backend=backend_factory,
        store=selected_store,
        subagents=build_subagents(),
        checkpointer=MemorySaver(),
        system_prompt=DEFAULT_SYSTEM_PROMPT,
    )


def run_demo_request(agent: Callable[..., Any], user_message: str, thread_id: str = "integrated-agent-demo") -> Any:
    """同步封装：调度 async 版，方便脚本快速调用。"""
    return asyncio.run(arun_demo_request(agent, user_message, thread_id))


async def arun_demo_request(agent: Callable[..., Any], user_message: str, thread_id: str = "integrated-agent-demo") -> Any:
    """统一调用入口（async），使用 HumanMessage 并 pretty_print 输出。"""
    messages = [HumanMessage(content=user_message)]
    result = await agent.ainvoke(
        {"messages": messages},
        config={"configurable": {"thread_id": thread_id}},
    )
    for message in result["messages"]:
        message.pretty_print()
    return result

agent = build_integrated_agent(root_dir=".", store=None)

if __name__ == "__main__":
    # 默认使用 InMemoryStore；如需持久化，可替换 store=build_sqlite_store()
    agent = build_integrated_agent(root_dir=".", store=None)
    run_demo_request(
        agent,
        "请调研'企业知识库检索最佳实践'，把关键信息存入 /memories/research/notes.txt，"
        "在 /workspace/plan.md 草拟执行计划，总结给我一个精简答复。",
    )
