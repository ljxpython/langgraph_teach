from __future__ import annotations

from pathlib import Path
from uuid import UUID

from deepagents.backends import FilesystemBackend
from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from copilotkit import LangGraphAGUIAgent
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_config

from deepagent_src.frontend_teach.langgraph_graphs import tool_calling_builder


WORKSPACES_ROOT = Path(__file__).resolve().parent / "sandbox_workspaces"


def workspace_path_for_thread(thread_id: str) -> Path:
    try:
        safe_id = str(UUID(thread_id))
    except (ValueError, AttributeError) as exc:
        raise ValueError("thread_id must be a UUID") from exc

    workspace = (WORKSPACES_ROOT / safe_id).resolve()
    workspace.relative_to(WORKSPACES_ROOT.resolve())
    return workspace


def workspace_for_thread(thread_id: str) -> Path:
    workspace = workspace_path_for_thread(thread_id)
    (workspace / "src").mkdir(parents=True, exist_ok=True)

    readme = workspace / "README.md"
    app_file = workspace / "src" / "app.py"
    if not readme.exists():
        readme.write_text("# Sandbox Demo\n\nA thread-scoped learning workspace.\n", encoding="utf-8")
    if not app_file.exists():
        app_file.write_text(
            'def greeting(name: str) -> str:\n    return f"Hello, {name}!"\n',
            encoding="utf-8",
        )
    return workspace


def sandbox_backend(_runtime: object) -> FilesystemBackend:
    thread_id = get_config().get("configurable", {}).get("thread_id")
    if not thread_id:
        raise ValueError("sandbox_agent requires a thread_id")
    return FilesystemBackend(
        root_dir=workspace_path_for_thread(thread_id),
        virtual_mode=True,
    )


def resolve_file(thread_id: str, file_path: str) -> Path:
    workspace = workspace_for_thread(thread_id)
    relative = file_path.lstrip("/")
    if not relative or ".." in Path(relative).parts:
        raise ValueError("invalid file path")
    resolved = (workspace / relative).resolve()
    resolved.relative_to(workspace)
    return resolved


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
add_langgraph_fastapi_endpoint(
    app,
    LangGraphAGUIAgent(
        name="copilotkit_integration",
        graph=tool_calling_builder.compile(
            name="copilotkit_integration",
            checkpointer=InMemorySaver(),
        ),
    ),
    path="/api/copilotkit",
)


@app.get("/sandbox/{thread_id}/tree")
def list_tree(thread_id: str) -> dict[str, object]:
    try:
        workspace = workspace_for_thread(thread_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    entries = []
    for path in sorted(workspace.rglob("*"), key=lambda item: (item.is_file(), str(item))):
        entries.append(
            {
                "name": path.name,
                "path": "/" + path.relative_to(workspace).as_posix(),
                "type": "directory" if path.is_dir() else "file",
                "size": path.stat().st_size if path.is_file() else 0,
            }
        )
    return {"entries": entries}


@app.get("/sandbox/{thread_id}/file")
def read_file(thread_id: str, file_path: str = Query(alias="filePath")) -> dict[str, str]:
    try:
        path = resolve_file(thread_id, file_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    if path.stat().st_size > 1_000_000:
        raise HTTPException(status_code=413, detail="file is too large for the teaching UI")
    return {"path": file_path, "content": path.read_text(encoding="utf-8", errors="replace")}
