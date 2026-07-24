from __future__ import annotations

from pathlib import Path

from deepagents.backends import FilesystemBackend
from deepagents.middleware.skills import SkillsMiddleware, _list_skills_with_errors


ROOT_DIR = Path(__file__).resolve().parent / "workspace"
SKILL_SOURCE = "/skills/"
REFERENCE_PATH = "/skills/langgraph-docs/references/resource-map.md"
ASSET_PATH = "/skills/langgraph-docs/assets/report-template.md"


def read_text(backend: FilesystemBackend, path: str) -> str:
    result = backend.read(path, limit=1000)
    assert result.error is None
    assert result.file_data is not None
    return result.file_data["content"]


def main() -> None:
    backend = FilesystemBackend(root_dir=ROOT_DIR, virtual_mode=True)
    skills, error = _list_skills_with_errors(backend, SKILL_SOURCE)
    middleware = SkillsMiddleware(backend=backend, sources=[SKILL_SOURCE])
    discovery_text = middleware._format_skills_list(skills)

    assert error is None
    assert "RESOURCE_REFERENCE_MARKER" not in discovery_text
    assert "RESOURCE_ASSET_MARKER" not in discovery_text

    skill_body = read_text(backend, skills[0]["path"])
    reference_body = read_text(backend, REFERENCE_PATH)
    asset_body = read_text(backend, ASSET_PATH)

    assert "references/resource-map.md" in skill_body
    assert "scripts/show_resource_map.py" in skill_body
    assert "assets/report-template.md" in skill_body
    assert "RESOURCE_REFERENCE_MARKER" in reference_body
    assert "RESOURCE_ASSET_MARKER" in asset_body

    print("supporting resources ok")


if __name__ == "__main__":
    main()
