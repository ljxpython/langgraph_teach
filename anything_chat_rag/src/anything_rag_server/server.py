"""
基于 RAG-Anything + LightRAG 的本地向量库 FastMCP 服务。

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
from pathlib import Path
import sys
import inspect
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager
from types import MethodType

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
from fastmcp import Context, FastMCP
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
from lightrag.lightrag import QueryParam
try:
    from raganything import RAGAnything, RAGAnythingConfig
except ImportError:  # 兼容旧版包未导出 RAGAnythingConfig
    from raganything import RAGAnything  # type: ignore
    from raganything.config import RAGAnythingConfig  # type: ignore

try:
    from src.anything_rag_server.collections_tool import (
        get_available_collections,
        get_available_collections_raw,
    )
except ModuleNotFoundError:
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
    embedding_binding: str
    vlm_model: Optional[str]
    vlm_base_url: Optional[str]
    vlm_api_key: Optional[str]
    embedding_api_key: Optional[str]
    embedding_model: str
    embedding_dim: int
    embedding_base_url: Optional[str]
    embedding_binding_host: Optional[str]
    working_dir: str
    parser: str
    parse_method: str
    enable_image: bool
    enable_table: bool
    enable_equation: bool
    workspace: str
    vector_storage: str


def load_settings() -> ServiceSettings:
    load_dotenv()

    # workspace 优先级：专用 env > LightRAG 原生 WORKSPACE > 兼容旧的 collection 变量
    workspace_override = (
        os.getenv("ANYTHING_RAG_WORKSPACE")
        or os.getenv("WORKSPACE")
        or os.getenv("ANYTHING_RAG_COLLECTION")
        or os.getenv("ANYTHING_RAG_MILVUS_COLLECTION")
        or os.getenv("MILVUS_COLLECTION_NAME")
    )
    default_workdir = (
        os.getenv("RAG_WORKDIR")
        or os.getenv("WORKING_DIR")
        or str(Path("rag_storage").resolve())
    )

    embedding_binding = os.getenv("EMBEDDING_BINDING", "openai")
    raw_embedding_host = os.getenv("EMBEDDING_BINDING_HOST")
    raw_embedding_base = os.getenv("EMBEDDING_BASE_URL")

    # OpenAI 兼容接口需要 /v1，Ollama 等自托管则保持原样
    if embedding_binding in {"openai", "azure_openai"}:
        embedding_base_url = _append_v1(raw_embedding_base or raw_embedding_host)
        embedding_binding_host = raw_embedding_host or raw_embedding_base
    else:
        embedding_base_url = raw_embedding_base or raw_embedding_host
        embedding_binding_host = raw_embedding_host or raw_embedding_base

    return ServiceSettings(
        llm_api_key=os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY", ""),
        llm_base_url=os.getenv("DEEPSEEK_API_BASE") or os.getenv("LLM_BASE_URL"),
        llm_model=os.getenv("LLM_MODEL", "deepseek-chat"),
        embedding_binding=embedding_binding,
        vlm_model=os.getenv("IMAGE_PARSER_MODEL"),
        vlm_base_url=os.getenv("IMAGE_PARSER_API_BASE"),
        vlm_api_key=os.getenv("IMAGE_PARSER_API_KEY"),
        embedding_api_key=os.getenv("EMBEDDING_BINDING_API_KEY")
        or os.getenv("EMBEDDING_API_KEY")
        or os.getenv("DEEPSEEK_API_KEY")
        or os.getenv("LLM_API_KEY"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "qwen3-embedding:0.6b"),
        embedding_dim=int(os.getenv("EMBEDDING_DIM", 1536)),
        embedding_base_url=embedding_base_url,
        embedding_binding_host=embedding_binding_host,
        working_dir=default_workdir,
        parser=os.getenv("RAG_PARSER", "docling"),
        parse_method=os.getenv("RAG_PARSE_METHOD", "auto"),
        enable_image=os.getenv("ENABLE_IMAGE", "true").lower() != "false",
        enable_table=os.getenv("ENABLE_TABLE", "true").lower() != "false",
        enable_equation=os.getenv("ENABLE_EQUATION", "true").lower() != "false",
        workspace=workspace_override or "",
        vector_storage=(
            os.getenv("ANYTHING_RAG_VECTOR_STORAGE")
            or os.getenv("LIGHTRAG_VECTOR_STORAGE")
            or os.getenv("VECTOR_STORAGE")
            or "NanoVectorDBStorage"
        ),
    )


# --------------------------------------------------------------------------- #
# RAG 服务封装
# --------------------------------------------------------------------------- #


class AnythingRAGService:
    def __init__(self, settings: ServiceSettings):
        if not settings.llm_api_key:
            raise RuntimeError("缺少 LLM API Key，请设置 DEEPSEEK_API_KEY 或 LLM_API_KEY")

        self.settings = settings
        self.current_workspace = settings.workspace
        self.embedding_func = self._build_embedding_func(settings)

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

        lightrag_kwargs: Dict[str, Any] = {
            "vector_storage": settings.vector_storage,
        }
        # workspace 允许为空字符串，表示使用默认根目录
        if self.current_workspace is not None:
            lightrag_kwargs["workspace"] = self.current_workspace
        # 确保 LightRAG 工作目录与 server 配置一致（兼容旧版 RAGAnything 仅从 lightrag_kwargs 读 working_dir）
        lightrag_kwargs["working_dir"] = self.settings.working_dir
        self.lightrag_kwargs = lightrag_kwargs

        self.rag = self._create_rag()

    def _build_embedding_func(self, settings: ServiceSettings) -> EmbeddingFunc:
        binding = settings.embedding_binding or "openai"
        embedding_dim = settings.embedding_dim or 1536
        host = settings.embedding_base_url or settings.embedding_binding_host
        api_key = settings.embedding_api_key or settings.llm_api_key

        if binding == "ollama":
            from lightrag.llm.ollama import ollama_embed

            func = lambda texts: ollama_embed(  # noqa: E731
                texts,
                embed_model=settings.embedding_model,
                host=host,
                api_key=api_key,
            )
        elif binding in {"openai", "azure_openai"}:
            func = lambda texts: openai_embed(  # noqa: E731
                texts,
                model=settings.embedding_model,
                api_key=api_key or settings.llm_api_key,
                base_url=host,
                embedding_dim=embedding_dim,
                use_azure=binding == "azure_openai",
                azure_deployment=settings.embedding_model
                if binding == "azure_openai"
                else None,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION")
                or os.getenv("OPENAI_API_VERSION"),
            )
        elif binding == "gemini":
            from lightrag.llm.gemini import gemini_embed

            func = lambda texts: gemini_embed(  # noqa: E731
                texts,
                model=settings.embedding_model,
                base_url=host,
                api_key=api_key,
                embedding_dim=embedding_dim,
            )
        else:
            raise ValueError(f"不支持的 EMBEDDING_BINDING: {binding}")

        return EmbeddingFunc(
            embedding_dim=embedding_dim,
            max_token_size=8192,
            func=func,
        )

    def _create_rag(self) -> RAGAnything:
        """按当前 settings/lightrag_kwargs 重建 RAG 实例。"""
        config = RAGAnythingConfig(
            working_dir=self.settings.working_dir,
            parser=self.settings.parser,
            parse_method=self.settings.parse_method,
            enable_image_processing=self.settings.enable_image,
            enable_table_processing=self.settings.enable_table,
            enable_equation_processing=self.settings.enable_equation,
        )

        sig = inspect.signature(RAGAnything.__init__)
        params = set(sig.parameters.keys())

        base_kwargs = {
            k: v
            for k, v in {
                "llm_model_func": self.llm_model_func,
                "vision_model_func": self.vision_model_func,
                "embedding_func": self.embedding_func,
            }.items()
            if k in params
        }

        if "config" in params:
            base_kwargs["config"] = config
        else:
            base_kwargs["config_obj"] = config  # stash for later assignment

        # 优先使用 lightrag_kwargs，如果不支持则尝试直接传入 LightRAG 实例
        if "lightrag_kwargs" in params:
            base_kwargs["lightrag_kwargs"] = self.lightrag_kwargs
        elif "lightrag" in params:
            from lightrag import LightRAG  # local import to avoid module side-effects

            light_kwargs = {
                "working_dir": self.settings.working_dir,
                "llm_model_func": self.llm_model_func,
                "embedding_func": self.embedding_func,
                "vector_storage": self.settings.vector_storage,
            }
            # workspace 为空字符串时依旧传入，保证隔离
            light_kwargs["workspace"] = self.current_workspace or ""
            base_kwargs["lightrag"] = LightRAG(**light_kwargs)

        # 过滤掉不存在于签名的键
        call_kwargs = {k: v for k, v in base_kwargs.items() if k in params}
        rag = RAGAnything(**call_kwargs)

        # 兼容旧版 RAGAnything：手动绑定 config/working_dir
        if "config" not in params:
            cfg = base_kwargs.get("config_obj", config)
            try:
                rag.config = cfg  # type: ignore[attr-defined]
                rag.working_dir = cfg.working_dir  # type: ignore[attr-defined]
            except Exception:
                pass

        # 兼容极旧版 raganything：如果缺少 aquery/query，则挂接到底层 LightRAG
        if not hasattr(rag, "aquery"):
            async def _aquery_fallback(self, query: str, mode: str = "hybrid", **kwargs):
                qp = QueryParam(mode=mode)
                return await self.lightrag.aquery(query, param=qp)  # type: ignore[attr-defined]

            rag.aquery = MethodType(_aquery_fallback, rag)  # type: ignore[attr-defined]

        if not hasattr(rag, "query"):
            def _query_fallback(self, query: str, mode: str = "hybrid", **kwargs):
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(self.aquery(query, mode=mode, **kwargs))  # type: ignore[attr-defined]

            rag.query = MethodType(_query_fallback, rag)  # type: ignore[attr-defined]
        return rag

    def _switch_workspace(self, workspace: str | None):
        """在同一进程内动态切换 workspace，保持导入/检索一致。"""
        target_workspace = self.current_workspace if workspace is None else workspace
        if target_workspace == self.current_workspace:
            return

        self.current_workspace = target_workspace
        self.settings.workspace = target_workspace or ""
        self.lightrag_kwargs = {
            "vector_storage": self.settings.vector_storage,
        }
        # workspace 允许为空字符串
        if target_workspace is not None:
            self.lightrag_kwargs["workspace"] = target_workspace
        self.rag = self._create_rag()

    async def _ensure_ready(self):
        """
        确保 LightRAG 初始化，失败时抛出明确错误。
        """
        init_result = await self.rag._ensure_lightrag_initialized()
        if isinstance(init_result, dict) and init_result.get("success") is False:
            error_msg = init_result.get("error") or ""
            raise RuntimeError(f"LightRAG 初始化失败：{error_msg or '未知原因'}")
        return init_result

    async def rewrite_queries(self, question: str, num_variants: int = 3) -> List[Dict[str, str]]:
        prompt = (
            f"将下面的问题改写为 {num_variants} 个更利于检索的查询，输出 JSON 数组，每个元素含 strategy 和 query 字段：\n"
            f"问题：{question}\n"
            "示例输出：[{\"strategy\":\"original\",\"query\":\"...\"},{\"strategy\":\"simplify\",\"query\":\"...\"}]"
        )
        system_prompt = (
            "你是查询改写助手，保持语义一致，策略可包含 original/simplify/expand/rephrase/decompose。"
            "仅返回 JSON，不要添加 ```json 代码块。"
        )

        def _normalize_variants(raw_val) -> List[Dict[str, str]]:
            """尽量从模型输出提取 JSON，失败则回退原问题。"""
            # 已是结构化
            if isinstance(raw_val, list):
                data = raw_val
            else:
                text = str(raw_val).strip()
                # 去除代码块包裹
                if "```" in text:
                    parts = text.split("```")
                    # 取第一段 json 内容
                    if len(parts) >= 3:
                        text = parts[1].strip()
                if text.startswith("json"):
                    text = text[4:].strip()
                try:
                    data = json.loads(text)
                except Exception:
                    data = None

            results: List[Dict[str, str]] = []
            if isinstance(data, dict):
                data = data.get("variants") or data.get("queries") or data.get("data") or []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, str):
                        results.append({"strategy": "variant", "query": item})
                    elif isinstance(item, dict):
                        results.append(
                            {
                                "strategy": item.get("strategy", "variant"),
                                "query": item.get("query") or item.get("rewritten") or question,
                            }
                        )
            if not results:
                results = [{"strategy": "original", "query": question}]
            return results[:num_variants]

        raw = self.llm_model_func(prompt, system_prompt=system_prompt)
        if asyncio.iscoroutine(raw):
            raw = await raw

        return _normalize_variants(raw)

    async def _aquery(self, query: str, mode: str = "hybrid", workspace: str | None = None) -> Any:
        # 切换 workspace 后再初始化
        self._switch_workspace(workspace)
        # 确保 LightRAG 初始化完成
        await self._ensure_ready()

        # 优先调用 raganything 的异步接口，缺失时回退到底层 LightRAG
        if hasattr(self.rag, "aquery"):
            try:
                return await self.rag.aquery(query, mode=mode)  # type: ignore[arg-type]
            except TypeError:
                # 兼容旧版 raganything.aquery(query)
                return await self.rag.aquery(query)  # type: ignore[misc]

        # 旧版只暴露同步 query，避免阻塞事件循环，使用线程池执行
        if hasattr(self.rag, "query"):
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: self.rag.query(query, mode=mode))  # type: ignore[arg-type]

        # 最后兜底直接使用 LightRAG 实例
        if hasattr(self.rag, "lightrag") and hasattr(self.rag.lightrag, "aquery"):
            return await self.rag.lightrag.aquery(query, param=QueryParam(mode=mode))

        raise AttributeError("RAGAnything 实例缺少可用的查询接口（aquery/query）。")

    async def retrieve(self, query: str, mode: str = "hybrid", workspace: str | None = None) -> Dict[str, Any]:
        result = await self._aquery(query, mode=mode, workspace=workspace)
        resolved_workspace = workspace if workspace is not None else self.current_workspace
        return {
            "query": query,
            "mode": mode,
            "workspace": resolved_workspace,
            "collection": resolved_workspace,  # 兼容旧字段
            "result": result,
        }

    async def multi_retrieve(
        self, queries: List[str], mode: str = "hybrid", workspace: str | None = None
    ) -> List[Dict[str, Any]]:
        outputs = []
        for q in queries:
            outputs.append(await self.retrieve(q, mode, workspace))
        return outputs

    async def answer(
        self,
        question: str,
        mode: str = "hybrid",
        use_rewrite: bool = True,
        num_variants: int = 3,
        workspace: str | None = None,
    ) -> Dict[str, Any]:
        variants = [{"strategy": "original", "query": question}]
        if use_rewrite:
            variants = await self.rewrite_queries(question, num_variants=num_variants)

        retrievals = []
        for variant in variants:
            retrievals.append(await self.retrieve(variant["query"], mode, workspace))

        # 检查是否有有效上下文，避免无上下文时让 LLM 自行杜撰
        has_context = False
        context_blocks = []
        for item in retrievals:
            content = item.get("result", "")
            context_blocks.append(f"[{item['mode']}] {item['query']} -> {content}")
            if content and "[no-context]" not in str(content):
                has_context = True

        if not has_context:
            final_answer = "抱歉，未检索到与问题相关的内容，请确认工作空间是否正确或重新导入文档。"
        else:
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
            "workspace": workspace if workspace is not None else self.current_workspace,
            "collection": workspace if workspace is not None else self.current_workspace,
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
    workspace: str | None = None,
    collection: str | None = None,
    ctx: Context | None = None,
) -> Dict[str, Any]:
    """
    对指定查询执行检索，按请求的模式返回检索结果。

    参数：
    - query：要检索的文本。
    - mode：检索模式（hybrid/dense/sparse 等），默认 hybrid。
    - workspace：目标工作空间（与本地向量库一致）；兼容 collection 作为别名。
    - ctx：MCP 上下文，自动注入。

    返回：
    - 包含 query、mode、workspace 以及底层检索结果的字典。
    """
    service = ctx.request_context.lifespan_context.service
    target_workspace = workspace if workspace is not None else collection
    return await service.retrieve(query, mode=mode, workspace=target_workspace)


@mcp.tool()
async def rag_answer(
    question: str,
    mode: str = "hybrid",
    use_rewrite: bool = True,
    num_variants: int = 3,
    workspace: str | None = None,
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
    - workspace：本地向量库工作空间（兼容 collection）。
    - ctx：MCP 上下文，自动注入。

    返回：
    - question/mode/use_rewrite：本次调用的配置
    - variants：采用的查询变体
    - retrievals：每个查询的检索结果
    - answer：聚合后的回答
    """
    service = ctx.request_context.lifespan_context.service
    target_workspace = workspace if workspace is not None else collection
    return await service.answer(
        question, mode=mode, use_rewrite=use_rewrite, num_variants=num_variants, workspace=target_workspace
    )


@mcp.tool()
async def rag_multi_query_search(
    queries: List[str],
    mode: str = "hybrid",
    workspace: str | None = None,
    collection: str | None = None,
    ctx: Context | None = None,
) -> Dict[str, Any]:
    """
    同时对多条查询执行检索，并返回各自的结果列表。

    参数：
    - queries：查询字符串列表。
    - mode：检索模式，默认 hybrid。
    - workspace：本地向量库工作空间（兼容 collection）。
    - ctx：MCP 上下文，自动注入。

    返回：
    - mode：本次检索的模式
    - results：每条查询对应的检索结果集合
    """
    service = ctx.request_context.lifespan_context.service
    target_workspace = workspace if workspace is not None else collection
    results = await service.multi_retrieve(queries, mode=mode, workspace=target_workspace)
    resolved = target_workspace or service.current_workspace
    return {"mode": mode, "results": results, "workspace": resolved, "collection": resolved}


@mcp.tool()
async def list_collections(ctx: Context | None = None) -> Dict[str, Any]:
    """
    列出可用工作空间（本地向量库扫描结果或 collections.json）。
    便于调用方选择 workspace/collection 再进行检索/回答。
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

    settings = load_settings()
    print("启动 Anything RAG MCP 服务")
    print(f"工作目录: {settings.working_dir}")
    print(
        f"工作空间: {settings.workspace or '(default)'} | 向量存储: {settings.vector_storage}"
    )
    if args.sse:
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        # stdio 模式无需 host/port，避免传参导致 fastmcp 抛出意外参数错误
        mcp.run()


if __name__ == "__main__":
    main()
