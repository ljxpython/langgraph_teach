"""短期记忆 SQLite 持久化示例。

使用 SqliteSaver 将对话历史落盘到 src/data/memory_checkpoints.sqlite，
同一 thread_id 再次运行可恢复上下文。模型来源：src/llms.get_default_model。
"""

from pathlib import Path

from langchain.messages import HumanMessage
from langchain.agents import create_agent
from langgraph.checkpoint.sqlite import SqliteSaver

from src.llms import get_default_model

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "memory_checkpoints.sqlite"


def run_demo() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SqliteSaver.from_conn_string(str(DB_PATH)) as checkpointer:
        checkpointer.setup()
        agent = create_agent(
            model=get_default_model(),
            tools=[],
            system_prompt="保持回答简洁，利用已有对话信息回答。",
            checkpointer=checkpointer,
        )

        config = {"configurable": {"thread_id": "sqlite-thread"}}
        queries = [
            "我叫李雷，帮我记住。",
            "再确认一下我叫什么名字？",
        ]

        for text in queries:
            messages = [HumanMessage(content=text)]
            messages = agent.invoke({"messages": messages}, config)
            for m in messages["messages"]:
                m.pretty_print()
            print()

        print(f"持久化文件位置：{DB_PATH}")


if __name__ == "__main__":
    run_demo()
