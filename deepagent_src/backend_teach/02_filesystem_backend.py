import os
from pathlib import Path
from uuid import uuid4

os.environ["LANGSMITH_TRACING"] = "false"

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

from deepagent_src.llms import gpt_model


def main():
    workspace = Path(__file__).with_name("workspace").resolve()
    workspace.mkdir(exist_ok=True)
    file_path = f"/note-{uuid4().hex[:8]}.txt"

    agent = create_deep_agent(
        model=gpt_model,
        backend=FilesystemBackend(root_dir=workspace, virtual_mode=True),
    )
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"使用 write_file 把‘我正在学习 FilesystemBackend’写入 {file_path}，再读取确认",
                }
            ]
        }
    )

    print(result["messages"][-1].content)
    print("磁盘内容：", (workspace / file_path.removeprefix("/")).read_text())


if __name__ == "__main__":
    main()
