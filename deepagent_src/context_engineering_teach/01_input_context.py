from __future__ import annotations

from pathlib import Path

from deepagents import MemoryMiddleware, create_deep_agent
from deepagents.backends import FilesystemBackend
from deepagents.middleware.skills import SkillsMiddleware, _list_skills_with_errors

from _model import get_real_model
from deepagent_src.agent_output import invoke_and_pretty_print


ROOT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = ROOT_DIR / "workspace"
MEMORY_PATH = "/memories/AGENTS.md"
SKILL_SOURCE = "/skills/"


def main() -> None:
    backend = FilesystemBackend(root_dir=WORKSPACE_DIR, virtual_mode=True)

    agent = create_deep_agent(
        model=get_real_model(),
        backend=backend,
        system_prompt="You teach Deep Agents context engineering.",
        memory=[MEMORY_PATH],
        skills=[SKILL_SOURCE],
    )

    memory_file = backend.download_files([MEMORY_PATH])[0]
    assert memory_file.error is None
    assert memory_file.content is not None

    memory_prompt = MemoryMiddleware(
        backend=backend,
        sources=[MEMORY_PATH],
    )._format_agent_memory({MEMORY_PATH: memory_file.content.decode("utf-8")})

    skills, error = _list_skills_with_errors(backend, SKILL_SOURCE)
    skills_prompt = SkillsMiddleware(
        backend=backend,
        sources=[SKILL_SOURCE],
    )._format_skills_list(skills)

    assert agent is not None
    assert error is None
    assert "Prefer concise Chinese explanations" in memory_prompt
    assert "context-scout" in skills_prompt

    result = invoke_and_pretty_print(
        agent,
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "用一句中文说明你启动时能看到哪些 input context。"
                        "只回答一句话。"
                    ),
                }
            ]
        }
    )
    assert result["messages"][-1].content
    print("input context real agent ok")


if __name__ == "__main__":
    main()
