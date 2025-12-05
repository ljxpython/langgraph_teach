"""自定义 AgentState + before/after 中间件示例。

- 自定义状态：额外记录 user_id、preferences。
- before_model：截断消息（保留首条 + 最近 4 条），避免上下文过长。
- after_model：过滤含敏感词的回复。
"""

from dataclasses import dataclass
from typing import Any

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import after_model, before_model
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.runtime import Runtime

from src.llms import get_default_model


@dataclass
class CustomState(AgentState):
    user_id: str
    preferences: dict[str, Any]


@before_model
def trim_messages(state: CustomState, runtime: Runtime) -> dict[str, Any] | None:
    messages = state["messages"]
    if len(messages) <= 5:
        return None
    print(messages)
    first = messages[0]
    recent = messages[-4:]
    return {"messages": [first, *recent]}


@after_model
def filter_sensitive(state: CustomState, runtime: Runtime) -> dict[str, Any] | None:
    banned = ["密码", "secret"]
    last = state["messages"][-1]
    if any(word in getattr(last, "content", "") for word in banned):
        return {"messages": state["messages"][:-1]}
    return None


def run_demo() -> None:
    agent = create_agent(
        model=get_default_model(),
        tools=[],
        state_schema=CustomState,
        checkpointer=InMemorySaver(),
        middleware=[trim_messages, filter_sensitive],
        system_prompt="根据用户偏好回答，保持简洁。",
    )

    config = {"configurable": {"thread_id": "middleware-thread"}}
    payload = {
        "messages": [HumanMessage(content="我叫李雷，喜欢简短回答。")],
        "user_id": "user_001",
        "preferences": {"style": "concise"},
    }
    first = agent.invoke(payload, config)
    for m in first["messages"]:
        m.pretty_print()

    second = agent.invoke(
        {
            "messages": [HumanMessage(content="重复说几次我的名字，越多越好")],
            "user_id": "user_001",
            "preferences": {"style": "concise"},
        },
        config,
    )
    for m in second["messages"]:
        m.pretty_print()


if __name__ == "__main__":
    run_demo()
