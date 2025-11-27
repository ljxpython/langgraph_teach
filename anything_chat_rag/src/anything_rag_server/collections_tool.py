import json
import os
from pathlib import Path
from typing import Any, Dict, List

from langchain_core.tools import tool


def _get_working_dir() -> Path:
    """获取本地 LightRAG 工作目录。"""
    return Path(
        os.getenv("RAG_WORKDIR")
        or os.getenv("WORKING_DIR")
        or Path("rag_storage").resolve()
    )


def _from_local_workdir() -> List[Dict[str, Any]]:
    """扫描本地 LightRAG 工作目录，推断可用 workspace。"""
    working_dir = _get_working_dir()
    workspaces = []

    # 显式配置优先
    configured = os.getenv("ANYTHING_RAG_WORKSPACE") or os.getenv("WORKSPACE")
    if configured is not None:
        workspaces.append(configured)

    if working_dir.exists():
        # 子目录视为独立 workspace
        for item in working_dir.iterdir():
            if item.is_dir():
                workspaces.append(item.name)
        # 根目录存在向量/图文件时表示默认 workspace
        vector_hints = [
            "vdb_chunks.json",
            "vdb_entities.json",
            "vdb_relationships.json",
            "graph_chunk_entity_relation.graphml",
        ]
        if any((working_dir / name).exists() for name in vector_hints):
            workspaces.append(configured or "")

    results: List[Dict[str, Any]] = []
    for ws in sorted(set(workspaces)):
        results.append(
            {
                "name": ws,
                "description": f"Local workspace {'(default)' if ws == '' else ws}",
                "source": "local",
            }
        )
    return results


def _from_local_file() -> List[Dict[str, Any]]:
    """读取本地 collections.json 作为兜底."""
    collections_file = Path(__file__).with_name("collections.json")
    if not collections_file.exists():
        return []
    try:
        data = json.loads(collections_file.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except Exception:
        return []
    return []


def _build_collections_json() -> str:
    """内部方法：返回集合信息 JSON 字符串（便于本地调试和工具复用）"""
    candidates: List[Dict[str, Any]] = []
    candidates.extend(_from_local_workdir())
    candidates.extend(_from_local_file())

    default_name = (
        os.getenv("ANYTHING_RAG_WORKSPACE")
        or os.getenv("WORKSPACE")
        or os.getenv("MILVUS_COLLECTION_NAME")
        or "knowledge_base"
    )
    if not any(c.get("name") == default_name for c in candidates):
        candidates.append(
            {
                "name": default_name,
                "description": "Default workspace/collection (env WORKSPACE or fallback).",
                "source": "default",
            }
        )

    return json.dumps(candidates, ensure_ascii=False, indent=2)


@tool
def get_available_collections() -> str:
    """
    获取可用的集合/工作空间信息，优先扫描本地 LightRAG 工作目录，
    再读取本地 collections.json。
    返回 JSON 字符串，元素包含 name 和 description。
    """
    return _build_collections_json()


# 便于脚本/调试直接调用
def get_available_collections_raw() -> str:
    return _build_collections_json()


if __name__ == '__main__':
    print(get_available_collections_raw())
    print(get_available_collections.invoke({}))
