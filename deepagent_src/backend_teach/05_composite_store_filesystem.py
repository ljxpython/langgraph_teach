import os
from pathlib import Path
from uuid import uuid4

os.environ["LANGSMITH_TRACING"] = "false"

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend, StoreBackend
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.sqlite import SqliteStore

from deepagent_src.llms import gpt_model


def main():
    root = Path(__file__).parent
    workspace = root / "workspace"
    workspace.mkdir(exist_ok=True)
    file_id = uuid4().hex[:8]
    draft_path = f"/draft-{file_id}.txt"
    memory_path = f"/memories/preference-{file_id}.txt"
    project_path = f"/workspace/report-{file_id}.txt"

    with SqliteStore.from_conn_string(str(root / "backend_store.sqlite")) as store:
        store.setup()
        backend = CompositeBackend(
            default=StateBackend(),
            routes={
                "/memories/": StoreBackend(namespace=lambda _rt: ("demo-user",)),
                "/workspace/": FilesystemBackend(root_dir=workspace, virtual_mode=True),
            },
        )
        agent = create_deep_agent(
            model=gpt_model,
            backend=backend,
            store=store,
            checkpointer=InMemorySaver(),
        )

        agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"把‘仅 thread-a 可见’写入 {draft_path}；"
                            f"把‘跨 thread 共享’写入 {memory_path}；"
                            f"把‘本地磁盘文件’写入 {project_path}"
                        ),
                    }
                ]
            },
            {"configurable": {"thread_id": "thread-a"}},
        )
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"读取 {memory_path} 和 {project_path}；"
                            f"再尝试读取 {draft_path}，说明哪些文件能读到"
                        ),
                    }
                ]
            },
            {"configurable": {"thread_id": "thread-b"}},
        )

    print(result["messages"][-1].content)
    print("SQLite Store：", root / "backend_store.sqlite")
    print("磁盘文件：", workspace / f"report-{file_id}.txt")


if __name__ == "__main__":
    main()
