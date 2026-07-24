from __future__ import annotations

import os
from pathlib import Path

from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend, StoreBackend
from deepagents.backends.utils import create_file_data
from deepagents.middleware.filesystem import _check_fs_permission
from deepagents.middleware.skills import SkillsMiddleware, _list_skills_with_errors
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from deepagent_src.agent_output import stream_values_and_pretty_print
from deepagent_src.llms import get_gpt_model


ROOT_DIR = Path(__file__).resolve().parent / "workspace"
SKILLS_DIR = ROOT_DIR / "skills"
WORKSPACE_DIR = ROOT_DIR / "workspace"
SKILL_SOURCE = "/skills/"
SKILL_PATH = "/skills/langgraph-docs/SKILL.md"
MEMORY_PATH = "/memories/team-note.txt"


def main() -> None:
    os.environ["LANGSMITH_TRACING"] = "false"
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    skills_backend = FilesystemBackend(root_dir=SKILLS_DIR, virtual_mode=True)
    reports_backend = FilesystemBackend(root_dir=WORKSPACE_DIR, virtual_mode=True)
    shared_store = InMemoryStore()
    shared_store.put(
        ("skills-teach",),
        MEMORY_PATH,
        create_file_data("team prefers one-page reports"),
    )

    backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/skills/": skills_backend,
            "/workspace/": reports_backend,
            "/memories/": StoreBackend(
                store=shared_store,
                namespace=lambda _rt: ("skills-teach",),
            ),
        },
    )

    permissions = [
        FilesystemPermission(
            operations=["write"],
            paths=["/skills/personal/**"],
            mode="interrupt",
        ),
        FilesystemPermission(
            operations=["write"],
            paths=["/skills/**"],
            mode="deny",
        ),
    ]

    research_subagent = {
        "name": "researcher",
        "description": "Research with the shared LangGraph docs skill.",
        "system_prompt": "Use the configured skills when the task matches.",
        "skills": [SKILL_SOURCE],
        "permissions": permissions,
    }

    graph = create_deep_agent(
        model=get_gpt_model(),
        backend=backend,
        skills=[SKILL_SOURCE],
        permissions=permissions,
        subagents=[research_subagent],
        store=shared_store,
        checkpointer=InMemorySaver(),
    )

    skills, error = _list_skills_with_errors(backend, SKILL_SOURCE)
    middleware = SkillsMiddleware(backend=backend, sources=[SKILL_SOURCE])
    discovery_text = middleware._format_skills_list(skills)
    skill_body = skills_backend.read("/langgraph-docs/SKILL.md", limit=1000)
    reference_body = skills_backend.read(
        "/langgraph-docs/references/resource-map.md",
        limit=1000,
    )
    asset_body = skills_backend.read(
        "/langgraph-docs/assets/report-template.md",
        limit=1000,
    )
    memory_read = StoreBackend(
        store=shared_store,
        namespace=lambda _rt: ("skills-teach",),
    ).read(MEMORY_PATH)
    report_template = asset_body.file_data["content"].format(
        question="How do DeepAgent skills fit together?",
        answer="Use skills for discovery, SKILL.md for instructions, resources for support files, backend for storage, permissions for guardrails, and subagents for scoped capability.",
        sources="- SKILL.md\n- references/resource-map.md\n- assets/report-template.md",
    )

    assert error is None
    assert "langgraph-docs" in discovery_text
    assert "Read `/skills/langgraph-docs/SKILL.md` for full instructions" in discovery_text
    assert skill_body.file_data is not None
    assert reference_body.file_data is not None
    assert asset_body.file_data is not None
    assert memory_read.error is None
    assert report_template.startswith("# Report Template")
    assert _check_fs_permission(permissions, "write", SKILL_PATH) == "deny"
    assert _check_fs_permission(permissions, "read", SKILL_PATH) == "allow"
    assert (
        _check_fs_permission(
            permissions,
            "write",
            "/skills/personal/langgraph-docs/SKILL.md",
        )
        == "interrupt"
    )
    assert research_subagent["skills"] == [SKILL_SOURCE]
    assert graph is not None

    messages = [
        HumanMessage(
            content=(
                "请使用 langgraph-docs skill，总结 DeepAgent skills 的使用链路。"
                "要求：先读取 skill 的完整说明，再按需查看 references/resource-map.md "
                "和 assets/report-template.md，最后用中文给出一段简短总结。"
                "不要联网，不要写文件。"
            )
        )
    ]
    messages = stream_values_and_pretty_print(
        graph,
        {"messages": messages},
        {"configurable": {"thread_id": "skills-comprehensive-case"}},
    )
    assert messages["messages"]

    print("comprehensive skills case ok")


if __name__ == "__main__":
    main()
