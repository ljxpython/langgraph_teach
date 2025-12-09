"""RAG Knowledge Base API Client.

This module provides a client for interacting with the external RAG knowledge base
API for retrieving performance testing reference materials.

The client supports multiple query modes:
- local: Returns entities and their direct relationships + related chunks
- global: Returns relationship patterns across the knowledge graph
- hybrid: Combines local and global retrieval strategies
- naive: Returns only vector-retrieved text chunks (no knowledge graph)
- mix: Integrates knowledge graph data with vector-retrieved chunks
"""
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
import httpx
import logging
# pragma: no cover  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002VG1WSWF3PT06Y2IwMWU1OWQ=

logger = logging.getLogger(__name__)


class QueryMode(str, Enum):
    """Query modes for RAG retrieval."""
    LOCAL = "local"      # Entity-focused retrieval
    GLOBAL = "global"    # Relationship pattern retrieval
    HYBRID = "hybrid"    # Combined local + global
    NAIVE = "naive"      # Vector similarity only
    MIX = "mix"          # Knowledge graph + vector
    BYPASS = "bypass"    # Skip retrieval


@dataclass
class QueryRequest:
    """Request model for knowledge retrieval."""
    query: str
    mode: QueryMode = QueryMode.MIX
    only_need_context: bool = True
    only_need_prompt: bool = False
    top_k: int = 10
    chunk_top_k: int = 5
    max_entity_tokens: int = 2000
    max_relation_tokens: int = 2000
    max_total_tokens: int = 8000
    hl_keywords: Optional[List[str]] = None
    ll_keywords: Optional[List[str]] = None
    enable_rerank: bool = True
    include_references: bool = True
    include_chunk_content: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API request dictionary."""
        return {
            "query": self.query,
            "mode": self.mode.value,
            "only_need_context": self.only_need_context,
            "only_need_prompt": self.only_need_prompt,
            "top_k": self.top_k,
            "chunk_top_k": self.chunk_top_k,
            "max_entity_tokens": self.max_entity_tokens,
            "max_relation_tokens": self.max_relation_tokens,
            "max_total_tokens": self.max_total_tokens,
            "hl_keywords": self.hl_keywords or [],
            "ll_keywords": self.ll_keywords or [],
            "enable_rerank": self.enable_rerank,
            "include_references": self.include_references,
            "include_chunk_content": self.include_chunk_content,
        }


@dataclass
class Entity:
    """Knowledge graph entity."""
    entity_name: str
    entity_type: str
    description: str
    source_id: str
    file_path: str
    reference_id: str

# fmt: off  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002VG1WSWF3PT06Y2IwMWU1OWQ=

@dataclass
class Relationship:
    """Knowledge graph relationship."""
    src_id: str
    tgt_id: str
    description: str
    keywords: str
    weight: float
    source_id: str
    file_path: str
    reference_id: str


@dataclass
class Chunk:
    """Text chunk from documents."""
    content: str
    file_path: str
    chunk_id: str
    reference_id: str


@dataclass
class Reference:
    """Document reference."""
    reference_id: str
    file_path: str


@dataclass
class QueryData:
    """Structured query data from RAG."""
    entities: List[Entity] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    chunks: List[Chunk] = field(default_factory=list)
    references: List[Reference] = field(default_factory=list)


@dataclass
class QueryMetadata:
    """Query processing metadata."""
    query_mode: str
    keywords: Dict[str, List[str]]
    processing_info: Dict[str, Any]


@dataclass
class QueryResponse:
    """Response from knowledge retrieval."""
    status: str
    message: str
    data: QueryData
    metadata: Optional[QueryMetadata] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueryResponse":
        """Parse response from API."""
        query_data = QueryData(
            entities=[Entity(**e) for e in data.get("data", {}).get("entities", [])],
            relationships=[Relationship(**r) for r in data.get("data", {}).get("relationships", [])],
            chunks=[Chunk(**c) for c in data.get("data", {}).get("chunks", [])],
            references=[Reference(**r) for r in data.get("data", {}).get("references", [])],
        )
        metadata = None
        if "metadata" in data:
            metadata = QueryMetadata(
                query_mode=data["metadata"].get("query_mode", ""),
                keywords=data["metadata"].get("keywords", {}),
                processing_info=data["metadata"].get("processing_info", {}),
            )
        return cls(
            status=data.get("status", "unknown"),
            message=data.get("message", ""),
            data=query_data,
            metadata=metadata,
        )
# pragma: no cover  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002VG1WSWF3PT06Y2IwMWU1OWQ=


class KnowledgeClient:
    """Client for RAG Knowledge Base API.

    This client provides access to the external knowledge base for retrieving
    performance testing reference materials, best practices, and expert knowledge.

    Example:
        >>> client = KnowledgeClient(api_url="http://localhost:8000")
        >>> response = await client.query(
        ...     query="K6 load testing best practices",
        ...     mode=QueryMode.MIX,
        ...     hl_keywords=["performance", "testing"],
        ... )
        >>> for chunk in response.data.chunks:
        ...     print(chunk.content)
    """

    def __init__(
        self,
        api_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize the knowledge client.

        Args:
            api_url: Base URL of the RAG API.
            api_key: Optional API key for authentication.
            timeout: Request timeout in seconds.
        """
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            self._client = httpx.AsyncClient(
                base_url=self.api_url,
                headers=headers,
                timeout=self.timeout,
            )
        return self._client

    async def query(
        self,
        query: str,
        mode: QueryMode = QueryMode.MIX,
        top_k: int = 10,
        chunk_top_k: int = 5,
        hl_keywords: Optional[List[str]] = None,
        ll_keywords: Optional[List[str]] = None,
        **kwargs,
    ) -> QueryResponse:
        """Query the knowledge base.

        Args:
            query: The search query (min 3 characters).
            mode: Retrieval strategy affecting data types returned.
            top_k: Number of top entities/relationships to retrieve.
            chunk_top_k: Number of text chunks to retrieve.
            hl_keywords: High-level keywords for query.
            ll_keywords: Low-level keywords for query.
            **kwargs: Additional query parameters.

        Returns:
            QueryResponse with entities, relationships, chunks, and references.

        Raises:
            httpx.HTTPError: On API request failure.
        """
        request = QueryRequest(
            query=query,
            mode=mode,
            top_k=top_k,
            chunk_top_k=chunk_top_k,
            hl_keywords=hl_keywords,
            ll_keywords=ll_keywords,
            **kwargs,
        )

        client = await self._get_client()

        try:
            response = await client.post(
                "/query/data",
                json=request.to_dict(),
            )
            response.raise_for_status()
            return QueryResponse.from_dict(response.json())
        except httpx.HTTPError as e:
            logger.error(f"Knowledge API request failed: {e}")
            raise

    async def query_for_context(
        self,
        query: str,
        domain: str = "performance_testing",
        **kwargs,
    ) -> str:
        """Query and format results as context string.

        This is a convenience method that formats the query results
        as a context string suitable for LLM prompts.

        Args:
            query: The search query.
            domain: Domain hint for better retrieval.
            **kwargs: Additional query parameters.

        Returns:
            Formatted context string with relevant knowledge.
        """
        response = await self.query(query, **kwargs)

        if response.status != "success":
            return f"Knowledge retrieval failed: {response.message}"

        context_parts = []

        # Add entity information
        if response.data.entities:
            context_parts.append("## Relevant Concepts\n")
            for entity in response.data.entities[:5]:
                context_parts.append(f"- **{entity.entity_name}** ({entity.entity_type}): {entity.description}")

        # Add relationship information
        if response.data.relationships:
            context_parts.append("\n## Key Relationships\n")
            for rel in response.data.relationships[:5]:
                context_parts.append(f"- {rel.src_id} → {rel.tgt_id}: {rel.description}")

        # Add chunk content
        if response.data.chunks:
            context_parts.append("\n## Reference Materials\n")
            for chunk in response.data.chunks[:3]:
                context_parts.append(f"```\n{chunk.content}\n```\n")
                context_parts.append(f"_Source: {chunk.file_path}_\n")

        return "\n".join(context_parts)

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self
# pragma: no cover  My80OmFIVnBZMlhtblk3a3ZiUG1yS002VG1WSWF3PT06Y2IwMWU1OWQ=

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

