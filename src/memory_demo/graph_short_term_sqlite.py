"""StateGraph 短期记忆 + SQLite 持久化示例。

使用 SqliteSaver 将消息检查点写入 src/data/graph_checkpoints.sqlite。
同一 thread_id 复用对话上下文。
"""

from pathlib import Path

from langchain.messages import HumanMessage
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver

from src.llms import get_default_model

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "graph_checkpoints.sqlite"


def call_model(state: MessagesState):
    model = get_default_model()
    response = model.invoke(state["messages"])
    return {"messages": response}


def run_demo() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SqliteSaver.from_conn_string(str(DB_PATH)) as checkpointer:
        checkpointer.setup()

        builder = StateGraph(MessagesState)
        builder.add_node("call_model", call_model)
        builder.add_edge(START, "call_model")
        graph = builder.compile(checkpointer=checkpointer)

        config = {"configurable": {"thread_id": "graph-sqlite-thread"}}
        graph.invoke({"messages": [HumanMessage(content="你好，我叫李雷")]}, config)
        final = graph.invoke({"messages": [HumanMessage(content="我叫什么名字？")]}, config)
        for m in final["messages"]:
            m.pretty_print()
        print(f"检查点文件：{DB_PATH}")


if __name__ == "__main__":
    run_demo()
