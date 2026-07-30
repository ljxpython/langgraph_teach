from __future__ import annotations

import os
from pathlib import Path

from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from deepagents.middleware.skills import _list_skills_with_errors
from langchain.messages import HumanMessage

from deepagent_src.agent_output import stream_values_and_pretty_print
from deepagent_src.llms import get_gpt_model


ROOT = Path(__file__).resolve().parent
DOCUMENTATION_DIR = ROOT / "skill_sources" / "documentation"
RELEASE_DIR = ROOT / "skill_sources" / "release"
DOCUMENTATION_SOURCE = "/documentation-skills/"
RELEASE_SOURCE = "/release-skills/"
SKILL_PATHS = {
    "/documentation-skills/langgraph-answer/SKILL.md",
    "/release-skills/release-check/SKILL.md",
}


def build_backend() -> CompositeBackend:
    return CompositeBackend(
        default=StateBackend(),
        routes={
            DOCUMENTATION_SOURCE: FilesystemBackend(
                root_dir=DOCUMENTATION_DIR, virtual_mode=True
            ),
            RELEASE_SOURCE: FilesystemBackend(
                root_dir=RELEASE_DIR, virtual_mode=True
            ),
        },
    )


def assert_both_sources_discovered(backend: CompositeBackend) -> None:
    discovered_paths = set()
    for source in (DOCUMENTATION_SOURCE, RELEASE_SOURCE):
        skills, error = _list_skills_with_errors(backend, source)
        assert error is None
        discovered_paths.update(skill["path"] for skill in skills)
    assert discovered_paths == SKILL_PATHS


def read_skill_paths(messages: list) -> set[str]:
    paths = set()
    for message in messages:
        for call in getattr(message, "tool_calls", None) or []:
            if call.get("name") == "read_file":
                path = call.get("args", {}).get("file_path")
                if path in SKILL_PATHS:
                    paths.add(path)
    return paths


def main() -> None:
    os.environ["LANGSMITH_TRACING"] = "false"
    backend = build_backend()
    assert_both_sources_discovered(backend)

    graph = create_deep_agent(
        model=get_gpt_model(disable_tool_streaming=True),
        backend=backend,
        skills=[DOCUMENTATION_SOURCE, RELEASE_SOURCE],
        permissions=[
            FilesystemPermission(
                operations=["write"],
                paths=["/documentation-skills/**", "/release-skills/**"],
                mode="deny",
            )
        ],
        subagents=[],
        system_prompt=(
            "你是多来源 Skills 教学助手。用户要求组合能力时，必须先分别调用 read_file "
            "读取匹配的每一份 SKILL.md，再同时遵循两份完整指令；禁止仅凭摘要回答。"
        ),
    )

    state = stream_values_and_pretty_print(
        graph,
        {
            "messages": [
                HumanMessage(
                    content=(
                        "请同时使用 langgraph-answer 和 release-check 两个 skill："
                        "解释静态 LangGraph Agent、thread 与 run 的关系，并给出发布检查结论。"
                        "不要联网，不要写文件。"
                    )
                )
            ]
        },
    )

    assert read_skill_paths(state["messages"]) == SKILL_PATHS
    final_text = state["messages"][-1].text
    assert "架构结论：" in final_text
    assert "发布检查：" in final_text
    assert "通过" in final_text
    print("multi-source skills real call ok")


if __name__ == "__main__":
    main()
