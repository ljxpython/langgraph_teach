"""短期记忆 InMemorySaver 示例。

基于 LangGraph 的检查点功能，将对话状态保存在内存中，
同一 thread_id 的多次调用会自动携带历史消息。模型使用 src/llms.py 中的 get_default_model。
"""

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import HumanMessage

from src.llms import get_default_model


def run_demo() -> None:
    # 使用默认模型与内存检查点器
    llm = get_default_model()
    checkpointer = InMemorySaver()
    agent = create_agent(
        model=llm,
        tools=[],
        system_prompt="保持回答简洁，用之前的对话信息回答用户问题。",
        checkpointer=checkpointer,
    )

    # 同一 thread_id 共享短期记忆
    config = {"configurable": {"thread_id": "memory-demo-thread"}}
    user_queries = [
        "你好，我叫小明。",
        "请记住我的名字，并简短确认。",
        "我叫什么名字？",
    ]

    for text in user_queries:
        messages = [HumanMessage(content=text)]
        messages = agent.invoke({"messages": messages}, config)
        for m in messages["messages"]:
            m.pretty_print()
        print()


if __name__ == "__main__":
    run_demo()
