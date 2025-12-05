"""长期记忆 SQLite Store 示例。

演示通过 LangGraph SqliteStore 读取/写入用户画像，并在工具中访问长期记忆。
数据文件落在 src/data/memory_store.sqlite。
"""

from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.tools import ToolRuntime, tool
from langgraph.store.sqlite import SqliteStore

from src.llms import get_default_model

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "memory_store.sqlite"


@dataclass
class Context:
    user_id: str


class UserInfo(TypedDict):
    name: str
    language: str


@tool
def fetch_user_info(runtime: ToolRuntime[Context]) -> str:
    store = runtime.store
    user_id = runtime.context.user_id
    item = store.get(("users",), user_id)
    return str(item.value) if item else "Unknown user"


@tool
def save_user_info(user_info: UserInfo, runtime: ToolRuntime[Context]) -> str:
    store = runtime.store
    user_id = runtime.context.user_id
    store.put(("users",), user_id, user_info)
    return "已保存用户画像。"


def run_demo() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SqliteStore.from_conn_string(str(DB_PATH)) as store:
        store.setup()
        store.put(("users",), "seed_user", {"name": "种子用户", "language": "Chinese"})

        agent = create_agent(
            model=get_default_model(),
            tools=[fetch_user_info, save_user_info],
            store=store,
            context_schema=Context,
            system_prompt=(
                "你是助手，优先调用工具读取或保存用户画像；"
                "当用户提供姓名或语言信息时调用 save_user_info，回答时引用最新画像。"
            ),
        )

        existing_ctx = Context(user_id="seed_user")
        existing = agent.invoke(
            {"messages": [HumanMessage(content="读取我已有的画像")]},
            context=existing_ctx,
        )
        for m in existing["messages"]:
            m.pretty_print()

        new_ctx = Context(user_id="user_123")
        agent.invoke(
            {"messages": [HumanMessage(content="我叫韩梅梅，只说中文")]},
            context=new_ctx,
        )
        lookup = agent.invoke(
            {"messages": [HumanMessage(content="我是谁？")]},
            context=new_ctx,
        )
        for m in lookup["messages"]:
            m.pretty_print()

        matches = store.search(("users",), filter={"name": "韩梅梅"})
        print("索引过滤结果：", [item.value for item in matches])
        print(f"长期存储文件位置：{DB_PATH}")


if __name__ == "__main__":
    run_demo()
