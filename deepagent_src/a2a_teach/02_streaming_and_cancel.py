from __future__ import annotations

import asyncio

import httpx
import uvicorn
from a2a.client import ClientConfig, create_client
from a2a.helpers.proto_helpers import new_text_message, new_text_part
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
    CancelTaskRequest,
    Role,
    SendMessageConfiguration,
    SendMessageRequest,
    Task,
    TaskState,
    TaskStatus,
)
from a2a.utils.constants import TransportProtocol
from fastapi import FastAPI

AGENT_URL = "http://127.0.0.1:8765"


class SlowExecutor(AgentExecutor):
    """用可控慢任务验证 A2A 生命周期，不依赖模型响应时间。"""

    def __init__(self) -> None:
        self.cancel_called = False

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
        await updater.add_artifact(
            [new_text_part("progress: remote task is working")],
            name="progress",
            last_chunk=False,
        )
        await asyncio.sleep(5)
        await updater.add_artifact(
            [new_text_part("final: task completed")],
            name="result",
        )
        await updater.complete()

    async def cancel(self, context: RequestContext, event_queue) -> None:
        self.cancel_called = True
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.cancel()


def build_a2a_app(executor: AgentExecutor) -> FastAPI:
    card = AgentCard(
        name="streaming-cancel-agent",
        version="0.1.0",
        description="A streaming A2A teaching agent.",
        supported_interfaces=[
            AgentInterface(
                protocol_binding=TransportProtocol.JSONRPC,
                url=f"{AGENT_URL}/",
            )
        ],
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
    )
    handler = DefaultRequestHandler(executor, InMemoryTaskStore(), card)
    app = FastAPI()
    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(card),
        jsonrpc_routes=create_jsonrpc_routes(handler, rpc_url="/"),
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
    executor = SlowExecutor()
    server = uvicorn.Server(
        uvicorn.Config(
            build_a2a_app(executor),
            host="127.0.0.1",
            port=8765,
            log_level="error",
            access_log=False,
        )
    )
    server_task = asyncio.create_task(server.serve())

    try:
        await wait_for_server()
        client = await create_client(AGENT_URL, ClientConfig(streaming=True))
        task_id = None
        event_kinds: list[str] = []
        saw_progress = False

        try:
            async with asyncio.timeout(0.25):
                request = SendMessageRequest(
                    message=new_text_message(
                        "请执行一个需要较长时间的远端任务。",
                        role=Role.ROLE_USER,
                    ),
                    configuration=SendMessageConfiguration(),
                )
                async for event in client.send_message(request):
                    kind = event.WhichOneof("payload")
                    event_kinds.append(kind)
                    print("stream_event:", kind)
                    if kind == "task":
                        task_id = event.task.id
                    elif kind == "status_update":
                        task_id = event.status_update.task_id
                        print(
                            "status:",
                            TaskState.Name(event.status_update.status.state),
                        )
                    elif kind == "artifact_update":
                        saw_progress = True
        except TimeoutError:
            print("client_wait: timed out after 250ms")
        else:
            raise AssertionError("slow task unexpectedly completed before timeout")

        assert task_id, "stream did not return a task ID"
        canceled_task = await client.cancel_task(CancelTaskRequest(id=task_id))
        print("cancel_state:", TaskState.Name(canceled_task.status.state))

        assert "status_update" in event_kinds, event_kinds
        assert saw_progress, event_kinds
        assert executor.cancel_called
        assert canceled_task.status.state == TaskState.TASK_STATE_CANCELED
        assert [artifact.name for artifact in canceled_task.artifacts] == ["progress"]
        print("a2a streaming, timeout, and cancel ok")
        await client.close()
    finally:
        server.should_exit = True
        await server_task


if __name__ == "__main__":
    asyncio.run(main())
