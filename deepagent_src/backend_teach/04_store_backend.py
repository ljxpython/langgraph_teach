import os

os.environ["LANGSMITH_TRACING"] = "false"

from deepagents import create_deep_agent
from deepagents.backends import StoreBackend
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from deepagent_src.llms import gpt_model


def main():
    agent = create_deep_agent(
        model=gpt_model,
        backend=StoreBackend(namespace=lambda _rt: ("demo-user",)),
        store=InMemoryStore(),
        checkpointer=InMemorySaver(),
    )

    agent.invoke(
        {"messages": [{"role": "user", "content": "把‘用户喜欢精简代码’写入 /memory.txt"}]},
        {"configurable": {"thread_id": "thread-a"}},
    )
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "读取 /memory.txt，告诉我用户偏好"}]},
        {"configurable": {"thread_id": "thread-b"}},
    )
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
