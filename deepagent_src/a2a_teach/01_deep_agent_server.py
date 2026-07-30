from __future__ import annotations

import asyncio
import os

import httpx
from a2a.client import ClientConfig, create_client
from a2a.helpers.proto_helpers import (
    get_text_parts,
    new_text_message,
    new_text_part,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes.agent_card_routes import create_agent_card_routes
from a2a.server.routes.fastapi_routes import add_a2a_routes_to_fastapi
from a2a.server.routes.jsonrpc_routes import create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    Role,
    SendMessageConfiguration,
    SendMessageRequest,
    Task,
    TaskState,
    TaskStatus,
)
from a2a.utils.constants import TransportProtocol
from deepagents import create_deep_agent
from fastapi import FastAPI
from langchain.messages import HumanMessage

from deepagent_src.llms import get_gpt_model

AGENT_URL = "http://a2a.local"


class RemoteDeepAgentExecutor(AgentExecutor):
    def __init__(self) -> None:
        self.agent = create_deep_agent(
            model=get_gpt_model(disable_tool_streaming=True),
            subagents=[],
            system_prompt=(
                "你是通过 A2A 暴露的远程 Deep Agent。"
                "用户会提供一个发票 ID。只回复 `A2A_REMOTE_OK: <发票ID>`。"
            ),
        )

    async def execute(self, context: RequestContext, event_queue) -> None:
        await event_queue.enqueue_event(
            Task(
                id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_SUBMITTED),
            )
        )
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.start_work()

        state = await self.agent.ainvoke(
            {"messages": [HumanMessage(content=context.get_user_input())]}
        )
        answer = state["messages"][-1].text
        await updater.add_artifact([new_text_part(answer)], name="deep-agent-answer")
        await updater.complete()

    async def cancel(self, context: RequestContext, event_queue) -> None:
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.cancel()


def build_a2a_app() -> FastAPI:
    card = AgentCard(
        name="invoice-a2a-deep-agent",
        version="0.1.0",
        description="A Deep Agent exposed through the A2A protocol.",
        supported_interfaces=[
            AgentInterface(
                protocol_binding=TransportProtocol.JSONRPC,
                url=f"{AGENT_URL}/",
            )
        ],
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="invoice-id-echo",
                name="Invoice ID response",
                description="Returns the invoice ID supplied by the caller.",
                tags=["invoice", "teaching"],
            )
        ],
    )
    handler = DefaultRequestHandler(
        RemoteDeepAgentExecutor(),
        InMemoryTaskStore(),
        card,
    )
    app = FastAPI()
    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(card),
        jsonrpc_routes=create_jsonrpc_routes(handler, rpc_url="/"),
    )
    return app


async def main() -> None:
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

    app = build_a2a_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url=AGENT_URL,
    ) as http_client:
        client = await create_client(
            AGENT_URL,
            ClientConfig(streaming=False, httpx_client=http_client),
        )
        request = SendMessageRequest(
            message=new_text_message(
                "请处理发票 ID：inv-1001。",
                role=Role.ROLE_USER,
            ),
            configuration=SendMessageConfiguration(),
        )
        responses = [response async for response in client.send_message(request)]
        await client.close()

    task = responses[-1].task
    answer = "\n".join(get_text_parts(task.artifacts[-1].parts))
    print("task_state:", TaskState.Name(task.status.state))
    print("artifact:", answer)
    assert task.status.state == TaskState.TASK_STATE_COMPLETED
    assert answer == "A2A_REMOTE_OK: inv-1001", answer
    print("a2a deep agent real call ok")


if __name__ == "__main__":
    asyncio.run(main())
