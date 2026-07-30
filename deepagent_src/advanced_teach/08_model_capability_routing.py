from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from deepagents import create_deep_agent
from langchain.agents.middleware import ModelRequest, ModelResponse, wrap_model_call
from langchain_core.language_models import BaseChatModel
from langchain.messages import HumanMessage

from deepagent_src.llms import get_default_model, get_gpt_model

Capability = Literal["text", "tool_calling", "vision_input", "vision_tool_result"]


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    capabilities: frozenset[Capability]
    create: Callable[[], BaseChatModel]


@dataclass(frozen=True)
class ModelRoute:
    model_id: str
    required_capabilities: frozenset[Capability]


MODEL_REGISTRY = {
    "deepseek-text": ModelSpec(
        model_id="deepseek-text",
        capabilities=frozenset({"text", "tool_calling"}),
        create=get_default_model,
    ),
    "gpt-vision-input": ModelSpec(
        model_id="gpt-vision-input",
        capabilities=frozenset({"text", "tool_calling", "vision_input"}),
        create=lambda: get_gpt_model(disable_tool_streaming=True),
    ),
}


def resolve_model(route: ModelRoute) -> ModelSpec:
    model = MODEL_REGISTRY.get(route.model_id)
    if model is None:
        raise ValueError(f"不允许选择模型：{route.model_id}")
    missing = route.required_capabilities - model.capabilities
    if missing:
        raise ValueError(
            f"模型 {route.model_id} 不满足能力要求：{', '.join(sorted(missing))}"
        )
    return model


@wrap_model_call
def select_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    route = request.runtime.context
    if not isinstance(route, ModelRoute):
        raise ValueError("运行时 context 必须是 ModelRoute")
    model = resolve_model(route)
    print(f"selected_model: {model.model_id}")
    return handler(request.override(model=model.create()))


def main() -> None:
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

    selected = resolve_model(
        ModelRoute(
            model_id="gpt-vision-input",
            required_capabilities=frozenset({"vision_input"}),
        )
    )
    assert selected.model_id == "gpt-vision-input"

    try:
        resolve_model(
            ModelRoute(
                model_id="deepseek-text",
                required_capabilities=frozenset({"vision_input"}),
            )
        )
    except ValueError as exc:
        print("rejected_route:", exc)
    else:
        raise AssertionError("缺少 vision_input 的模型不应通过路由校验")

    agent = create_deep_agent(
        model=get_gpt_model(disable_tool_streaming=True),
        middleware=[select_model],
        subagents=[],
        context_schema=ModelRoute,
        system_prompt="你是模型路由教学助手。只回复 ROUTER_OK。",
    )
    state = agent.invoke(
        {"messages": [HumanMessage(content="验证运行时模型路由。")]},
        context=ModelRoute(
            model_id="gpt-vision-input",
            required_capabilities=frozenset({"vision_input"}),
        ),
    )
    final_text = state["messages"][-1].text
    print("final:", final_text)
    assert "router_ok" in final_text.lower(), final_text
    print("model capability routing real call ok")


if __name__ == "__main__":
    main()
