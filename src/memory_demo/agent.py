

from pathlib import Path
import sqlite3

from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

from src.llms import get_default_model

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "memory_checkpoints.sqlite"


def get_agent():
    """构造并返回带 SQLite 持久化的 Agent。"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    checkpointer.setup()

    return create_agent(
        model=get_default_model(),
        tools=[],
        # checkpointer=checkpointer,
        system_prompt="你是一个智能助手，你可以根据用户的问题进行回答。",
    )

agent = get_agent()


if __name__ == "__main__":
    agent = get_agent()
    messages = [HumanMessage(content="你好，这里是内存示例。")]
    result = agent.invoke({"messages": messages}, {"configurable": {"thread_id": "demo-thread"}})
    for m in result["messages"]:
        m.pretty_print()
