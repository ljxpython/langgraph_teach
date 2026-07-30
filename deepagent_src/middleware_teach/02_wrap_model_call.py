from __future__ import annotations

from collections.abc import Callable

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, ModelResponse, wrap_model_call
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage

handler_calls = 0


@wrap_model_call(name="guard_and_rewrite_model")
def guard_and_rewrite_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    global handler_calls

    user_text = request.state["messages"][-1].text
    if "skip-model" in user_text:
        return ModelResponse(result=[AIMessage(content="SHORT_CIRCUIT_OK")])

    handler_calls += 1
    response = handler(request)
    model_text = response.result[0].text
    return ModelResponse(result=[AIMessage(content=f"WRAPPED:{model_text}")])


def main() -> None:
    global handler_calls
    handler_calls = 0

    agent = create_agent(
        model=FakeListChatModel(responses=["MODEL_OK"]),
        tools=[],
        middleware=[guard_and_rewrite_model],
    )

    normal_state = agent.invoke(
        {"messages": [{"role": "user", "content": "call model"}]}
    )
    skipped_state = agent.invoke(
        {"messages": [{"role": "user", "content": "skip-model"}]}
    )

    normal_text = normal_state["messages"][-1].text
    skipped_text = skipped_state["messages"][-1].text

    print("normal:", normal_text)
    print("skipped:", skipped_text)
    print("handler_calls:", handler_calls)

    assert normal_text == "WRAPPED:MODEL_OK", normal_text
    assert skipped_text == "SHORT_CIRCUIT_OK", skipped_text
    assert handler_calls == 1, handler_calls
    print("wrap_model_call local check ok")


if __name__ == "__main__":
    main()
