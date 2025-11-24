"""
基于 RAG-Anything 的查询示例，演示三类查询：
1) 纯文本多种检索模式
2) VLM 增强（自动/手动开关）
3) 指定多模态内容的查询（表格、公式）

说明：使用本地默认向量库（NanoVectorDBStorage），无需 Milvus。
运行前请在项目根目录准备 .env（DEEPSEEK_API_KEY 等），并确保示例 PDF 存在。

 - 纯文本查询：rag.aquery("Your question", mode=...) 支持 hybrid（向量+KG混合默认）、local（上下文/局部侧重）、global（全局关系侧重）、naive（简单向量检索）。rag.query 是同步封装，便于阻塞场景。
  - VLM 增强查询：当初始化时提供了 vision_model_func，aquery 会在检索到包含图片路径的上下文时，自动读取图片、编码为 base64，并将文本+图像一起发给多模态模型。如果想强制开/关，使用 vlm_enhanced=True/False。
  - 多模态内容查询：aquery_with_multimodal 允许附带结构化模态内容（如表格 type: "table" 或公式 type: "equation"）。这些模态内容会和检索上下文一起提供给模型，提升针对性。


"""

import asyncio
import os
from dotenv import load_dotenv
from raganything import RAGAnything, RAGAnythingConfig
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc


load_dotenv()

# 基础配置
api_key = os.getenv("DEEPSEEK_API_KEY")
base_url = os.getenv("DEEPSEEK_API_BASE")
vl_model_name = os.getenv("IMAGE_PARSER_MODEL")
vl_base_url = os.getenv("IMAGE_PARSER_API_BASE")
vl_api_key = os.getenv("IMAGE_PARSER_API_KEY")
embedding_base_url = os.getenv("EMBEDDING_BASE_URL")
embedding_model = os.getenv("EMBEDDING_MODEL")

# OpenAI 兼容接口通常以 /v1 结尾，避免 404
if embedding_base_url and not embedding_base_url.rstrip("/").endswith("/v1"):
    embedding_base_url = embedding_base_url.rstrip("/") + "/v1"


def build_llm():
    def llm_model_func(prompt, system_prompt=None, history_messages=None, **kwargs):
        return openai_complete_if_cache(
            "deepseek-chat",
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages or [],
            api_key=api_key,
            base_url=base_url,
            **kwargs,
        )

    return llm_model_func


def build_vlm():
    # VLM 封装：当提供 vision_model_func 时，aquery 会自动尝试图片增强
    def vision_model_func(
        prompt, system_prompt=None, history_messages=None, image_data=None, messages=None, **kwargs
    ):
        if messages:
            return openai_complete_if_cache(
                vl_model_name,
                "",
                system_prompt=None,
                history_messages=[],
                messages=messages,
                api_key=vl_api_key,
                base_url=vl_base_url,
                **kwargs,
            )
        if image_data:
            return openai_complete_if_cache(
                vl_model_name,
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
                api_key=vl_api_key,
                base_url=vl_base_url,
                **kwargs,
            )
        return build_llm()(prompt, system_prompt, history_messages or [], **kwargs)

    return vision_model_func


def build_embedding_func():
    return EmbeddingFunc(
        embedding_dim=1024,
        max_token_size=8192,
        func=lambda texts: openai_embed(
            texts,
            model=embedding_model or "qwen3-embedding:0.6b",
            api_key=api_key,
            base_url=embedding_base_url,
        ),
    )


async def main():
    llm_model_func = build_llm()
    vision_model_func = build_vlm()
    embedding_func = build_embedding_func()

    config = RAGAnythingConfig(
        working_dir="./rag_storage",
        parser="docling",
        parse_method="auto",
        enable_image_processing=True,
        enable_table_processing=True,
        enable_equation_processing=True,
    )

    # 使用默认向量库（本地 NanoVectorDBStorage），不传 lightrag_kwargs
    rag = RAGAnything(
        config=config,
        llm_model_func=llm_model_func,
        vision_model_func=vision_model_func,
        embedding_func=embedding_func,
    )

    # 先处理文档，生成知识库
    await rag.process_document_complete(
        file_path="/Users/bytedance/PycharmProjects/my_best/langgraph_teach/src/agentic_rag/pdf_test.pdf",
        output_dir="./output",
        parse_method="auto",
    )

    print("\n=== 1) 纯文本多检索模式 ===")
    text_result_hybrid = await rag.aquery("What are the main findings?", mode="hybrid")
    text_result_local = await rag.aquery("What are the main findings?", mode="local")
    text_result_global = await rag.aquery("What are the main findings?", mode="global")
    text_result_naive = await rag.aquery("What are the main findings?", mode="naive")
    # 同步版本仅适用于非 async 场景；当前在异步函数里会触发事件循环冲突，因此示例中不调用。
    # 如需同步调用，请在顶层脚本中直接使用 rag.query(...)，不要在 asyncio 事件循环中调用。
    print("Hybrid:", text_result_hybrid)
    print("Local:", text_result_local)
    print("Global:", text_result_global)
    print("Naive:", text_result_naive)

    print("\n=== 2) VLM 增强查询 ===")
    vlm_result = await rag.aquery(
        "Analyze the charts and figures in the document",
        mode="hybrid",
    )
    vlm_enabled = await rag.aquery(
        "What do the images show in this document?",
        mode="hybrid",
        vlm_enhanced=True,
    )
    vlm_disabled = await rag.aquery(
        "What do the images show in this document?",
        mode="hybrid",
        vlm_enhanced=False,
    )
    print("Auto VLM:", vlm_result)
    print("VLM Enabled:", vlm_enabled)
    print("VLM Disabled:", vlm_disabled)

    print("\n=== 3) 多模态内容查询 ===")
    table_result = await rag.aquery_with_multimodal(
        "Compare these performance metrics with the document content",
        multimodal_content=[
            {
                "type": "table",
                "table_data": """Method,Accuracy,Speed
                                RAGAnything,95.2%,120ms
                                Traditional,87.3%,180ms""",
                "table_caption": "Performance comparison",
            }
        ],
        mode="hybrid",
    )
    equation_result = await rag.aquery_with_multimodal(
        "Explain this formula and its relevance to the document content",
        multimodal_content=[
            {
                "type": "equation",
                "latex": "P(d|q) = \\frac{P(q|d) \\cdot P(d)}{P(q)}",
                "equation_caption": "Document relevance probability",
            }
        ],
        mode="hybrid",
    )
    print("Table query:", table_result)
    print("Equation query:", equation_result)


if __name__ == "__main__":
    asyncio.run(main())
