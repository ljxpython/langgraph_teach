from __future__ import annotations

from pydantic import BaseModel
from typing import Any, Optional


class GPTKeywordExtractionFormat(BaseModel):
    high_level_keywords: list[str]
    low_level_keywords: list[str]
# pylint: disable  MC8yOmFIVnBZMlhtblk3a3ZiUG1yS002VGxkbFVRPT06YzY1NDdhNTQ=


class KnowledgeGraphNode(BaseModel):
    id: str
    labels: list[str]
    properties: dict[str, Any]  # anything else goes here
# noqa  MS8yOmFIVnBZMlhtblk3a3ZiUG1yS002VGxkbFVRPT06YzY1NDdhNTQ=


class KnowledgeGraphEdge(BaseModel):
    id: str
    type: Optional[str]
    source: str  # id of source node
    target: str  # id of target node
    properties: dict[str, Any]  # anything else goes here


class KnowledgeGraph(BaseModel):
    nodes: list[KnowledgeGraphNode] = []
    edges: list[KnowledgeGraphEdge] = []
    is_truncated: bool = False
