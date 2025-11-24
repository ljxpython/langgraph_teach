"""
基于 RAG-Anything + LightRAG + Milvus 的简易 FastMCP 服务。

提供四个工具：
- rag_query_rewrite：多样化查询改写
- rag_retrieve：单查询检索
- rag_answer：可选改写 + 聚合回答
- rag_multi_query_search：多查询检索并聚合
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastmcp import Context, FastMCP
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
from raganything import RAGAnything, RAGAnythingConfig
from anything_rag_server.collections_tool import (
    get_available_collections,
    get_available_collections_raw,
)
import asyncio

# --------------------------------------------------------------------------- #
# 环境与初始化
# --------------------------------------------------------------------------- #


def _append_v1(url: Optional[str]) -> Optional[str]:
    if not url:
        return url
    cleaned = url.rstrip("/")
    if not cleaned.endswith("/v1"):
        cleaned += "/v1"
    return cleaned


@dataclass
class ServiceSettings:
    llm_api_key: str
    llm_base_url: Optional[str]
    llm_model: str
    vlm_model: Optional[str]
    vlm_base_url: Optional[str]
    vlm_api_key: Optional[str]
    embedding_api_key: Optional[str]
    embedding_model: str
    embedding_base_url: Optional[str]
    working_dir: str
    parser: str
    parse_method: str
    enable_image: bool
    enable_table: bool
    enable_equation: bool
    milvus_uri: Optional[str]
    milvus_collection: str


def load_settings() -> ServiceSettings:
    load_dotenv()

    # 允许通过 ANYTHING_RAG_COLLECTION / ANYTHING_RAG_MILVUS_COLLECTION 优先覆盖集合名，避免导入/检索集合不一致
    collection_override = (
        os.getenv("ANYTHING_RAG_COLLECTION")
        or os.getenv("ANYTHING_RAG_MILVUS_COLLECTION")
        or os.getenv("MILVUS_COLLECTION_NAME")
    )

    return ServiceSettings(
        llm_api_key=os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY", ""),
        llm_base_url=os.getenv("DEEPSEEK_API_BASE") or os.getenv("LLM_BASE_URL"),
        llm_model=os.getenv("LLM_MODEL", "deepseek-chat"),
        vlm_model=os.getenv("IMAGE_PARSER_MODEL"),
        vlm_base_url=os.getenv("IMAGE_PARSER_API_BASE"),
        vlm_api_key=os.getenv("IMAGE_PARSER_API_KEY"),
        embedding_api_key=os.getenv("EMBEDDING_API_KEY")
        or os.getenv("DEEPSEEK_API_KEY")
        or os.getenv("LLM_API_KEY"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "qwen3-embedding:0.6b"),
        embedding_base_url=_append_v1(os.getenv("EMBEDDING_BASE_URL")),
        working_dir=os.getenv("RAG_WORKDIR", "./rag_storage"),
        parser=os.getenv("RAG_PARSER", "docling"),
        parse_method=os.getenv("RAG_PARSE_METHOD", "auto"),
        enable_image=os.getenv("ENABLE_IMAGE", "true").lower() != "false",
        enable_table=os.getenv("ENABLE_TABLE", "true").lower() != "false",
        enable_equation=os.getenv("ENABLE_EQUATION", "true").lower() != "false",
        milvus_uri=os.getenv("MILVUS_URI"),
        milvus_collection=collection_override or "knowledge_base",
    )


# --------------------------------------------------------------------------- #
# RAG 服务封装
# --------------------------------------------------------------------------- #


class AnythingRAGService:
    def __init__(self, settings: ServiceSettings):
        if not settings.llm_api_key:
            raise RuntimeError("缺少 LLM API Key，请设置 DEEPSEEK_API_KEY 或 LLM_API_KEY")

        self.settings = settings
        self.current_collection = settings.milvus_collection
        if settings.milvus_uri:
            os.environ["MILVUS_URI"] = settings.milvus_uri

        self.embedding_func = EmbeddingFunc(
            embedding_dim=1024,
            max_token_size=8192,
            func=lambda texts: openai_embed(
                texts,
                model=settings.embedding_model,
                api_key=settings.embedding_api_key or settings.llm_api_key,
                base_url=settings.embedding_base_url,
            ),
        )

        def llm_model_func(prompt, system_prompt=None, history_messages=None, **kwargs):
            return openai_complete_if_cache(
                settings.llm_model,
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages or [],
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                **kwargs,
            )
        self.llm_model_func = llm_model_func

        def vision_model_func(
            prompt,
            system_prompt=None,
            history_messages=None,
            image_data=None,
            messages=None,
            **kwargs,
        ):
            if messages:
                return openai_complete_if_cache(
                    settings.vlm_model or settings.llm_model,
                    "",
                    system_prompt=None,
                    history_messages=[],
                    messages=messages,
                    api_key=settings.vlm_api_key or settings.llm_api_key,
                    base_url=settings.vlm_base_url or settings.llm_base_url,
                    **kwargs,
                )
            if image_data:
                return openai_complete_if_cache(
                    settings.vlm_model or settings.llm_model,
                    "",
                    system_prompt=None,
                    history_messages=[],
                    messages=[
                        {"role": "system", "content": system_prompt}
                        if system_prompt
                        else None,
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                                },
                            ],
                        },
                    ],
                    api_key=settings.vlm_api_key or settings.llm_api_key,
                    base_url=settings.vlm_base_url or settings.llm_base_url,
                    **kwargs,
                )
            return llm_model_func(prompt, system_prompt, history_messages or [], **kwargs)
        self.vision_model_func = vision_model_func

        lightrag_kwargs: Dict[str, Any] = {}
        if settings.milvus_uri:
            lightrag_kwargs = {
                "vector_storage": "MilvusVectorDBStorage",
                "workspace": self.current_collection,
            }
        self.lightrag_kwargs = lightrag_kwargs

        self.rag = self._create_rag()

    def _create_rag(self) -> RAGAnything:
        """按当前 settings/lightrag_kwargs 重建 RAG 实例。"""
        return RAGAnything(
            config=RAGAnythingConfig(
                working_dir=self.settings.working_dir,
                parser=self.settings.parser,
                parse_method=self.settings.parse_method,
                enable_image_processing=self.settings.enable_image,
                enable_table_processing=self.settings.enable_table,
                enable_equation_processing=self.settings.enable_equation,
            ),
            llm_model_func=self.llm_model_func,
            vision_model_func=self.vision_model_func,
            embedding_func=self.embedding_func,
            lightrag_kwargs=self.lightrag_kwargs,
        )

    def _switch_collection(self, collection: str | None):
        """在同一进程内动态切换集合（workspace），保持导入/检索一致。"""
        if not collection or collection == self.current_collection:
            return
        self.current_collection = collection
        # 更新 settings，便于后续再用
        self.settings.milvus_collection = collection
        if self.settings.milvus_uri:
            self.lightrag_kwargs = {
                "vector_storage": "MilvusVectorDBStorage",
                "workspace": collection,
            }
        else:
            self.lightrag_kwargs = {}
        self.rag = self._create_rag()

    async def _ensure_ready(self):
        """
        确保 LightRAG 初始化；如 Milvus 不可用则自动回退到本地存储。
        """
        init_result = await self.rag._ensure_lightrag_initialized()
        if isinstance(init_result, dict) and init_result.get("success") is False:
            error_msg = init_result.get("error") or ""
            # Milvus 无法连接时回退到本地文件存储
            if self.lightrag_kwargs and "Milvus" in error_msg:
                self.lightrag_kwargs = {}
                # 重建 rag 对象并重试
                self.rag = RAGAnything(
                    config=self.rag.config,
                    llm_model_func=self.llm_model_func,
                    vision_model_func=self.vision_model_func,
                    embedding_func=self.embedding_func,
                    lightrag_kwargs={},
                )
                retry = await self.rag._ensure_lightrag_initialized()
                if isinstance(retry, dict) and retry.get("success") is False:
                    raise RuntimeError(
                        f"LightRAG 初始化失败：{retry.get('error') or '未知原因'}"
                    )
                return retry

            raise RuntimeError(f"LightRAG 初始化失败：{error_msg or '未知原因'}")
        return init_result

    async def rewrite_queries(self, question: str, num_variants: int = 3) -> List[Dict[str, str]]:
        prompt = f"将下面的问题改写为 {num_variants} 个更利于检索的查询，输出 JSON 数组，每个元素含 strategy 和 query 字段：{question}"
        system_prompt = (
            "你是查询改写助手，保持语义一致，策略可包含 original/simplify/expand/rephrase/decompose。"
        )
        raw = self.llm_model_func(prompt, system_prompt=system_prompt)
        if asyncio.iscoroutine(raw):
            raw = await raw
        try:
            data = json.loads(raw)
            results = []
            for item in data:
                results.append(
                    {
                        "strategy": item.get("strategy", "variant"),
                        "query": item.get("query") or item.get("rewritten") or question,
                    }
                )
            return results or [{"strategy": "original", "query": question}]
        except Exception:
            lines = [line.strip("-• ").strip() for line in raw.splitlines() if line.strip()]
            variants = lines[:num_variants] or [question]
            return [{"strategy": "variant", "query": q} for q in variants]

    async def _aquery(self, query: str, mode: str = "hybrid", collection: str | None = None) -> Any:
        # 切换 workspace（集合）后再初始化
        self._switch_collection(collection)
        # 确保 LightRAG 初始化完成，必要时回退到本地存储
        await self._ensure_ready()

        try:
            return await self.rag.aquery(query, mode=mode)
        except TypeError:
            # 兼容旧版本 raganything 的接口签名
            return await self.rag.aquery(query)

    async def retrieve(self, query: str, mode: str = "hybrid", collection: str | None = None) -> Dict[str, Any]:
        result = await self._aquery(query, mode=mode, collection=collection)
        return {
            "query": query,
            "mode": mode,
            "result": result,
        }

    async def multi_retrieve(
        self, queries: List[str], mode: str = "hybrid", collection: str | None = None
    ) -> List[Dict[str, Any]]:
        outputs = []
        for q in queries:
            outputs.append(await self.retrieve(q, mode, collection))
        return outputs

    async def answer(
        self,
        question: str,
        mode: str = "hybrid",
        use_rewrite: bool = True,
        num_variants: int = 3,
        collection: str | None = None,
    ) -> Dict[str, Any]:
        variants = [{"strategy": "original", "query": question}]
        if use_rewrite:
            variants = await self.rewrite_queries(question, num_variants=num_variants)

        retrievals = []
        for variant in variants:
            retrievals.append(await self.retrieve(variant["query"], mode, collection))

        context_blocks = []
        for item in retrievals:
            content = item.get("result", "")
            context_blocks.append(f"[{item['mode']}] {item['query']} -> {content}")

        synthesis_prompt = (
            "根据以下检索结果生成回答，引用关键信息，保持简洁：\n\n"
            + "\n\n".join(context_blocks)
            + "\n\n用户问题："
            + question
        )
        final_answer = self.llm_model_func(synthesis_prompt)
        if asyncio.iscoroutine(final_answer):
            final_answer = await final_answer
        return {
            "question": question,
            "mode": mode,
            "use_rewrite": use_rewrite,
            "variants": variants,
            "answer": final_answer,
            "retrievals": retrievals,
        }


# --------------------------------------------------------------------------- #
# MCP Server
# --------------------------------------------------------------------------- #


@dataclass
class ServiceContext:
    service: AnythingRAGService


@asynccontextmanager
async def lifespan(server: FastMCP):
    settings = load_settings()
    service = AnythingRAGService(settings)
    yield ServiceContext(service)


mcp = FastMCP(name="anything-rag", lifespan=lifespan)


@mcp.tool()
async def rag_query_rewrite(question: str, num_variants: int = 3, ctx: Context | None = None) -> Dict[str, Any]:
    """
    将用户问题改写为多个检索友好的表达方式。

    参数：
    - question：用户原始问题，必须提供完整语句。
    - num_variants：希望生成的改写数量（默认 3）。
    - ctx：MCP 上下文，LangGraph/LC 会自动注入，无需手动传递。

    返回：
    - question：原始问题
    - variants：改写后的查询列表，每项包含 strategy 和 query。
    """
    service = ctx.request_context.lifespan_context.service
    variants = await service.rewrite_queries(question, num_variants=num_variants)
    return {"question": question, "variants": variants}


@mcp.tool()
async def rag_retrieve(
    query: str,
    mode: str = "hybrid",
    collection: str | None = None,
    ctx: Context | None = None,
) -> Dict[str, Any]:
    """
    对指定查询执行检索，按请求的模式返回检索结果。

    参数：
    - query：要检索的文本。
    - mode：检索模式（hybrid/dense/sparse 等），默认 hybrid。
    - ctx：MCP 上下文，自动注入。

    返回：
    - 包含 query、mode 以及底层检索结果的字典。
    """
    service = ctx.request_context.lifespan_context.service
    return await service.retrieve(query, mode=mode, collection=collection)


@mcp.tool()
async def rag_answer(
    question: str,
    mode: str = "hybrid",
    use_rewrite: bool = True,
    num_variants: int = 3,
    collection: str | None = None,
    ctx: Context | None = None,
) -> Dict[str, Any]:
    """
    结合检索与可选的查询改写，生成带引用的最终回答。

    参数：
    - question：用户问题。
    - mode：检索模式（hybrid/dense/sparse 等），默认 hybrid。
    - use_rewrite：是否先对问题进行多路改写再检索。
    - num_variants：改写条目数量，use_rewrite=True 时生效。
    - ctx：MCP 上下文，自动注入。

    返回：
    - question/mode/use_rewrite：本次调用的配置
    - variants：采用的查询变体
    - retrievals：每个查询的检索结果
    - answer：聚合后的回答
    """
    service = ctx.request_context.lifespan_context.service
    return await service.answer(
        question, mode=mode, use_rewrite=use_rewrite, num_variants=num_variants, collection=collection
    )


@mcp.tool()
async def rag_multi_query_search(
    queries: List[str],
    mode: str = "hybrid",
    collection: str | None = None,
    ctx: Context | None = None,
) -> Dict[str, Any]:
    """
    同时对多条查询执行检索，并返回各自的结果列表。

    参数：
    - queries：查询字符串列表。
    - mode：检索模式，默认 hybrid。
    - ctx：MCP 上下文，自动注入。

    返回：
    - mode：本次检索的模式
    - results：每条查询对应的检索结果集合
    """
    service = ctx.request_context.lifespan_context.service
    results = await service.multi_retrieve(queries, mode=mode, collection=collection)
    return {"mode": mode, "results": results, "collection": collection}


@mcp.tool()
async def list_collections(ctx: Context | None = None) -> Dict[str, Any]:
    """
    列出可用集合（来自 Milvus 或本地 collections.json）。
    便于调用方选择 collection 再进行检索/回答。
    """
    # 直接复用 collections_tool 的逻辑
    try:
        data = json.loads(get_available_collections_raw())
    except Exception:
        data = get_available_collections()
    return {"collections": data}


def main():
    parser = argparse.ArgumentParser(description="Anything RAG FastMCP Server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--sse", action="store_true", help="启用 SSE 传输")
    args = parser.parse_args()

    print("启动 Anything RAG MCP 服务")
    print(f"工作目录: {load_settings().working_dir}")
    if args.sse:
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        # stdio 模式无需 host/port，避免传参导致 fastmcp 抛出意外参数错误
        mcp.run()


if __name__ == "__main__":
    main()
