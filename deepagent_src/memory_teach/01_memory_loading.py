from __future__ import annotations

from pathlib import Path

from deepagents import MemoryMiddleware
from deepagents.backends import FilesystemBackend


ROOT_DIR = Path(__file__).resolve().parent / "workspace"
MEMORY_PATH = "/memories/AGENTS.md"


def main() -> None:
    backend = FilesystemBackend(root_dir=ROOT_DIR, virtual_mode=True)
    middleware = MemoryMiddleware(backend=backend, sources=[MEMORY_PATH])
    response = backend.download_files([MEMORY_PATH])[0]

    assert response.error is None
    assert response.content is not None

    memory_prompt = middleware._format_agent_memory(
        {MEMORY_PATH: response.content.decode("utf-8")}
    )

    assert "<agent_memory>" in memory_prompt
    assert "Prefer concise Chinese explanations" in memory_prompt
    assert "INTERNAL_AUTHOR_NOTE" not in memory_prompt
    print("memory loading ok")


if __name__ == "__main__":
    main()
