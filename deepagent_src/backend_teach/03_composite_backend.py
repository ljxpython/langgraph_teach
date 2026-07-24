import os
from pathlib import Path
from uuid import uuid4

os.environ["LANGSMITH_TRACING"] = "false"

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend

from deepagent_src.llms import gpt_model


def main():
    workspace = Path(__file__).with_name("workspace").resolve()
    workspace.mkdir(exist_ok=True)
    file_id = uuid4().hex[:8]
    draft_path = f"/draft-{file_id}.txt"
    project_path = f"/workspace/project-{file_id}.txt"

    backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/workspace/": FilesystemBackend(
                root_dir=workspace,
                virtual_mode=True,
            )
        },
    )
    agent = create_deep_agent(model=gpt_model, backend=backend)
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"把‘临时草稿’写入 {draft_path}，"
                        f"把‘项目文件’写入 {project_path}，然后读取两个文件确认"
                    ),
                }
            ]
        }
    )

    print(result["messages"][-1].content)
    print("磁盘文件：", (workspace / f"project-{file_id}.txt").read_text())
    print("草稿是否落盘：", (workspace / f"draft-{file_id}.txt").exists())


if __name__ == "__main__":
    main()
