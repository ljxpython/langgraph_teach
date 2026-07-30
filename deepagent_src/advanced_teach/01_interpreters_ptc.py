from __future__ import annotations

import os
from importlib.util import find_spec
from typing import Any

from deepagents import create_deep_agent
from langchain.messages import HumanMessage
from langchain_core.tools import tool

from deepagent_src.llms import get_gpt_model


PRODUCTS: dict[str, dict[str, Any]] = {
    "starter": {"price": 19, "seats": 3},
    "team": {"price": 79, "seats": 12},
    "enterprise": {"price": 249, "seats": 80},
}


@tool
def lookup_plan(plan: str) -> dict[str, Any]:
    """Look up a subscription plan by name."""
    key = plan.strip().lower()
    if key not in PRODUCTS:
        return {"plan": plan, "found": False}
    return {"plan": key, "found": True, **PRODUCTS[key]}


@tool
def discount_amount(price: int, percent: int) -> dict[str, int]:
    """Calculate the final price after a percentage discount."""
    return {"price": price, "percent": percent, "final": round(price * (100 - percent) / 100)}


def require_quickjs() -> None:
    if find_spec("langchain_quickjs") is not None:
        return
    raise SystemExit(
        "缺少 langchain_quickjs，当前项目还不能运行 Deep Agents Interpreter/PTC。\n"
        "安装命令：uv add \"deepagents[quickjs]\"\n"
        "注意：这是包管理操作，执行前要确认依赖变更。"
    )


def tool_call_names(messages: list[Any]) -> list[str]:
    names: list[str] = []
    for message in messages:
        for call in getattr(message, "tool_calls", None) or []:
            names.append(call.get("name", ""))
    return names


def main() -> None:
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    require_quickjs()

    from langchain_quickjs import CodeInterpreterMiddleware

    agent = create_deep_agent(
        model=get_gpt_model(disable_tool_streaming=True),
        tools=[lookup_plan, discount_amount],
        middleware=[CodeInterpreterMiddleware(ptc=["lookup_plan", "discount_amount"])],
        subagents=[],
        system_prompt=(
            "你是 Interpreter/PTC 教学助手。必须用 eval 写 JavaScript，"
            "在 eval 里通过 tools.lookupPlan 和 tools.discountAmount 查询 starter、team、enterprise，"
            "计算每个套餐打 20% 折后的价格，只返回一张简短中文表。"
        ),
    )

    state = agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "请用 Interpreter 的 PTC 一次性处理 starter、team、enterprise 三个套餐，"
                        "查询原价并计算 20% 折后价。"
                    )
                )
            ]
        }
    )

    for message in state["messages"]:
        message.pretty_print()

    names = tool_call_names(state["messages"])
    assert "eval" in names, names
    final_text = state["messages"][-1].text
    assert "starter" in final_text.lower()
    assert "team" in final_text.lower()
    assert "enterprise" in final_text.lower()
    print("interpreter ptc real call ok")


if __name__ == "__main__":
    main()
