"""工具读写短期记忆示例。

- 工具读取 runtime.state。
- 工具通过 Command(update=...) 写回状态与消息。
"""

from dataclasses import dataclass

from langchain.agents import AgentState, create_agent
from langchain.messages import HumanMessage
from langchain.tools import ToolRuntime, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from src.llms import get_default_model


@dataclass
class CustomState(AgentState):
    user_name: str | None = None


@tool
def update_user(runtime: ToolRuntime) -> Command:
    """记录用户姓名到状态。"""
    user_name = runtime.state.get("user_name")
    if user_name:
        return Command(update={"messages": []})
    return Command(
        update={
            "user_name": "李雷",
            "messages": [
                {"role": "tool", "content": "已记录用户姓名为李雷", "tool_call_id": runtime.tool_call_id}
            ],
        }
    )


@tool
def greet(runtime: ToolRuntime) -> str | Command:
    """基于已记录的用户姓名进行问候。"""
    user_name = runtime.state.get("user_name")
    if not user_name:
        return Command(
            update={
                "messages": [
                    {
                        "role": "tool",
                        "content": "请先调用 update_user 以获取用户名。",
                        "tool_call_id": runtime.tool_call_id,
                    }
                ]
            }
        )
    return f"你好，{user_name}！"


def run_demo() -> None:
    agent = create_agent(
        model=get_default_model(),
        tools=[update_user, greet],
        state_schema=CustomState,
        checkpointer=InMemorySaver(),
        system_prompt=(
            "你必须先调用 update_user 以记录用户姓名，然后调用 greet 完成问候；"
            "禁止在未调用工具的情况下直接回答。"
        ),
    )

    config = {"configurable": {"thread_id": "tool-state-thread"}}
    first = agent.invoke({"messages": [HumanMessage(content="打个招呼")]}, config)
    for m in first["messages"]:
        m.pretty_print()
    second = agent.invoke({"messages": [HumanMessage(content="再说一次")]}, config)
    for m in second["messages"]:
        m.pretty_print()


if __name__ == "__main__":
    run_demo()
