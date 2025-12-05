"""StateGraph 长期记忆 + SQLite Store 示例。

使用 SqliteStore 持久化用户画像到 src/data/graph_store.sqlite，
在节点中读取 store 信息并响应。
"""

from pathlib import Path
from typing import TypedDict

from langchain.messages import HumanMessage
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.store.sqlite import SqliteStore

from src.llms import get_default_model

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "graph_store.sqlite"


class Context(TypedDict):
    user_id: str


def call_model(state: MessagesState, *, store: SqliteStore, config: dict):
    model = get_default_model()
    user_id = config["configurable"]["user_id"]
    namespace = ("memories", user_id)
    memories = store.search(namespace, query=str(state["messages"][-1].content))
    memory_text = "\n".join(str(item.value) for item in memories) if memories else "暂无画像"
    system_msg = {"role": "system", "content": f"你是助手，用户画像：{memory_text}"}
    response = model.invoke([system_msg, *state["messages"]])
    # 简单记忆：当用户提到“记住”时写入 store
    last = state["messages"][-1].content
    if isinstance(last, str) and "记住" in last:
        store.put(namespace, f"mem-{len(memories)+1}", {"data": last})
    return {"messages": response}


def run_demo() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SqliteStore.from_conn_string(str(DB_PATH)) as store:
        store.setup()
        builder = StateGraph(MessagesState)
        builder.add_node("call_model", call_model)
        builder.add_edge(START, "call_model")
        graph = builder.compile(store=store)

        config = {"configurable": {"thread_id": "graph-store-thread", "user_id": "u1"}}
        graph.invoke({"messages": [HumanMessage(content="记住：我叫韩梅梅")]}, config)
        final = graph.invoke({"messages": [HumanMessage(content="我是谁？")]}, config)
        for m in final["messages"]:
            m.pretty_print()
        print(f"长期存储文件：{DB_PATH}")


if __name__ == "__main__":
    run_demo()
