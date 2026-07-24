import os
from pathlib import Path

os.environ["LANGSMITH_TRACING"] = "false"

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend

from deepagent_src.llms import gpt_model


def main():
    workspace = Path(__file__).with_name("shell_workspace").resolve()
    workspace.mkdir(exist_ok=True)

    agent = create_deep_agent(
        model=gpt_model,
        backend=LocalShellBackend(
            root_dir=workspace,
            virtual_mode=True,
            env={"PATH": "/usr/bin:/bin"},
            timeout=10,
        ),
    )
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "只使用 execute 执行 pwd，不要执行其他命令。告诉我输出。",
                }
            ]
        }
    )
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
