"""检查点查看与清理示例。

演示 graph.get_state / get_state_history 与 checkpointer.delete_thread。
"""

from langgraph.graph import START, MessagesState, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import HumanMessage

from src.llms import get_default_model


def call_model(state: MessagesState):
    model = get_default_model()
    resp = model.invoke(state["messages"])
    return {"messages": resp}


def run_demo() -> None:
    checkpointer = InMemorySaver()
    builder = StateGraph(MessagesState)
    builder.add_node("call_model", call_model)
    builder.add_edge(START, "call_model")
    graph = builder.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "checkpoint-thread"}}
    graph.invoke({"messages": [HumanMessage(content="记住我叫李雷")]}, config)
    graph.invoke({"messages": [HumanMessage(content="我叫什么名字？")]}, config)

    snapshot = graph.get_state(config)
    history = list(graph.get_state_history(config))
    print("最新状态消息数：", len(snapshot.values["messages"]))
    print("历史快照数：", len(history))

    # 删除该线程的所有检查点
    graph.checkpointer.delete_thread("checkpoint-thread")
    print("已清理 checkpoint-thread 的检查点。")


if __name__ == "__main__":
    run_demo()
