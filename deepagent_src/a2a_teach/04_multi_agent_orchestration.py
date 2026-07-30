from __future__ import annotations

import asyncio

import httpx
import uvicorn
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
from langchain.messages import HumanMessage, ToolMessage
from langchain.tools import tool

from deepagent_src.llms import get_gpt_model

QUOTE_AGENT_URL = "http://127.0.0.1:8770"
RISK_AGENT_URL = "http://127.0.0.1:8771"


class SpecialistExecutor(AgentExecutor):
    def __init__(self, instruction: str) -> None:
        self.agent = create_deep_agent(
            model=get_gpt_model(disable_tool_streaming=True),
            subagents=[],
            system_prompt=instruction,
        )
        self.invocations = 0

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
        self.invocations += 1
        state = await self.agent.ainvoke(
            {"messages": [HumanMessage(content=context.get_user_input())]}
        )
        await updater.add_artifact(
            [new_text_part(state["messages"][-1].text)],
            name="specialist-result",
        )
        await updater.complete()

    async def cancel(self, context: RequestContext, event_queue) -> None:
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.cancel()


def build_specialist_app(
    *,
    name: str,
    url: str,
    description: str,
    executor: AgentExecutor,
) -> FastAPI:
    card = AgentCard(
        name=name,
        version="0.1.0",
        description=description,
        supported_interfaces=[
            AgentInterface(
                protocol_binding=TransportProtocol.JSONRPC,
                url=f"{url}/",
                protocol_version="1.0",
            )
        ],
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id=name,
                name=name,
                description=description,
                tags=["invoice", "specialist"],
            )
        ],
    )
    handler = DefaultRequestHandler(executor, InMemoryTaskStore(), card)
    app = FastAPI()
    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(card),
        jsonrpc_routes=create_jsonrpc_routes(handler, rpc_url="/"),
    )
    return app


async def invoke_remote_agent(url: str, request_text: str) -> str:
    async with httpx.AsyncClient(timeout=60) as http_client:
        client = await create_client(
            url,
            ClientConfig(streaming=False, httpx_client=http_client),
        )
        request = SendMessageRequest(
            message=new_text_message(request_text, role=Role.ROLE_USER),
            configuration=SendMessageConfiguration(),
        )
        responses = [response async for response in client.send_message(request)]
        await client.close()

    task = responses[-1].task
    if task.status.state != TaskState.TASK_STATE_COMPLETED:
        raise RuntimeError(f"remote task failed: {TaskState.Name(task.status.state)}")
    return "\n".join(get_text_parts(task.artifacts[-1].parts))


@tool
async def ask_specialists(request: str) -> str:
    """Ask the quote and risk A2A specialists concurrently for one invoice request."""
    quote, risk = await asyncio.gather(
        invoke_remote_agent(QUOTE_AGENT_URL, request),
        invoke_remote_agent(RISK_AGENT_URL, request),
    )
    return f"quote specialist: {quote}\nrisk specialist: {risk}"


async def wait_for_servers() -> None:
    async with httpx.AsyncClient() as http_client:
        for _ in range(50):
            try:
                responses = await asyncio.gather(
                    http_client.get(f"{QUOTE_AGENT_URL}/.well-known/agent-card.json"),
                    http_client.get(f"{RISK_AGENT_URL}/.well-known/agent-card.json"),
                )
            except httpx.ConnectError:
                await asyncio.sleep(0.05)
                continue
            if all(response.is_success for response in responses):
                return
            await asyncio.sleep(0.05)
    raise RuntimeError("specialist A2A servers did not start")


async def main() -> None:
    quote_executor = SpecialistExecutor(
        "你是报价专家。用户询问 inv-3001 时，只回复 "
        "`QUOTE_AGENT: inv-3001 total=USD 108.00`。"
    )
    risk_executor = SpecialistExecutor(
        "你是风险专家。用户询问 inv-3001 时，只回复 "
        "`RISK_AGENT: inv-3001 status=approved`。"
    )
    servers = [
        uvicorn.Server(
            uvicorn.Config(
                build_specialist_app(
                    name="quote-specialist",
                    url=QUOTE_AGENT_URL,
                    description="Returns invoice quotes.",
                    executor=quote_executor,
                ),
                host="127.0.0.1",
                port=8770,
                log_level="error",
                access_log=False,
            )
        ),
        uvicorn.Server(
            uvicorn.Config(
                build_specialist_app(
                    name="risk-specialist",
                    url=RISK_AGENT_URL,
                    description="Returns invoice risk decisions.",
                    executor=risk_executor,
                ),
                host="127.0.0.1",
                port=8771,
                log_level="error",
                access_log=False,
            )
        ),
    ]
    server_tasks = [asyncio.create_task(server.serve()) for server in servers]

    try:
        await wait_for_servers()
        coordinator = create_deep_agent(
            model=get_gpt_model(disable_tool_streaming=True),
            tools=[ask_specialists],
            subagents=[],
            system_prompt=(
                "你是发票协调 Agent。对每个用户请求，必须且只能调用一次 "
                "ask_specialists；随后用中文汇总报价和风险结论，不能编造数据。"
            ),
        )
        state = await coordinator.ainvoke(
            {"messages": [HumanMessage(content="查询发票 inv-3001 的报价和风险状态。")]}
        )
        answer = state["messages"][-1].text
        coordinator_called = any(
            isinstance(message, ToolMessage) and message.name == "ask_specialists"
            for message in state["messages"]
        )

        print("coordinator_tool_called:", coordinator_called)
        print("quote_agent_calls:", quote_executor.invocations)
        print("risk_agent_calls:", risk_executor.invocations)
        print("answer:", answer)

        assert coordinator_called
        assert quote_executor.invocations == 1
        assert risk_executor.invocations == 1
        assert "108.00" in answer
        assert "approved" in answer
        print("multi a2a deep agent orchestration ok")
    finally:
        for server in servers:
            server.should_exit = True
        await asyncio.gather(*server_tasks)


if __name__ == "__main__":
    asyncio.run(main())
