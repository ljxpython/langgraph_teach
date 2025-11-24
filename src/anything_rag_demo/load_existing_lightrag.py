"""
演示如何加载已有的 LightRAG 实例，再交给 RAG-Anything 继续查询/新增文档。
要点：
- 复用已有 working_dir（如果里面已有数据会直接加载）
- 仅使用本地默认向量库（NanoVectorDBStorage），不依赖 Milvus
- 通过 .env 读取 LLM/embedding/VLM 配置
"""

import asyncio
import os
from dotenv import load_dotenv
from raganything import RAGAnything, RAGAnythingConfig
from lightrag import LightRAG
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.utils import EmbeddingFunc


load_dotenv()

# 基础 API 配置（请在 .env 填写实际值）
api_key = os.getenv("DEEPSEEK_API_KEY") or "your-api-key"
base_url = os.getenv("DEEPSEEK_API_BASE")
embedding_model = os.getenv("EMBEDDING_MODEL") or "qwen3-embedding:0.6b"
embedding_base_url = os.getenv("EMBEDDING_BASE_URL")
vl_model_name = os.getenv("IMAGE_PARSER_MODEL")
vl_base_url = os.getenv("IMAGE_PARSER_API_BASE")
vl_api_key = os.getenv("IMAGE_PARSER_API_KEY")

# OpenAI 兼容接口通常以 /v1 结尾，避免 404
if embedding_base_url and not embedding_base_url.rstrip("/").endswith("/v1"):
    embedding_base_url = embedding_base_url.rstrip("/") + "/v1"


async def load_existing_lightrag():
    # 指定已有 LightRAG 工作目录（若为空会自动创建新实例）
    lightrag_working_dir = "./existing_lightrag_storage"
    if os.path.exists(lightrag_working_dir) and os.listdir(lightrag_working_dir):
        print("✅ Found existing LightRAG instance, loading...")
    else:
        print("❌ No existing LightRAG instance found, will create new one")

    # 构造基础 LLM 与 embedding（这里保持简单，本地向量库即可）
    llm_model_func = lambda prompt, system_prompt=None, history_messages=None, **kwargs: openai_complete_if_cache(
        "deepseek-chat",
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages or [],
        api_key=api_key,
        base_url=base_url,
        **kwargs,
    )
    embedding_func = EmbeddingFunc(
        embedding_dim=1024,
        max_token_size=8192,
        func=lambda texts: openai_embed(
            texts,
            model=embedding_model,
            api_key=api_key,
            base_url=embedding_base_url,
        ),
    )

    # 加载/创建 LightRAG；working_dir 内已有的缓存/向量库会被复用
    lightrag_instance = LightRAG(
        working_dir=lightrag_working_dir,
        llm_model_func=llm_model_func,
        embedding_func=embedding_func,
    )
    await lightrag_instance.initialize_storages()
    await initialize_pipeline_status()

    # VLM 封装：提供 vision_model_func 后，RAG 会在需要时自动做图片增强
    def vision_model_func(
        prompt, system_prompt=None, history_messages=None, image_data=None, messages=None, **kwargs
    ):
        if messages:
            return openai_complete_if_cache(
                vl_model_name or "gpt-4o",
                "",
                system_prompt=None,
                history_messages=[],
                messages=messages,
                api_key=vl_api_key or api_key,
                base_url=vl_base_url or base_url,
                **kwargs,
            )
        if image_data:
            return openai_complete_if_cache(
                vl_model_name or "gpt-4o",
                "",
                system_prompt=None,
                history_messages=[],
                messages=[
                    {"role": "system", "content": system_prompt} if system_prompt else None,
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                        ],
                    },
                ],
                api_key=vl_api_key or api_key,
                base_url=vl_base_url or base_url,
                **kwargs,
            )
        return llm_model_func(prompt, system_prompt, history_messages or [], **kwargs)

    # 将已有 LightRAG 交给 RAG-Anything，继续查询/处理
    # 避免 mineru 依赖，显式使用 docling 解析器（纯 Python，开箱即用）
    config = RAGAnythingConfig(
        working_dir="./rag_storage",
        parser="docling",
        parse_method="auto",
        enable_image_processing=True,
        enable_table_processing=True,
        enable_equation_processing=True,
    )

    rag = RAGAnything(
        lightrag=lightrag_instance,  # 复用已有存储与配置
        vision_model_func=vision_model_func,
        config=config,
    )

    # 查询现有知识库
    result = await rag.aquery(
        "What data has been processed in this LightRAG instance?",
        mode="hybrid",
    )
    print("Query result:", result)

    # 向已有实例继续新增文档（示例路径请替换为真实文件）
    await rag.process_document_complete(
        file_path="/Users/bytedance/PycharmProjects/my_best/langgraph_teach/src/agentic_rag/pdf_test.pdf",
        output_dir="./output",
    )


if __name__ == "__main__":
    asyncio.run(load_existing_lightrag())
