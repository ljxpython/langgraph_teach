import json
import os
from pathlib import Path
from typing import Any, Dict, List

from langchain_core.tools import tool


def _from_milvus() -> List[Dict[str, Any]]:
    """尝试从 Milvus 列出集合。"""
    milvus_uri = os.getenv("MILVUS_URI")
    if not milvus_uri:
        return []

    try:
        from pymilvus import connections, utility  # type: ignore
    except Exception:
        return []

    try:
        connections.connect("default", uri=milvus_uri)
        collections = utility.list_collections()
        return [{"name": name, "description": "Milvus collection", "source": "milvus"} for name in collections]
    except Exception:
        return []


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
    candidates.extend(_from_milvus())
    candidates.extend(_from_local_file())

    default_name = os.getenv("MILVUS_COLLECTION_NAME", "knowledge_base")
    if not any(c.get("name") == default_name for c in candidates):
        candidates.append(
            {
                "name": default_name,
                "description": "Default collection (from env MILVUS_COLLECTION_NAME or fallback).",
                "source": "default",
            }
        )

    return json.dumps(candidates, ensure_ascii=False, indent=2)


@tool
def get_available_collections() -> str:
    """
    获取可用的集合信息，优先尝试 Milvus，其次读取本地 collections.json。
    返回 JSON 字符串，元素包含 name 和 description。
    """
    return _build_collections_json()


# 便于脚本/调试直接调用
def get_available_collections_raw() -> str:
    return _build_collections_json()


if __name__ == '__main__':
    print(get_available_collections_raw())
    print(get_available_collections.invoke({}))
