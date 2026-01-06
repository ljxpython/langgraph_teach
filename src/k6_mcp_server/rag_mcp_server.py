"""
RAG MCP 服务器 - 基于 LightRAG 的高级数据检索服务

本 MCP 服务器提供高级 RAG 功能，包括：
- 多模式查询（local, global, hybrid, naive, mix, bypass）
- 结构化数据检索（实体、关系、文本块）
- 知识图谱分析
- 源文档引用追踪

主要工具：
1. rag_query_data: 高级数据检索端点，返回结构化 RAG 分析数据
"""
import argparse
import os
import json
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional, List, Dict, Literal
from dotenv import load_dotenv

import httpx
from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field


# ============================================================================
# 数据模型
# ============================================================================

class EntityData(BaseModel):
    """知识图谱实体"""
    entity_name: str = Field(description="实体名称")
    entity_type: str = Field(default="UNKNOWN", description="实体类型")
    description: str = Field(default="", description="实体描述")
    source_id: str = Field(default="", description="来源文本块 ID")
    file_path: str = Field(default="", description="来源文件路径")
    reference_id: str = Field(default="", description="引用 ID")


class RelationshipData(BaseModel):
    """知识图谱关系"""
    src_id: str = Field(description="源实体 ID")
    tgt_id: str = Field(description="目标实体 ID")
    description: str = Field(default="", description="关系描述")
    keywords: str = Field(default="", description="关系关键词")
    weight: float = Field(default=0.0, description="关系权重")
    source_id: str = Field(default="", description="来源文本块 ID")
    file_path: str = Field(default="", description="来源文件路径")
    reference_id: str = Field(default="", description="引用 ID")


class ChunkData(BaseModel):
    """文本块数据"""
    content: str = Field(description="文本内容")
    file_path: str = Field(default="", description="来源文件路径")
    chunk_id: str = Field(default="", description="文本块 ID")
    reference_id: str = Field(default="", description="引用 ID")


class ReferenceData(BaseModel):
    """引用数据"""
    reference_id: str = Field(description="引用 ID")
    file_path: str = Field(description="文件路径")


class KeywordsInfo(BaseModel):
    """关键词信息"""
    high_level: List[str] = Field(default_factory=list, description="高级别关键词")
    low_level: List[str] = Field(default_factory=list, description="低级别关键词")


class ProcessingInfo(BaseModel):
    """处理信息"""
    total_entities_found: int = Field(default=0, description="找到的总实体数")
    total_relations_found: int = Field(default=0, description="找到的总关系数")
    entities_after_truncation: int = Field(default=0, description="截断后的实体数")
    relations_after_truncation: int = Field(default=0, description="截断后的关系数")
    final_chunks_count: int = Field(default=0, description="最终文本块数")


class QueryDataMetadata(BaseModel):
    """查询数据元数据"""
    query_mode: str = Field(default="", description="查询模式")
    keywords: Optional[KeywordsInfo] = Field(default=None, description="提取的关键词")
    processing_info: Optional[ProcessingInfo] = Field(default=None, description="处理信息")


class QueryData(BaseModel):
    """查询数据"""
    entities: List[EntityData] = Field(default_factory=list, description="实体列表")
    relationships: List[RelationshipData] = Field(default_factory=list, description="关系列表")
    chunks: List[ChunkData] = Field(default_factory=list, description="文本块列表")
    references: List[ReferenceData] = Field(default_factory=list, description="引用列表")


class QueryDataResponse(BaseModel):
    """查询数据响应"""
    status: str = Field(description="状态：success 或 failure")
    message: str = Field(description="状态描述消息")
    data: Optional[QueryData] = Field(default=None, description="查询数据")
    metadata: Optional[QueryDataMetadata] = Field(default=None, description="元数据")


# 查询模式类型
QueryMode = Literal["local", "global", "hybrid", "naive", "mix", "bypass"]


# ============================================================================
# RAG 客户端
# ============================================================================

class LightRAGClient:
    """LightRAG API 客户端"""

    def __init__(
        self,
        base_url: str = "http://localhost:9621",
        api_key: Optional[str] = None,
        timeout: float = 60.0
    ):
        """初始化 LightRAG 客户端

        参数：
            base_url: LightRAG 服务器基础 URL
            api_key: API 密钥（可选）
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout
            )
        return self._client

    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def query_data(
        self,
        query: str,
        mode: QueryMode = "mix",
        only_need_context: bool = False,
        only_need_prompt: bool = False,
        response_type: Optional[str] = None,
        top_k: int = 10,
        chunk_top_k: int = 5,
        max_entity_tokens: Optional[int] = None,
        max_relation_tokens: Optional[int] = None,
        max_total_tokens: Optional[int] = None,
        hl_keywords: Optional[List[str]] = None,
        ll_keywords: Optional[List[str]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        user_prompt: Optional[str] = None,
        enable_rerank: bool = True,
        include_references: bool = True,
        include_chunk_content: bool = False,
        stream: bool = False
    ) -> QueryDataResponse:
        """调用 /query/data 端点进行高级数据检索

        参数：
            query: 搜索查询（至少3个字符）
            mode: 检索策略 (local, global, hybrid, naive, mix, bypass)
            only_need_context: 是否只返回上下文
            only_need_prompt: 是否只返回提示词
            response_type: 响应类型
            top_k: 返回的顶部实体/关系数量
            chunk_top_k: 返回的文本块数量
            max_entity_tokens: 实体上下文的令牌限制
            max_relation_tokens: 关系上下文的令牌限制
            max_total_tokens: 总体令牌预算
            hl_keywords: 高级别关键词列表
            ll_keywords: 低级别关键词列表
            conversation_history: 对话历史
            user_prompt: 用户提示词
            enable_rerank: 是否启用重排序
            include_references: 是否包含引用
            include_chunk_content: 是否包含文本块内容
            stream: 是否流式返回

        返回：
            QueryDataResponse: 包含实体、关系、文本块和引用的结构化响应

        异常：
            httpx.HTTPError: HTTP 请求错误
            ValueError: 参数验证错误
        """
        # 验证查询长度
        if len(query.strip()) < 3:
            raise ValueError("查询必须至少包含3个字符")

        # 验证模式
        valid_modes = ["local", "global", "hybrid", "naive", "mix", "bypass"]
        if mode not in valid_modes:
            raise ValueError(f"无效的查询模式：{mode}。有效模式：{valid_modes}")

        # 构建请求体
        request_body: Dict[str, Any] = {
            "query": query,
            "mode": mode,
            "only_need_context": only_need_context,
            "only_need_prompt": only_need_prompt,
            "top_k": top_k,
            "chunk_top_k": chunk_top_k,
            "enable_rerank": enable_rerank,
            "include_references": include_references,
            "include_chunk_content": include_chunk_content,
            "stream": stream
        }

        # 添加可选参数
        if response_type is not None:
            request_body["response_type"] = response_type
        if max_entity_tokens is not None:
            request_body["max_entity_tokens"] = max_entity_tokens
        if max_relation_tokens is not None:
            request_body["max_relation_tokens"] = max_relation_tokens
        if max_total_tokens is not None:
            request_body["max_total_tokens"] = max_total_tokens
        if hl_keywords is not None:
            request_body["hl_keywords"] = hl_keywords
        if ll_keywords is not None:
            request_body["ll_keywords"] = ll_keywords
        if conversation_history is not None:
            request_body["conversation_history"] = conversation_history
        if user_prompt is not None:
            request_body["user_prompt"] = user_prompt

        client = await self._get_client()

        try:
            response = await client.post("/query/data", json=request_body)
            response.raise_for_status()

            result = response.json()

            # 解析响应数据
            data = None
            if "data" in result and result["data"]:
                raw_data = result["data"]
                data = QueryData(
                    entities=[EntityData(**e) for e in raw_data.get("entities", [])],
                    relationships=[RelationshipData(**r) for r in raw_data.get("relationships", [])],
                    chunks=[ChunkData(**c) for c in raw_data.get("chunks", [])],
                    references=[ReferenceData(**ref) for ref in raw_data.get("references", [])]
                )

            # 解析元数据
            metadata = None
            if "metadata" in result and result["metadata"]:
                raw_metadata = result["metadata"]
                keywords_info = None
                if "keywords" in raw_metadata and raw_metadata["keywords"]:
                    keywords_info = KeywordsInfo(**raw_metadata["keywords"])
                processing_info = None
                if "processing_info" in raw_metadata and raw_metadata["processing_info"]:
                    processing_info = ProcessingInfo(**raw_metadata["processing_info"])
                metadata = QueryDataMetadata(
                    query_mode=raw_metadata.get("query_mode", ""),
                    keywords=keywords_info,
                    processing_info=processing_info
                )

            return QueryDataResponse(
                status=result.get("status", "success"),
                message=result.get("message", "查询执行成功"),
                data=data,
                metadata=metadata
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                error_detail = e.response.json().get("detail", "无效的输入参数")
                raise ValueError(f"请求参数错误：{error_detail}")
            elif e.response.status_code == 500:
                raise RuntimeError(f"服务器内部错误：{e.response.text}")
            else:
                raise
        except httpx.RequestError as e:
            raise RuntimeError(f"请求失败：{str(e)}")


# ============================================================================
# MCP 服务器设置
# ============================================================================

class RAGContext:
    """RAG 操作的上下文"""
    def __init__(self, client: LightRAGClient):
        self.client = client


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[RAGContext]:
    """管理 LightRAG 客户端的应用程序生命周期"""
    config = server.config

    client = LightRAGClient(
        base_url=config.get("lightrag_base_url", "http://localhost:9621"),
        api_key=config.get("lightrag_api_key"),
        timeout=config.get("timeout", 60.0)
    )

    try:
        yield RAGContext(client)
    finally:
        await client.close()


mcp = FastMCP(name="LightRAG", lifespan=server_lifespan)


# ============================================================================
# MCP 工具
# ============================================================================

@mcp.tool()
async def rag_query_data(
    query: str,
    mode: str = "mix",
    top_k: int = 10,
    chunk_top_k: int = 5,
    max_entity_tokens: Optional[int] = None,
    max_relation_tokens: Optional[int] = None,
    max_total_tokens: Optional[int] = None,
    hl_keywords: Optional[List[str]] = None,
    ll_keywords: Optional[List[str]] = None,
    enable_rerank: bool = True,
    ctx: Context = None
) -> str:
    """
    高级数据检索端点，用于结构化 RAG 分析。

    此端点提供纯数据检索结果（无 LLM 生成），适用于：
    - 数据分析：检查用于 RAG 的信息
    - 系统集成：获取结构化数据用于自定义处理
    - 调试：了解检索行为和质量
    - 研究：分析知识图谱结构和关系

    查询模式行为：
    - local: 返回实体及其直接关系 + 相关文本块
    - global: 返回知识图谱中的关系模式
    - hybrid: 结合本地和全局检索策略
    - naive: 仅返回向量检索的文本块（无知识图谱）
    - mix: 集成知识图谱数据与向量检索的文本块
    - bypass: 返回空数据数组（用于直接 LLM 查询）

    参数：
        query: 要分析的搜索查询（至少3个字符）
        mode: 检索策略，影响返回的数据类型 (local, global, hybrid, naive, mix, bypass)
        top_k: 要检索的顶部实体/关系数量
        chunk_top_k: 要检索的文本块数量
        max_entity_tokens: 实体上下文的令牌限制
        max_relation_tokens: 关系上下文的令牌限制
        max_total_tokens: 检索的总体令牌预算
        hl_keywords: 高级别关键词列表（跳过初始 LLM 调用）
        ll_keywords: 低级别关键词列表（跳过初始 LLM 调用）
        enable_rerank: 是否启用重排序

    返回：
        结构化 JSON 响应，包含实体、关系、文本块、引用和元数据

    示例：
        分析实体关系：
            rag_query_data(query="机器学习算法", mode="local", top_k=10)

        探索全局模式：
            rag_query_data(query="人工智能趋势", mode="global", max_relation_tokens=2000)

        向量相似性搜索：
            rag_query_data(query="神经网络架构", mode="naive", chunk_top_k=5)

        提供关键词跳过 LLM：
            rag_query_data(
                query="什么是检索增强生成?",
                hl_keywords=["机器学习", "信息检索"],
                ll_keywords=["RAG", "知识库"],
                mode="mix"
            )
    """
    client = ctx.request_context.lifespan_context.client

    # 验证模式
    valid_modes = ["local", "global", "hybrid", "naive", "mix", "bypass"]
    if mode not in valid_modes:
        return f"❌ 无效的查询模式：{mode}\n有效模式：{', '.join(valid_modes)}"

    try:
        response = await client.query_data(
            query=query,
            mode=mode,  # type: ignore
            top_k=top_k,
            chunk_top_k=chunk_top_k,
            max_entity_tokens=max_entity_tokens,
            max_relation_tokens=max_relation_tokens,
            max_total_tokens=max_total_tokens,
            hl_keywords=hl_keywords,
            ll_keywords=ll_keywords,
            enable_rerank=enable_rerank,
            include_references=True,
            include_chunk_content=True
        )

        # 构建输出
        output = f"📊 RAG 数据检索结果\n"
        output += f"{'='*80}\n\n"
        output += f"📝 查询：{query}\n"
        output += f"🔧 模式：{mode}\n"
        output += f"📈 状态：{response.status}\n"
        output += f"💬 消息：{response.message}\n\n"

        if response.data:
            data = response.data

            # 实体信息
            output += f"{'='*80}\n"
            output += f"🏷️ 实体 ({len(data.entities)} 个)\n"
            output += f"{'='*80}\n"
            if data.entities:
                for i, entity in enumerate(data.entities[:10], 1):
                    output += f"\n{i}. {entity.entity_name}\n"
                    output += f"   类型：{entity.entity_type}\n"
                    if entity.description:
                        desc_preview = entity.description[:150]
                        if len(entity.description) > 150:
                            desc_preview += "..."
                        output += f"   描述：{desc_preview}\n"
                    if entity.file_path:
                        output += f"   来源：{entity.file_path}\n"
                    if entity.reference_id:
                        output += f"   引用ID：[{entity.reference_id}]\n"
                if len(data.entities) > 10:
                    output += f"\n... 还有 {len(data.entities) - 10} 个实体未显示\n"
            else:
                output += "（无实体数据）\n"

            # 关系信息
            output += f"\n{'='*80}\n"
            output += f"🔗 关系 ({len(data.relationships)} 个)\n"
            output += f"{'='*80}\n"
            if data.relationships:
                for i, rel in enumerate(data.relationships[:10], 1):
                    output += f"\n{i}. {rel.src_id} → {rel.tgt_id}\n"
                    if rel.description:
                        desc_preview = rel.description[:150]
                        if len(rel.description) > 150:
                            desc_preview += "..."
                        output += f"   描述：{desc_preview}\n"
                    if rel.keywords:
                        output += f"   关键词：{rel.keywords}\n"
                    output += f"   权重：{rel.weight:.3f}\n"
                    if rel.file_path:
                        output += f"   来源：{rel.file_path}\n"
                    if rel.reference_id:
                        output += f"   引用ID：[{rel.reference_id}]\n"
                if len(data.relationships) > 10:
                    output += f"\n... 还有 {len(data.relationships) - 10} 个关系未显示\n"
            else:
                output += "（无关系数据）\n"

            # 文本块信息
            output += f"\n{'='*80}\n"
            output += f"📄 文本块 ({len(data.chunks)} 个)\n"
            output += f"{'='*80}\n"
            if data.chunks:
                for i, chunk in enumerate(data.chunks[:5], 1):
                    output += f"\n{i}. [ID: {chunk.chunk_id}]\n"
                    if chunk.file_path:
                        output += f"   来源：{chunk.file_path}\n"
                    if chunk.content:
                        content_preview = chunk.content[:200].replace('\n', ' ')
                        if len(chunk.content) > 200:
                            content_preview += "..."
                        output += f"   内容：{content_preview}\n"
                    if chunk.reference_id:
                        output += f"   引用ID：[{chunk.reference_id}]\n"
                if len(data.chunks) > 5:
                    output += f"\n... 还有 {len(data.chunks) - 5} 个文本块未显示\n"
            else:
                output += "（无文本块数据）\n"

            # 引用信息
            output += f"\n{'='*80}\n"
            output += f"📚 引用 ({len(data.references)} 个)\n"
            output += f"{'='*80}\n"
            if data.references:
                for ref in data.references:
                    output += f"  [{ref.reference_id}] {ref.file_path}\n"
            else:
                output += "（无引用数据）\n"

        # 元数据信息
        if response.metadata:
            meta = response.metadata
            output += f"\n{'='*80}\n"
            output += f"📋 元数据\n"
            output += f"{'='*80}\n"
            output += f"查询模式：{meta.query_mode}\n"

            if meta.keywords:
                if meta.keywords.high_level:
                    output += f"高级别关键词：{', '.join(meta.keywords.high_level)}\n"
                if meta.keywords.low_level:
                    output += f"低级别关键词：{', '.join(meta.keywords.low_level)}\n"

            if meta.processing_info:
                info = meta.processing_info
                output += f"\n处理统计：\n"
                output += f"  - 找到的总实体数：{info.total_entities_found}\n"
                output += f"  - 找到的总关系数：{info.total_relations_found}\n"
                output += f"  - 截断后的实体数：{info.entities_after_truncation}\n"
                output += f"  - 截断后的关系数：{info.relations_after_truncation}\n"
                output += f"  - 最终文本块数：{info.final_chunks_count}\n"

        return output

    except ValueError as e:
        return f"❌ 参数错误：{str(e)}"
    except RuntimeError as e:
        return f"❌ 服务器错误：{str(e)}"
    except Exception as e:
        return f"❌ 查询失败：{str(e)}"


@mcp.tool()
async def rag_query_data_json(
    query: str,
    mode: str = "mix",
    top_k: int = 10,
    chunk_top_k: int = 5,
    max_entity_tokens: Optional[int] = None,
    max_relation_tokens: Optional[int] = None,
    max_total_tokens: Optional[int] = None,
    hl_keywords: Optional[List[str]] = None,
    ll_keywords: Optional[List[str]] = None,
    enable_rerank: bool = True,
    ctx: Context = None
) -> str:
    """
    高级数据检索端点（JSON 格式输出），用于结构化 RAG 分析。

    与 rag_query_data 功能相同，但返回原始 JSON 格式数据，
    便于程序化处理和系统集成。

    参数：
        query: 要分析的搜索查询（至少3个字符）
        mode: 检索策略 (local, global, hybrid, naive, mix, bypass)
        top_k: 要检索的顶部实体/关系数量
        chunk_top_k: 要检索的文本块数量
        max_entity_tokens: 实体上下文的令牌限制
        max_relation_tokens: 关系上下文的令牌限制
        max_total_tokens: 检索的总体令牌预算
        hl_keywords: 高级别关键词列表
        ll_keywords: 低级别关键词列表
        enable_rerank: 是否启用重排序

    返回：
        JSON 格式的结构化响应
    """
    client = ctx.request_context.lifespan_context.client

    # 验证模式
    valid_modes = ["local", "global", "hybrid", "naive", "mix", "bypass"]
    if mode not in valid_modes:
        return json.dumps({
            "status": "failure",
            "message": f"无效的查询模式：{mode}。有效模式：{valid_modes}",
            "data": None,
            "metadata": None
        }, ensure_ascii=False, indent=2)

    try:
        response = await client.query_data(
            query=query,
            mode=mode,  # type: ignore
            top_k=top_k,
            chunk_top_k=chunk_top_k,
            max_entity_tokens=max_entity_tokens,
            max_relation_tokens=max_relation_tokens,
            max_total_tokens=max_total_tokens,
            hl_keywords=hl_keywords,
            ll_keywords=ll_keywords,
            enable_rerank=enable_rerank,
            include_references=True,
            include_chunk_content=True
        )

        # 转换为字典
        result = {
            "status": response.status,
            "message": response.message,
            "data": None,
            "metadata": None
        }

        if response.data:
            result["data"] = {
                "entities": [e.model_dump() for e in response.data.entities],
                "relationships": [r.model_dump() for r in response.data.relationships],
                "chunks": [c.model_dump() for c in response.data.chunks],
                "references": [ref.model_dump() for ref in response.data.references]
            }

        if response.metadata:
            result["metadata"] = {
                "query_mode": response.metadata.query_mode,
                "keywords": response.metadata.keywords.model_dump() if response.metadata.keywords else None,
                "processing_info": response.metadata.processing_info.model_dump() if response.metadata.processing_info else None
            }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except ValueError as e:
        return json.dumps({
            "status": "failure",
            "message": f"参数错误：{str(e)}",
            "data": None,
            "metadata": None
        }, ensure_ascii=False, indent=2)
    except RuntimeError as e:
        return json.dumps({
            "status": "failure",
            "message": f"服务器错误：{str(e)}",
            "data": None,
            "metadata": None
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "failure",
            "message": f"查询失败：{str(e)}",
            "data": None,
            "metadata": None
        }, ensure_ascii=False, indent=2)


# ============================================================================
# 主入口点
# ============================================================================

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="LightRAG MCP 服务器")
    parser.add_argument(
        "--lightrag-url", type=str, default="http://localhost:9621",
        help="LightRAG 服务器 URL"
    )
    parser.add_argument(
        "--lightrag-api-key", type=str, default=None,
        help="LightRAG API 密钥"
    )
    parser.add_argument(
        "--timeout", type=float, default=60.0,
        help="请求超时时间（秒）"
    )
    parser.add_argument(
        "--sse", action="store_true", default=True,
        help="启用 SSE 模式"
    )
    parser.add_argument(
        "--port", type=int, default=8002,
        help="SSE 服务器端口号"
    )
    return parser.parse_args()


def main():
    """主入口点"""
    load_dotenv()
    args = parse_arguments()

    mcp.config = {
        "lightrag_base_url": os.environ.get("LIGHTRAG_BASE_URL", args.lightrag_url),
        "lightrag_api_key": os.environ.get("LIGHTRAG_API_KEY", args.lightrag_api_key),
        "timeout": float(os.environ.get("LIGHTRAG_TIMEOUT", args.timeout))
    }

    if args.sse:
        mcp.run(transport="sse", port=args.port, host="0.0.0.0")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
