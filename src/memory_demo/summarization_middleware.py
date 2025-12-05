"""自定义摘要中间件示例（兼容当前版本）。

使用 before_model 钩子在消息过多时调用模型生成摘要，压缩上下文。
"""

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import before_model
from langchain.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.runtime import Runtime

from src.llms import get_default_model


SUMMARY_THRESHOLD = 8  # 超过该条数触发摘要
KEEP_RECENT = 6  # 保留最近消息条数


@before_model
def summarize_if_needed(state: AgentState, runtime: Runtime):
    messages = state["messages"]
    if len(messages) <= SUMMARY_THRESHOLD:
        return None

    summarizer = get_default_model()
    summary_prompt = [
        HumanMessage(content="请用中文简要总结以下对话，用于压缩上下文："),
        *messages[:-KEEP_RECENT],
    ]
    summary = summarizer.invoke(summary_prompt)
    new_messages = [
        SystemMessage(content=f"对话摘要：{summary.content}"),
        *messages[-KEEP_RECENT:],
    ]
    return {"messages": new_messages}


def run_demo() -> None:
    agent = create_agent(
        model=get_default_model(),
        tools=[],
        middleware=[summarize_if_needed],
        checkpointer=InMemorySaver(),
        system_prompt="保持简洁，当历史过长时使用摘要。",
    )

    config = {"configurable": {"thread_id": "summary-thread"}}
    prompts = [
        "我叫小明。",
        "喜欢跑步。",
        "喜欢狗。",
        "喜欢咖啡。",
        "我最爱的颜色是蓝色。",
        "我最爱的电影是科幻片。",
        "总结一下我是谁。",
        "再问一次，我喜欢什么？",
    ]

    messages = []
    for text in prompts:
        messages = agent.invoke({"messages": [HumanMessage(content=text)]}, config)

    result = agent.invoke(
        {"messages": [HumanMessage(content="请再说一遍我的喜好。")]}, config
    )
    for m in result["messages"]:
        m.pretty_print()


if __name__ == "__main__":
    run_demo()
