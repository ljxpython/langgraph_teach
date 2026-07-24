from __future__ import annotations

from pathlib import Path

from deepagents.backends import FilesystemBackend
from deepagents.middleware.skills import SkillsMiddleware, _list_skills_with_errors


ROOT_DIR = Path(__file__).resolve().parent / "workspace"
SKILL_SOURCE = "/skills/"
FULL_INSTRUCTION_MARKER = "FULL_INSTRUCTIONS_ONLY_AFTER_READ"


def main() -> None:
    backend = FilesystemBackend(root_dir=ROOT_DIR, virtual_mode=True)
    skills, error = _list_skills_with_errors(backend, SKILL_SOURCE)
    middleware = SkillsMiddleware(backend=backend, sources=[SKILL_SOURCE])
    discovery_text = middleware._format_skills_list(skills)

    assert error is None
    assert "langgraph-docs" in discovery_text
    assert "Read `/skills/langgraph-docs/SKILL.md` for full instructions" in discovery_text
    assert FULL_INSTRUCTION_MARKER not in discovery_text

    read_result = backend.read(skills[0]["path"], limit=1000)

    assert read_result.error is None
    assert read_result.file_data is not None
    assert FULL_INSTRUCTION_MARKER in read_result.file_data["content"]
    print("progressive disclosure ok")


if __name__ == "__main__":
    main()
