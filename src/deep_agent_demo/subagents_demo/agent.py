from collections.abc import Callable
from typing import Any

from deepagents import create_deep_agent
from langchain.tools import tool
from langchain.messages import HumanMessage

from src.llms import get_default_model

DEFAULT_SYSTEM_PROMPT = """你是一个协调者，负责拆解任务并将具体工作委派给合适的子智能体。
- 复杂研究交给 research-agent
- 结构化写作交给 writer-agent
保持回复简洁，必要时调用 task() 触发子智能体。"""


@tool
def search_notes(topic: str) -> str:
    """模拟检索资料，真实场景可换成网络搜索或文件检索工具。"""
    return f"Found 3 notes about {topic}"


@tool
def write_outline(title: str) -> str:
    """生成一个简单的大纲，用于写手子智能体演示。"""
    return f"Outline for {title}: [背景, 关键点, 结论]"


def build_subagents() -> list[dict[str, Any]]:
    research_subagent = {
        "name": "research-agent",
        "description": "负责检索与信息汇总，适合较复杂的研究型问题",
        "system_prompt": """你是研究专家，步骤：
1) 拆分查询
2) 调用 search_notes 收集要点
3) 汇总关键发现，控制在 200 字以内""",
        "tools": [search_notes],
    }

    writer_subagent = {
        "name": "writer-agent",
        "description": "负责整理结构化输出（摘要、报告、说明）",
        "system_prompt": """你是写作专家，步骤：
1) 根据需求生成提纲（必要时调用 write_outline）
2) 输出简洁成稿，突出行动项
3) 控制在 200 字以内""",
        "tools": [write_outline],
    }
    return [research_subagent, writer_subagent]


def build_subagent_demo() -> Callable[..., Any]:
    """创建带子智能体的主 Agent。"""
    return create_deep_agent(
        model=get_default_model(),
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        subagents=build_subagents(),
    )


def run_demo_request(agent: Callable[..., Any], user_message: str, thread_id: str = "subagents-demo") -> Any:
    """统一调用入口，使用 HumanMessage，并打印对话。"""
    messages = [HumanMessage(content=user_message)]
    result = agent.invoke(
        {"messages": messages},
        config={"configurable": {"thread_id": thread_id}},
    )
    for message in result["messages"]:
        message.pretty_print()
    return result


if __name__ == "__main__":
    demo_agent = build_subagent_demo()
    run_demo_request(
        demo_agent,
        "请帮我研究“向量数据库应用”，并输出一个简短报告。",
    )
