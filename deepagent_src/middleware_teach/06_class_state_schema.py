from __future__ import annotations

from typing import Any, NotRequired

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, AgentState
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langgraph.runtime import Runtime


class AuditState(AgentState):
    model_call_count: NotRequired[int]
    last_model_text: NotRequired[str]


class AuditStateMiddleware(AgentMiddleware[AuditState, Any]):
    state_schema = AuditState

    def before_model(
        self,
        state: AuditState,
        runtime: Runtime[Any],
    ) -> dict[str, Any] | None:
        return {"model_call_count": state.get("model_call_count", 0) + 1}

    def after_model(
        self,
        state: AuditState,
        runtime: Runtime[Any],
    ) -> dict[str, Any] | None:
        return {"last_model_text": state["messages"][-1].text}


def main() -> None:
    agent = create_agent(
        model=FakeListChatModel(responses=["STATE_SCHEMA_OK"]),
        tools=[],
        middleware=[AuditStateMiddleware()],
    )
    state = agent.invoke({"messages": [{"role": "user", "content": "hi"}]})

    print("model_call_count:", state["model_call_count"])
    print("last_model_text:", state["last_model_text"])
    print("final:", state["messages"][-1].text)

    assert state["model_call_count"] == 1, state
    assert state["last_model_text"] == "STATE_SCHEMA_OK", state
    assert state["messages"][-1].text == "STATE_SCHEMA_OK"
    print("class middleware state_schema local check ok")


if __name__ == "__main__":
    main()
