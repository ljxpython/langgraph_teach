from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import AgentState, after_model, before_model
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langgraph.runtime import Runtime

event_log: list[str] = []


@before_model(name="log_before_model")
def log_before_model(
    state: AgentState,
    runtime: Runtime[Any],
) -> dict[str, Any] | None:
    event_log.append(f"before_model:{len(state['messages'])}")
    return None


@after_model(name="log_after_model")
def log_after_model(
    state: AgentState,
    runtime: Runtime[Any],
) -> dict[str, Any] | None:
    event_log.append(f"after_model:{state['messages'][-1].text}")
    return None


def main() -> None:
    event_log.clear()
    agent = create_agent(
        model=FakeListChatModel(responses=["MIDDLEWARE_OK"]),
        tools=[],
        middleware=[log_before_model, log_after_model],
    )
    state = agent.invoke({"messages": [{"role": "user", "content": "hi"}]})
    final_text = state["messages"][-1].text

    print("event_log:", event_log)
    print("final:", final_text)

    assert event_log == [
        "before_model:1",
        "after_model:MIDDLEWARE_OK",
    ], event_log
    assert final_text == "MIDDLEWARE_OK", final_text
    print("middleware lifecycle hooks local check ok")


if __name__ == "__main__":
    main()
