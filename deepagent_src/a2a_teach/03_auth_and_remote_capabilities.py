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
from a2a.server.context import ServerCallContext
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes.agent_card_routes import create_agent_card_routes
from a2a.server.routes.common import ServerCallContextBuilder
from a2a.server.routes.fastapi_routes import add_a2a_routes_to_fastapi
from a2a.server.routes.jsonrpc_routes import create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    HTTPAuthSecurityScheme,
    Role,
    SecurityRequirement,
    SecurityScheme,
    SendMessageConfiguration,
    SendMessageRequest,
    StringList,
    Task,
    TaskState,
    TaskStatus,
)
from a2a.utils.constants import TransportProtocol
from deepagents import create_deep_agent
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from langchain.messages import HumanMessage, ToolMessage
from langchain.tools import tool
from starlette.middleware.base import BaseHTTPMiddleware

from deepagent_src.llms import get_gpt_model

AGENT_URL = "http://127.0.0.1:8766"
TOKEN = "billing-demo-token"
CALLERS = {
    TOKEN: {
        "identity": "billing-operator-42",
        "capabilities": {"invoice_lookup"},
    }
}


@tool
def lookup_invoice(invoice_id: str) -> str:
    """Query one authorized invoice by invoice ID."""
    if invoice_id != "inv-2048":
        return f"Invoice {invoice_id}: not found."
    return "Invoice inv-2048: status=paid; amount=USD 128.50."


class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/.well-known/agent-card.json":
            return await call_next(request)

        token = request.headers.get("authorization", "").removeprefix("Bearer ")
        if token not in CALLERS:
            return JSONResponse(
                status_code=401,
                content={"detail": "valid Bearer token required"},
            )
        return await call_next(request)


class AuthContextBuilder(ServerCallContextBuilder):
    def build(self, request: Request) -> ServerCallContext:
        token = request.headers["authorization"].removeprefix("Bearer ")
        caller = CALLERS[token]
        return ServerCallContext(
            tenant=caller["identity"],
            state={
                "headers": dict(request.headers),
                "identity": caller["identity"],
                "allowed_capabilities": caller["capabilities"],
            },
        )


class RemoteBillingExecutor(AgentExecutor):
    def __init__(self) -> None:
        self.agent = create_deep_agent(
            model=get_gpt_model(disable_tool_streaming=True),
            tools=[lookup_invoice],
            subagents=[],
            system_prompt=(
                "你是受保护的远程发票查询 Agent。"
                "当用户请求查询发票时，必须先调用 lookup_invoice，"
                "然后只原样回复工具结果。"
            ),
        )
        self.agent_invocations = 0
        self.tool_called = False

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

        capabilities = context.call_context.state["allowed_capabilities"]
        if "invoice_lookup" not in capabilities:
            await updater.add_artifact(
                [new_text_part("A2A_FORBIDDEN_CAPABILITY: invoice_lookup")],
                name="authorization-error",
            )
            await updater.complete()
            return

        self.agent_invocations += 1
        state = await self.agent.ainvoke(
            {"messages": [HumanMessage(content=context.get_user_input())]}
        )
        self.tool_called = any(
            isinstance(message, ToolMessage) and message.name == "lookup_invoice"
            for message in state["messages"]
        )
        answer = state["messages"][-1].text
        await updater.add_artifact([new_text_part(answer)], name="invoice-result")
        await updater.complete()

    async def cancel(self, context: RequestContext, event_queue) -> None:
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.cancel()


def build_a2a_app(executor: AgentExecutor) -> FastAPI:
    security_requirement = SecurityRequirement(
        schemes={"bearerAuth": StringList(list=[])}
    )
    card = AgentCard(
        name="protected-invoice-deep-agent",
        version="0.1.0",
        description="An authenticated A2A Deep Agent for invoice lookups.",
        supported_interfaces=[
            AgentInterface(
                protocol_binding=TransportProtocol.JSONRPC,
                url=f"{AGENT_URL}/",
                protocol_version="1.0",
            )
        ],
        capabilities=AgentCapabilities(streaming=False),
        security_schemes={
            "bearerAuth": SecurityScheme(
                http_auth_security_scheme=HTTPAuthSecurityScheme(
                    scheme="bearer",
                    bearer_format="demo-token",
                )
            )
        },
        security_requirements=[security_requirement],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="invoice-lookup",
                name="Invoice lookup",
                description="Returns the status and amount for an authorized invoice.",
                tags=["billing", "authorized"],
                security_requirements=[security_requirement],
            )
        ],
    )
    handler = DefaultRequestHandler(executor, InMemoryTaskStore(), card)
    app = FastAPI()
    app.add_middleware(BearerAuthMiddleware)
    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(card),
        jsonrpc_routes=create_jsonrpc_routes(
            handler,
            rpc_url="/",
            context_builder=AuthContextBuilder(),
        ),
    )
    return app


async def wait_for_server() -> None:
    async with httpx.AsyncClient() as http_client:
        for _ in range(50):
            try:
                response = await http_client.get(
                    f"{AGENT_URL}/.well-known/agent-card.json"
                )
            except httpx.ConnectError:
                await asyncio.sleep(0.05)
                continue
            if response.is_success:
                return
            await asyncio.sleep(0.05)
    raise RuntimeError("A2A server did not start")


async def main() -> None:
    executor = RemoteBillingExecutor()
    server = uvicorn.Server(
        uvicorn.Config(
            build_a2a_app(executor),
            host="127.0.0.1",
            port=8766,
            log_level="error",
            access_log=False,
        )
    )
    server_task = asyncio.create_task(server.serve())

    try:
        await wait_for_server()
        async with httpx.AsyncClient() as anonymous_client:
            denied = await anonymous_client.post(f"{AGENT_URL}/", json={})
        print("anonymous_status:", denied.status_code)
        assert denied.status_code == 401

        async with httpx.AsyncClient(
            headers={"Authorization": f"Bearer {TOKEN}"},
            timeout=60,
        ) as http_client:
            client = await create_client(
                AGENT_URL,
                ClientConfig(streaming=False, httpx_client=http_client),
            )
            request = SendMessageRequest(
                message=new_text_message(
                    "查询发票 inv-2048。",
                    role=Role.ROLE_USER,
                ),
                configuration=SendMessageConfiguration(),
            )
            responses = [response async for response in client.send_message(request)]
            await client.close()

        task = responses[-1].task
        answer = "\n".join(get_text_parts(task.artifacts[-1].parts))
        print("task_state:", TaskState.Name(task.status.state))
        print("tool_called:", executor.tool_called)
        print("artifact:", answer)

        assert task.status.state == TaskState.TASK_STATE_COMPLETED
        assert executor.agent_invocations == 1
        assert executor.tool_called
        assert "inv-2048" in answer and "paid" in answer
        print("authenticated a2a deep agent real tool call ok")
    finally:
        server.should_exit = True
        await server_task


if __name__ == "__main__":
    asyncio.run(main())
