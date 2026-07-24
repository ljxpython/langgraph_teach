from __future__ import annotations

from pathlib import Path

from deepagents import FilesystemPermission
from deepagents.backends import FilesystemBackend
from deepagents.middleware.filesystem import _check_fs_permission
from deepagents.middleware.skills import _list_skills_with_errors


ROOT_DIR = Path(__file__).resolve().parent / "workspace"
SKILL_SOURCE = "/skills/"
SKILL_PATH = "/skills/langgraph-docs/SKILL.md"


READ_ONLY_SHARED_SKILLS = [
    FilesystemPermission(
        operations=["write"],
        paths=["/skills/**"],
        mode="deny",
    )
]

APPROVE_PERSONAL_SKILL_WRITES = [
    FilesystemPermission(
        operations=["write"],
        paths=["/skills/personal/**"],
        mode="interrupt",
    )
]

RESEARCH_SUBAGENT = {
    "name": "researcher",
    "description": "Research with the shared LangGraph docs skill.",
    "system_prompt": "Use the configured skills when the task matches.",
    "skills": [SKILL_SOURCE],
    "permissions": READ_ONLY_SHARED_SKILLS,
}


def main() -> None:
    backend = FilesystemBackend(root_dir=ROOT_DIR, virtual_mode=True)
    skills, error = _list_skills_with_errors(backend, SKILL_SOURCE)
    missing_skills, missing_error = _list_skills_with_errors(backend, "/missing-skills/")

    assert error is None
    assert skills[0]["path"] == SKILL_PATH
    assert missing_skills == []
    assert missing_error is not None

    assert _check_fs_permission(READ_ONLY_SHARED_SKILLS, "write", SKILL_PATH) == "deny"
    assert _check_fs_permission(READ_ONLY_SHARED_SKILLS, "read", SKILL_PATH) == "allow"
    assert _check_fs_permission(
        APPROVE_PERSONAL_SKILL_WRITES,
        "write",
        "/skills/personal/langgraph-docs/SKILL.md",
    ) == "interrupt"

    assert RESEARCH_SUBAGENT["skills"] == [SKILL_SOURCE]
    assert RESEARCH_SUBAGENT["permissions"] == READ_ONLY_SHARED_SKILLS
    print("permissions and subagent config ok")


if __name__ == "__main__":
    main()
