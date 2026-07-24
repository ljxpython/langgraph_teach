from __future__ import annotations

from pathlib import Path

from deepagents.backends import FilesystemBackend
from deepagents.middleware.skills import _list_skills_with_errors


ROOT_DIR = Path(__file__).resolve().parent / "workspace"
SKILL_SOURCE = "/skills/"


def main() -> None:
    backend = FilesystemBackend(root_dir=ROOT_DIR, virtual_mode=True)
    skills, error = _list_skills_with_errors(backend, SKILL_SOURCE)

    assert error is None
    assert skills[0]["name"] == "langgraph-docs"
    assert skills[0]["path"] == "/skills/langgraph-docs/SKILL.md"
    print("skills discovery ok:", skills[0]["name"], skills[0]["path"])


if __name__ == "__main__":
    main()
