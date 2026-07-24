import os
from pathlib import Path
from uuid import uuid4

os.environ["LANGSMITH_TRACING"] = "false"

from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend

from deepagent_src.llms import gpt_model


def main():
    workspace = Path(__file__).with_name("permissions_workspace").resolve()
    workspace.mkdir(exist_ok=True)
    file_id = uuid4().hex[:8]
    public_path = f"/workspace/public/ok-{file_id}.txt"
    protected_path = f"/workspace/protected/no-{file_id}.txt"

    permissions = [
        FilesystemPermission(["write"], ["/workspace/protected/**"], "deny"),
        FilesystemPermission(["write"], ["/workspace/**"], "allow"),
        FilesystemPermission(["write"], ["/**"], "deny"),
    ]
    agent = create_deep_agent(
        model=gpt_model,
        backend=CompositeBackend(
            default=StateBackend(),
            routes={
                "/workspace/": FilesystemBackend(root_dir=workspace, virtual_mode=True),
            },
        ),
        permissions=permissions,
    )
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"写入‘允许写入’到 {public_path}；"
                        f"再写入‘禁止写入’到 {protected_path}；"
                        "说明两个操作的结果"
                    ),
                }
            ]
        }
    )

    print(result["messages"][-1].content)
    print("允许文件：", (workspace / "public" / f"ok-{file_id}.txt").read_text())
    print("受保护文件存在：", (workspace / "protected" / f"no-{file_id}.txt").exists())


if __name__ == "__main__":
    main()
