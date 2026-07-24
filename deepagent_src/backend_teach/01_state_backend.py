import os

os.environ["LANGSMITH_TRACING"] = "false"

from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from langgraph.checkpoint.memory import InMemorySaver

from deepagent_src.llms import gpt_model


def main():
    agent = create_deep_agent(
        model=gpt_model,
        backend=StateBackend(),
        checkpointer=InMemorySaver(),
    )
    config = {"configurable": {"thread_id": "state-backend-demo"}}

    agent.invoke(
        {"messages": [{"role": "user", "content": "把‘我正在学习 StateBackend’写入 /note.txt"}]},
        config,
    )
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "读取 /note.txt，并告诉我文件内容"}]},
        config,
    )
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
