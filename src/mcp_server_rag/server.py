"""
专业的 RAG MCP 服务器 - 多策略检索优化

本 MCP 服务器提供高级 RAG 功能，包括：
- 多策略查询改写
- 从向量数据库并行检索
- 使用 LLM 评估的智能重排序
- 上下文感知的答案合成

架构：
1. 查询改写器：生成多个查询变体
2. 并行检索：从知识库并行检索
3. 重排序器：去重和重排序结果
4. 合成器：生成带引用的最终答案
"""


import argparse
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional, List, Dict
from dotenv import load_dotenv
import json
import asyncio
from pathlib import Path

from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_milvus import Milvus, BM25BuiltInFunction
from langchain_ollama import OllamaEmbeddings


# ============================================================================
# 数据模型
# ============================================================================

class RewrittenQuery(BaseModel):
    """改写后的查询及其策略"""
    original: str = Field(description="原始查询")
    rewritten: str = Field(description="改写后的查询")
    strategy: str = Field(description="改写策略：simplify, expand, rephrase, decompose")


class QueryRewriteOutput(BaseModel):
    """查询改写的输出"""
    queries: List[RewrittenQuery] = Field(description="3-5个查询变体的列表")


class RetrievalResult(BaseModel):
    """单个检索结果"""
    query: str = Field(description="用于检索的查询")
    content: str = Field(description="检索到的内容")
    score: float = Field(description="相关性分数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")
    strategy: Optional[str] = Field(default=None, description="使用的查询策略")


class RAGResponse(BaseModel):
    """完整的 RAG 响应"""
    answer: str = Field(description="最终合成的答案")
    sources: List[Dict[str, Any]] = Field(description="使用的源文档")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="响应元数据")


# ============================================================================
# RAG 连接器
# ============================================================================

class RAGConnector:
    """管理 RAG 操作，包括 LLM 和向量存储连接"""

    def __init__(
        self,
        llm_provider: str = "deepseek",
        llm_model: str = "deepseek-chat",
        llm_api_key: Optional[str] = None,
        llm_base_url: Optional[str] = "https://api.deepseek.com/v1",
        embedding_model: str = "qwen3-embedding:0.6b",
        embedding_base_url: str = "http://101.126.90.71:11434",
        milvus_uri: str = "http://101.126.90.71:19530",
        milvus_collection: Optional[str] = None,
    ):
        """使用 LLM 和向量存储初始化 RAG 连接器"""

        # 初始化 LLM
        if llm_api_key:
            os.environ[f"{llm_provider.upper()}_API_KEY"] = llm_api_key

        self.llm = init_chat_model(f"{llm_provider}:{llm_model}", base_url=llm_base_url)

        # 初始化嵌入模型
        self.embeddings = OllamaEmbeddings(
            model=embedding_model,
            base_url=embedding_base_url
        )

        # 初始化向量存储
        self.milvus_uri = milvus_uri
        self.milvus_collection = milvus_collection
        self.vector_store: Milvus = None

        if milvus_collection:
            self._init_vector_store(milvus_collection)

    def _init_vector_store(self, collection_name: str):
        """使用集合初始化向量存储"""
        self.vector_store = Milvus(
            embedding_function=self.embeddings,
            connection_args={"uri": self.milvus_uri},
            collection_name=collection_name,
            builtin_function=BM25BuiltInFunction(),
            vector_field=["dense", "sparse"],
        )

    def set_collection(self, collection_name: str):
        """切换到不同的集合"""
        print(f"[DEBUG] set_collection 被调用: collection_name={collection_name}")
        print(f"[DEBUG] 当前 vector_store 状态: {self.vector_store is not None}")
        self.milvus_collection = collection_name
        self._init_vector_store(collection_name)
        print(f"[DEBUG] vector_store 初始化完成: {self.vector_store is not None}")
    
    async def rewrite_query(self, question: str, num_variants: int = 3) -> List[Dict[str, str]]:
        """
        使用不同策略将查询改写为多个变体

        参数：
            question: 用户的原始问题
            num_variants: 要生成的查询变体数量（3-5个）

        返回：
            带有策略的改写查询列表
        """
        structured_llm = self.llm.with_structured_output(QueryRewriteOutput)

        system_prompt = f"""你是一个查询优化专家。将用户的问题改写为 {num_variants} 个不同的查询变体，以提高检索准确率。

策略：
1. original - 保留原始查询
2. simplify - 简化查询，提取核心关键词
3. expand - 扩展查询，添加相关概念和同义词
4. rephrase - 使用不同的表达方式重新表述
5. decompose - 将复杂问题分解为子问题

要求：
- 每个变体应使用不同的策略
- 改写后的查询应更好地匹配向量数据库中的文档
- 保持语义含义
- 生成 {num_variants} 个查询变体"""

        user_prompt = f"将以下问题改写为多个查询变体：\n\n{question}"

        try:
            response = structured_llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            return [q.model_dump() for q in response.queries]

        except Exception as e:
            # 降级处理：仅使用原始查询
            return [{
                "original": question,
                "rewritten": question,
                "strategy": "original"
            }]
    
    def _ensure_vector_store(self):
        """确保 vector_store 已初始化，如果未初始化则抛出友好的错误信息"""
        if not self.vector_store:
            error_msg = (
                "❌ 向量存储未初始化\n\n"
                "请先调用 rag_set_collection 工具设置集合，例如：\n"
                "  rag_set_collection(collection_name='your_collection_name')\n\n"
                f"当前状态：\n"
                f"  - Milvus URI: {self.milvus_uri}\n"
                f"  - 集合名称: {self.milvus_collection or '未设置'}\n"
                f"  - Vector Store: {'已初始化' if self.vector_store else '未初始化'}"
            )
            raise ValueError(error_msg)

    async def retrieve_documents(
        self,
        query: str,
        k: int = 3,
        strategy: Optional[str] = None
    ) -> List[RetrievalResult]:
        """
        从向量存储中检索文档

        参数：
            query: 查询文本
            k: 要检索的文档数量
            strategy: 使用的查询策略

        返回：
            检索结果列表
        """
        print(f"[DEBUG] retrieve_documents 被调用")
        print(f"[DEBUG] vector_store 状态: {self.vector_store is not None}")
        print(f"[DEBUG] milvus_collection: {self.milvus_collection}")

        # 确保 vector_store 已初始化
        self._ensure_vector_store()

        try:
            docs_with_scores = self.vector_store.similarity_search_with_score(query, k=k)

            results = []
            for doc, score in docs_with_scores:
                result = RetrievalResult(
                    query=query,
                    content=doc.page_content,
                    score=float(score),
                    metadata=doc.metadata,
                    strategy=strategy
                )
                results.append(result)

            return results

        except Exception as e:
            raise ValueError(f"检索失败：{str(e)}")
    
    async def rerank_results(
        self,
        results: List[RetrievalResult],
        question: str,
        top_k: int = 10
    ) -> List[RetrievalResult]:
        """
        重排序和去重结果

        参数：
            results: 检索结果列表
            question: 原始问题
            top_k: 要返回的顶部结果数量

        返回：
            重排序和去重后的结果
        """
        if not results:
            return []

        # 通过 pk（主键）去重
        seen_pks = set()
        deduped = []

        for result in results:
            pk = result.metadata.get("pk")
            if pk is not None:
                if pk not in seen_pks:
                    seen_pks.add(pk)
                    deduped.append(result)
            else:
                deduped.append(result)

        # 按分数排序（降序）
        deduped.sort(key=lambda x: x.score, reverse=True)

        # 多样性优化：优先选择不同来源
        diverse_results = []
        seen_sources = set()
        remaining = []

        for result in deduped:
            source = result.metadata.get("source", "unknown")
            if source not in seen_sources:
                diverse_results.append(result)
                seen_sources.add(source)
            else:
                remaining.append(result)

        diverse_results.extend(remaining)

        return diverse_results[:top_k]
    
    async def synthesize_answer(
        self,
        question: str,
        results: List[RetrievalResult],
        top_n: int = 5
    ) -> RAGResponse:
        """
        从检索到的文档合成最终答案

        参数：
            question: 原始问题
            results: 重排序后的检索结果
            top_n: 用于合成的顶部文档数量

        返回：
            包含答案和来源的 RAG 响应
        """
        if not results:
            return RAGResponse(
                answer="抱歉，没有找到相关文档来回答您的问题。请尝试换一种方式提问。",
                sources=[],
                metadata={"num_results": 0}
            )

        # 从 top-n 结果构建上下文
        context_parts = []
        sources = []

        for i, result in enumerate(results[:top_n], 1):
            source = result.metadata.get('source', 'unknown')
            content = result.content
            score = result.score

            context_part = f"""[文档 {i}]
来源：{source}
相关性分数：{score:.3f}
内容：
{content}"""
            context_parts.append(context_part)

            sources.append({
                "document_id": i,
                "source": source,
                "score": score,
                "content_preview": content[:200]
            })

        context = "\n\n" + "="*80 + "\n\n".join(context_parts)

        # 构建提示词
        system_prompt = """你是一个专业的问答助手。基于提供的文档回答用户问题。

要求：
1. **基于事实**：答案必须严格基于文档内容，不要编造
2. **引用来源**：使用 [文档 X] 格式标注信息来源
3. **综合信息**：如果多个文档提供了相关信息，请综合所有信息
4. **清晰准确**：使用要点或段落清晰地组织答案
5. **诚实表达**：如果文档缺乏足够信息，请明确说明

答案结构：
- 开头：直接回答核心问题
- 中间：提供详细解释和支持信息
- 结尾：总结要点或添加补充说明"""

        user_prompt = f"""基于以下文档回答问题：

{context}

用户问题：{question}

请提供详细准确的答案："""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            answer = response.content.strip()

            # 计算元数据
            unique_sources = set(r.metadata.get('source', 'unknown') for r in results)
            avg_score = sum(r.score for r in results[:top_n]) / min(top_n, len(results))

            return RAGResponse(
                answer=answer,
                sources=sources,
                metadata={
                    "num_results": len(results),
                    "num_sources": len(unique_sources),
                    "avg_score": avg_score,
                    "top_n_used": min(top_n, len(results))
                }
            )

        except Exception as e:
            # 降级处理：返回结构化摘要
            summary = f"# 来自 {len(results)} 个相关文档的信息摘要\n\n"
            summary += f"**问题**：{question}\n\n"
            summary += f"**注意**：LLM 生成失败，以下是文档摘要：\n\n"

            for i, result in enumerate(results[:5], 1):
                source = result.metadata.get('source', 'unknown')
                content_preview = result.content[:300].replace('\n', ' ')
                if len(result.content) > 300:
                    content_preview += "..."

                summary += f"## 文档 {i}（相关性：{result.score:.3f}）\n"
                summary += f"**来源**：{source}\n"
                summary += f"**内容**：{content_preview}\n\n"

            return RAGResponse(
                answer=summary,
                sources=sources,
                metadata={
                    "error": str(e),
                    "num_results": len(results)
                }
            )


# ============================================================================
# MCP 服务器设置
# ============================================================================

class RAGContext:
    """RAG 操作的上下文"""
    def __init__(self, connector: RAGConnector):
        self.connector = connector


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[RAGContext]:
    """管理 RAG 连接器的应用程序生命周期"""
    config = server.config
    
    # 从环境变量读取敏感配置，提供默认值
    llm_provider = os.getenv("LLM_PROVIDER", config.get("llm_provider", "deepseek"))
    llm_model = os.getenv("LLM_MODEL", config.get("llm_model", "deepseek-chat"))
    llm_api_key = os.getenv("LLM_API_KEY", config.get("llm_api_key"))
    llm_base_url = os.getenv("LLM_BASE_URL", config.get("llm_base_url", "https://api.deepseek.com/v1"))
    
    embedding_model = os.getenv("EMBEDDING_MODEL", config.get("embedding_model", "qwen3-embedding:0.6b"))
    embedding_base_url = os.getenv("EMBEDDING_BASE_URL", config.get("embedding_base_url", "http://121.40.159.60:11434"))
    
    milvus_uri = os.getenv("MILVUS_URI", config.get("milvus_uri", "http://121.40.159.60:19530"))
    milvus_collection = os.getenv("MILVUS_COLLECTION", config.get("milvus_collection"))

    # 验证必要的环境变量
    if not llm_api_key:
        raise ValueError(
            "❌ LLM_API_KEY 未设置\n"
            "请在 .env 文件中设置 LLM_API_KEY 或在命令行中提供 --llm-api-key 参数\n"
            "示例: export LLM_API_KEY=your_api_key"
        )

    connector = RAGConnector(
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_api_key=llm_api_key,
        llm_base_url=llm_base_url,
        embedding_model=embedding_model,
        embedding_base_url=embedding_base_url,
        milvus_uri=milvus_uri,
        milvus_collection=milvus_collection,
    )

    try:
        yield RAGContext(connector)
    finally:
        pass


mcp = FastMCP(name="RAG", lifespan=server_lifespan)


# ============================================================================
# MCP 工具
# ============================================================================

# # @mcp.tool()
# async def rag_get_status(
#     ctx: Context = None
# ) -> str:
#     """
#     获取 RAG 系统的当前状态。
#
#     返回当前集合名称和向量存储的初始化状态。
#     """
#     connector = ctx.request_context.lifespan_context.connector
#
#     status = f"""
# 📊 RAG 系统状态
# {'='*60}
# 🔗 Connector 对象 ID: {id(connector)}
# 📁 当前集合: {connector.milvus_collection or '未设置'}
# ✅ Vector Store 状态: {'已初始化' if connector.vector_store else '未初始化'}
# 🌐 Milvus URI: {connector.milvus_uri}
# {'='*60}
# """
#     return status


# # @mcp.tool()
# async def rag_set_collection(
#     collection_name: str,
#     ctx: Context = None
# ) -> str:
#     """
#     设置用于 RAG 操作的 Milvus 集合。
#
#     参数：
#         collection_name: Milvus 集合的名称
#     """
#     connector = ctx.request_context.lifespan_context.connector
#     print(f"[DEBUG] rag_set_collection 工具被调用")
#     print(f"[DEBUG] connector 对象 ID: {id(connector)}")
#
#     try:
#         connector.set_collection(collection_name)
#         # 验证设置是否成功
#         if connector.vector_store is None:
#             return f"⚠️ 警告：集合设置可能失败，vector_store 仍为 None"
#         return f"✅ 成功设置集合为 '{collection_name}'"
#     except Exception as e:
#         import traceback
#         error_detail = traceback.format_exc()
#         print(f"[ERROR] 设置集合失败: {error_detail}")
#         return f"❌ 设置集合失败：{str(e)}"
#

@mcp.tool()
async def rag_query_rewrite(
    question: str,
    num_variants: int = 3,
    ctx: Context = None
) -> str:
    """
    使用不同策略将用户问题改写为多个查询变体。

    通过生成多样化的查询表述来提高检索准确率。

    参数：
        question: 用户的原始问题
        num_variants: 要生成的查询变体数量（3-5个）
    """
    connector = ctx.request_context.lifespan_context.connector

    try:
        queries = await connector.rewrite_query(question, num_variants)

        output = f"查询改写结果（{len(queries)} 个变体）：\n\n"
        output += f"原始问题：{question}\n\n"
        output += "改写后的查询：\n"

        for i, q in enumerate(queries, 1):
            output += f"\n{i}. [{q['strategy']}]\n"
            output += f"   {q['rewritten']}\n"

        return output

    except Exception as e:
        return f"查询改写失败：{str(e)}"


@mcp.tool()
async def rag_retrieve(
    query: str,
    collection_name: Optional[str],
    k: int = 5,
    ctx: Context = None
) -> str:
    """
    从向量数据库检索相关文档。

    参数：
        query: 要搜索的查询文本
        collection_name: 集合名称（如果未全局设置）
        k: 要检索的文档数量
    """
    connector = ctx.request_context.lifespan_context.connector
    print(f"[DEBUG] rag_retrieve 工具被调用")
    print(f"[DEBUG] connector 对象 ID: {id(connector)}")
    print(f"[DEBUG] collection_name 参数: {collection_name}")
    print(f"[DEBUG] 当前 vector_store 状态: {connector.vector_store is not None}")

    try:
        # 如果提供了集合名称，则设置集合
        if collection_name:
            print(f"[DEBUG] 设置集合: {collection_name}")
            connector.set_collection(collection_name)
        elif not connector.vector_store:
            # 如果没有提供 collection_name 且 vector_store 未初始化，返回友好提示
            return (
                "❌ 检索失败：向量存储未初始化\n\n"
                "请先执行以下操作之一：\n"
                "1. 调用 rag_set_collection 设置集合：\n"
                "   rag_set_collection(collection_name='your_collection_name')\n\n"
                "2. 或者在调用 rag_retrieve 时提供 collection_name 参数：\n"
                "   rag_retrieve(query='...', collection_name='your_collection_name')\n\n"
                f"当前状态：\n"
                f"  - Milvus URI: {connector.milvus_uri}\n"
                f"  - 集合名称: {connector.milvus_collection or '未设置'}"
            )

        results = await connector.retrieve_documents(query, k=k)

        output = f"✅ 检索结果（{len(results)} 个文档）：\n\n"
        output += f"📝 查询：{query}\n"
        output += f"📁 集合：{connector.milvus_collection}\n\n"

        for i, result in enumerate(results, 1):
            source = result.metadata.get('source', 'unknown')
            output += f"\n{i}. [分数：{result.score:.3f}] {source}\n"
            content_preview = result.content[:200].replace('\n', ' ')
            if len(result.content) > 200:
                content_preview += "..."
            output += f"   {content_preview}\n"

        return output

    except ValueError as e:
        # ValueError 通常是我们自己抛出的友好错误
        return str(e)
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[ERROR] 检索失败: {error_detail}")
        return f"❌ 检索失败：{str(e)}"


@mcp.tool()
async def rag_answer(
    question: str,
    collection_name: Optional[str],
    num_variants: int = 3,
    k_per_query: int = 3,
    top_k: int = 10,
    top_n_synthesis: int = 5,
    ctx: Context = None
) -> str:
    """
    完整的 RAG 流程：改写查询、检索文档、重排序和合成答案。

    这是执行完整多策略检索优化的主要 RAG 工具。

    参数：
        question: 用户的问题
        collection_name: 集合名称
        num_variants: 要生成的查询变体数量（3-5个）
        k_per_query: 每个查询变体要检索的文档数量
        top_k: 重排序后保留的顶部文档数量
        top_n_synthesis: 用于答案合成的顶部文档数量
    """
    connector = ctx.request_context.lifespan_context.connector

    try:
        # 如果提供了集合名称，则设置集合
        if collection_name:
            connector.set_collection(collection_name)
        elif not connector.vector_store:
            # 如果没有提供 collection_name 且 vector_store 未初始化，返回友好提示
            return (
                "❌ RAG 流程失败：向量存储未初始化\n\n"
                "请先执行以下操作之一：\n"
                "1. 调用 rag_set_collection 设置集合：\n"
                "   rag_set_collection(collection_name='your_collection_name')\n\n"
                "2. 或者在调用 rag_answer 时提供 collection_name 参数：\n"
                "   rag_answer(question='...', collection_name='your_collection_name')\n\n"
                f"当前状态：\n"
                f"  - Milvus URI: {connector.milvus_uri}\n"
                f"  - 集合名称: {connector.milvus_collection or '未设置'}"
            )

        output = f"🚀 RAG 流程启动\n"
        output += f"{'='*80}\n\n"
        output += f"📥 问题：{question}\n\n"

        # 步骤 1：查询改写
        output += f"📝 步骤 1：查询改写\n"
        queries = await connector.rewrite_query(question, num_variants)
        output += f"   生成了 {len(queries)} 个查询变体\n"
        for i, q in enumerate(queries, 1):
            output += f"   {i}. [{q['strategy']}] {q['rewritten']}\n"
        output += "\n"

        # 步骤 2：并行检索
        output += f"🔍 步骤 2：并行检索\n"

        # 创建并行检索任务
        async def retrieve_for_query(q: Dict[str, str]) -> tuple[str, List[RetrievalResult]]:
            """为单个查询执行检索"""
            query_text = q.get("rewritten", q.get("original", ""))
            strategy = q.get("strategy", "unknown")
            results = await connector.retrieve_documents(
                query_text,
                k=k_per_query,
                strategy=strategy
            )
            return strategy, results

        # 并行执行所有检索任务
        retrieval_tasks = [retrieve_for_query(q) for q in queries]
        retrieval_results = await asyncio.gather(*retrieval_tasks)

        # 收集所有结果
        all_results = []
        for strategy, results in retrieval_results:
            all_results.extend(results)
            output += f"   [{strategy}] 检索到 {len(results)} 个文档\n"

        output += f"   总共检索：{len(all_results)} 个文档\n\n"

        # 步骤 3：重排序
        output += f"🎯 步骤 3：重排序和去重\n"
        reranked = await connector.rerank_results(all_results, question, top_k)
        output += f"   去重后：{len(reranked)} 个唯一文档\n"
        output += f"   选择 Top-{top_k} 用于合成\n\n"

        # 步骤 4：答案合成
        output += f"📝 步骤 4：答案合成\n"
        response = await connector.synthesize_answer(question, reranked, top_n_synthesis)
        output += f"   使用 top-{top_n_synthesis} 个文档\n"
        output += f"   平均相关性分数：{response.metadata.get('avg_score', 0):.3f}\n\n"

        output += f"{'='*80}\n"
        output += f"📤 最终答案\n"
        output += f"{'='*80}\n\n"
        output += response.answer
        output += f"\n\n{'='*80}\n"
        output += f"📊 元数据\n"
        output += f"{'='*80}\n"
        output += f"检索到的文档总数：{len(all_results)}\n"
        output += f"去重后的唯一文档：{len(reranked)}\n"
        output += f"用于合成的文档：{response.metadata.get('top_n_used', 0)}\n"
        output += f"唯一来源数：{response.metadata.get('num_sources', 0)}\n"
        output += f"平均相关性分数：{response.metadata.get('avg_score', 0):.3f}\n\n"

        output += f"📚 主要来源：\n"
        for i, source in enumerate(response.sources[:5], 1):
            output += f"{i}. {source['source']}（分数：{source['score']:.3f}）\n"

        return output

    except ValueError as e:
        # ValueError 通常是我们自己抛出的友好错误
        return str(e)
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[ERROR] RAG 流程失败: {error_detail}")
        return f"❌ RAG 流程失败：{str(e)}"


@mcp.tool()
async def rag_multi_query_search(
    queries: List[str],
    collection_name: Optional[str] = None,
    k_per_query: int = 3,
    top_k: int = 10,
    ctx: Context = None
) -> str:
    """
    使用自定义查询执行多查询搜索（不自动改写）。

    当您已经有多个查询表述时很有用。

    参数：
        queries: 查询字符串列表
        collection_name: 可选的集合名称
        k_per_query: 每个查询要检索的文档数量
        top_k: 去重后返回的顶部文档数量
    """
    connector = ctx.request_context.lifespan_context.connector

    try:
        # 如果提供了集合名称，则设置集合
        if collection_name:
            connector.set_collection(collection_name)
        elif not connector.vector_store:
            # 如果没有提供 collection_name 且 vector_store 未初始化，返回友好提示
            return (
                "❌ 多查询搜索失败：向量存储未初始化\n\n"
                "请先执行以下操作之一：\n"
                "1. 调用 rag_set_collection 设置集合：\n"
                "   rag_set_collection(collection_name='your_collection_name')\n\n"
                "2. 或者在调用 rag_multi_query_search 时提供 collection_name 参数：\n"
                "   rag_multi_query_search(queries=[...], collection_name='your_collection_name')\n\n"
                f"当前状态：\n"
                f"  - Milvus URI: {connector.milvus_uri}\n"
                f"  - 集合名称: {connector.milvus_collection or '未设置'}"
            )

        output = f"多查询搜索（{len(queries)} 个查询）：\n\n"

        # 创建并行检索任务
        async def retrieve_for_single_query(idx: int, query: str) -> tuple[int, str, List[RetrievalResult]]:
            """为单个查询执行检索"""
            results = await connector.retrieve_documents(query, k=k_per_query)
            return idx, query, results

        # 并行执行所有检索任务
        retrieval_tasks = [retrieve_for_single_query(i, q) for i, q in enumerate(queries, 1)]
        retrieval_results = await asyncio.gather(*retrieval_tasks)

        # 收集所有结果
        all_results = []
        for idx, query, results in sorted(retrieval_results, key=lambda x: x[0]):
            all_results.extend(results)
            output += f"{idx}. 查询：{query}\n"
            output += f"   检索到：{len(results)} 个文档\n\n"

        # 重排序和去重
        reranked = await connector.rerank_results(all_results, queries[0], top_k)

        output += f"{'='*80}\n"
        output += f"重排序结果（Top-{top_k}）：\n\n"

        for i, result in enumerate(reranked, 1):
            source = result.metadata.get('source', 'unknown')
            output += f"{i}. [分数：{result.score:.3f}] {source}\n"
            content_preview = result.content[:150].replace('\n', ' ')
            if len(result.content) > 150:
                content_preview += "..."
            output += f"   {content_preview}\n\n"

        return output

    except ValueError as e:
        # ValueError 通常是我们自己抛出的友好错误
        return str(e)
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[ERROR] 多查询搜索失败: {error_detail}")
        return f"❌ 多查询搜索失败：{str(e)}"


# ============================================================================
# 主入口点
# ============================================================================

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="RAG MCP 服务器")
    
    # 从环境变量获取默认值，避免硬编码敏感信息
    parser.add_argument(
        "--llm-provider", type=str, 
        default=os.getenv("LLM_PROVIDER", "deepseek"), 
        help="LLM 提供商（例如：deepseek, openai）"
    )
    parser.add_argument(
        "--llm-model", type=str, 
        default=os.getenv("LLM_MODEL", "deepseek-chat"), 
        help="LLM 模型名称"
    )
    parser.add_argument(
        "--llm-api-key", type=str, 
        default=os.getenv("LLM_API_KEY"), 
        help="LLM API 密钥"
    )
    parser.add_argument(
        "--llm-base-url", type=str, 
        default=os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1"), 
        help="LLM BASE URL"
    )
    parser.add_argument(
        "--embedding-model", type=str, 
        default=os.getenv("EMBEDDING_MODEL", "qwen3-embedding:0.6b"), 
        help="嵌入模型"
    )
    parser.add_argument(
        "--embedding-url", type=str, 
        default=os.getenv("EMBEDDING_BASE_URL", "http://localhost:11434"), 
        help="嵌入服务 URL"
    )
    parser.add_argument(
        "--milvus-uri", type=str, 
        default=os.getenv("MILVUS_URI", "http://localhost:19530"), 
        help="Milvus 服务器 URI"
    )
    parser.add_argument(
        "--milvus-collection", type=str, 
        default=os.getenv("MILVUS_COLLECTION"), 
        help="默认 Milvus 集合"
    )
    parser.add_argument("--sse", action="store_true", default=True, help="启用 SSE 模式")
    parser.add_argument(
        "--port", type=int, 
        default=int(os.getenv("SERVER_PORT", "8001")), 
        help="SSE 服务器端口号"
    )
    return parser.parse_args()


def main():
    """主入口点"""
    # 加载环境变量
    load_dotenv()
    
    # 检查是否存在 .env 文件
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        print(f"✅ 加载环境变量文件: {env_path}")
    else:
        print(f"⚠️  未找到 .env 文件，使用命令行参数或默认值")
    
    args = parse_arguments()

    # 构建配置，优先使用环境变量，然后是命令行参数，最后是默认值
    mcp.config = {
        "llm_provider": os.environ.get("LLM_PROVIDER", args.llm_provider),
        "llm_model": os.environ.get("LLM_MODEL", args.llm_model),
        "llm_api_key": os.environ.get("LLM_API_KEY", args.llm_api_key),
        "llm_base_url": os.environ.get("LLM_BASE_URL", args.llm_base_url),
        "embedding_model": os.environ.get("EMBEDDING_MODEL", args.embedding_model),
        "embedding_base_url": os.environ.get("EMBEDDING_BASE_URL", args.embedding_url),
        "milvus_uri": os.environ.get("MILVUS_URI", args.milvus_uri),
        "milvus_collection": os.environ.get("MILVUS_COLLECTION", args.milvus_collection),
    }
    
    # 显示配置摘要（隐藏敏感信息）
    print("\n" + "="*60)
    print("🔧 服务器配置摘要")
    print("="*60)
    print(f"LLM 提供商: {mcp.config['llm_provider']}")
    print(f"LLM 模型: {mcp.config['llm_model']}")
    print(f"LLM Base URL: {mcp.config['llm_base_url']}")
    print(f"嵌入模型: {mcp.config['embedding_model']}")
    print(f"嵌入服务 URL: {mcp.config['embedding_base_url']}")
    print(f"Milvus URI: {mcp.config['milvus_uri']}")
    print(f"默认集合: {mcp.config['milvus_collection'] or '未设置'}")
    print("="*60 + "\n")

    if args.sse:
        mcp.run(transport="sse", port=args.port, host="0.0.0.0")
    else:
        mcp.run()


if __name__ == "__main__":
    main()

