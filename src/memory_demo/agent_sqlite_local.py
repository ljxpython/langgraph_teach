"""本地运行的 SQLite 持久化 Agent。

用途：
- 不被 LangGraph API 自动加载（避免 checkpointer 限制）。
- 直接在脚本中使用 SqliteSaver 将会话检查点落盘到 src/data/memory_checkpoints.sqlite。

使用示例：
    python -m src.memory_demo.agent_sqlite_local
"""

from pathlib import Path
import sqlite3

from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

from src.llms import get_default_model

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "memory_checkpoints.sqlite"


def get_agent():
    """构造一个带 SQLite 持久化的 Agent（本地脚本使用，不供 langgraph_api 加载）。"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    checkpointer.setup()

    return create_agent(
        model=get_default_model(),
        tools=[],
        checkpointer=checkpointer,
        system_prompt="你是一个智能助手，使用 SQLite 存储短期记忆。",
    )


def demo() -> None:
    agent = get_agent()
    config = {"configurable": {"thread_id": "demo-sqlite"}}

    for text in ["你好，我叫李雷", "我叫什么名字？"]:
        messages = [HumanMessage(content=text)]
        result = agent.invoke({"messages": messages}, config)
        for m in result["messages"]:
            m.pretty_print()
        print()
    print(f"检查点文件路径：{DB_PATH}")

agent = get_agent()
if __name__ == "__main__":
    demo()
