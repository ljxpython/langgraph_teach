from collections.abc import Callable
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langchain.messages import HumanMessage
from langchain.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from src.llms import get_default_model

DEFAULT_SYSTEM_PROMPT = """你是中间件演示协调者：
- 多步骤任务要写 todo 列表并随时更新
- 大输出或多次调用工具时，可将中间结果写入文件系统
- 需要深入分析或写作时，委派给专用子智能体
保持回复精简，必要时调用 task()、write_todos、filesystem 工具。"""


@tool
def outline(title: str) -> str:
    """生成简短写作提纲。"""
    return f"Outline for {title}: 背景/要点/总结"


def build_subagents() -> list[dict[str, Any]]:
    writer_subagent = {
        "name": "writer-agent",
        "description": "整理思路并生成简短报告或说明",
        "system_prompt": """你是写作助手：
1) 如果缺少结构，先生成提纲
2) 输出 150-200 字摘要，突出行动项""",
        "tools": [outline],
    }
    return [writer_subagent]


def build_composite_backend():
    return lambda rt: CompositeBackend(
        default=StateBackend(rt),
        routes={"/memories/": StoreBackend(rt)},
    )


def build_middleware_agent(store: Any | None = None) -> Callable[..., Any]:
    """创建带默认中间件（规划/文件系统/子智能体）的 deep agent，并配置子智能体与存储。"""
    selected_store = store or InMemoryStore()

    return create_deep_agent(
        model=get_default_model(),
        backend=build_composite_backend(),
        store=selected_store,
        # create_deep_agent 默认会挂载 TodoListMiddleware / FilesystemMiddleware / SubAgentMiddleware
        # 通过 subagents 参数注入自定义子智能体即可，避免重复实例导致报错
        subagents=build_subagents(),
        checkpointer=MemorySaver(),
        system_prompt=DEFAULT_SYSTEM_PROMPT,
    )


def run_demo_request(agent: Callable[..., Any], user_message: str, thread_id: str = "middleware-demo") -> Any:
    """统一调用入口，使用 HumanMessage 并 pretty_print 输出。"""
    messages = [HumanMessage(content=user_message)]
    result = agent.invoke(
        {"messages": messages},
        config={"configurable": {"thread_id": thread_id}},
    )
    for message in result["messages"]:
        message.pretty_print()
    return result


if __name__ == "__main__":
    demo_agent = build_middleware_agent()
    run_demo_request(
        demo_agent,
        "请规划一份学习计划，并把关键记忆写到 /memories/plan.md，临时笔记写到 /notes.txt，必要时用子智能体生成摘要。",
    )
