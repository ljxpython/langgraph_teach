"""StateGraph 截断与删除消息示例。

使用 trim_messages 工具，演示删除早期消息控制上下文。
"""

from langchain_core.messages.utils import count_tokens_approximately, trim_messages
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import HumanMessage

from src.llms import get_default_model


def call_model(state: MessagesState):
    model = get_default_model()
    messages = trim_messages(
        state["messages"],
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=128,
        start_on="human",
        end_on=("human", "tool"),
    )
    response = model.invoke(messages)
    return {"messages": response}


def run_demo() -> None:
    checkpointer = InMemorySaver()
    builder = StateGraph(MessagesState)
    builder.add_node("call_model", call_model)
    builder.add_edge(START, "call_model")
    graph = builder.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "trim-thread"}}
    graph.invoke({"messages": [HumanMessage(content="我叫李雷")]}, config)
    graph.invoke({"messages": [HumanMessage(content="写一首关于猫的诗")]}, config)
    graph.invoke({"messages": [HumanMessage(content="再写一首关于狗的诗")]}, config)
    final = graph.invoke({"messages": [HumanMessage(content="我叫什么名字？")]}, config)
    for m in final["messages"]:
        m.pretty_print()


if __name__ == "__main__":
    run_demo()
