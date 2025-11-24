import asyncio
from raganything import RAGAnything, RAGAnythingConfig
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
import os
from dotenv import load_dotenv


load_dotenv()

# Set up API configuration
api_key = os.getenv("DEEPSEEK_API_KEY")
base_url = os.getenv("DEEPSEEK_API_BASE")  # Optional
vl_model_name = os.getenv("IMAGE_PARSER_MODEL")
vl_base_url = os.getenv("IMAGE_PARSER_API_BASE")
vl_api_key = os.getenv("IMAGE_PARSER_API_KEY")
embedding_base_url = os.getenv("EMBEDDING_BASE_URL")
embedding_model = os.getenv("EMBEDDING_MODEL")
milvus_uri = os.getenv("MILVUS_URI")
milvus_collection_name = os.getenv("MILVUS_COLLECTION_NAME", "knowledge_base")
if embedding_base_url and not embedding_base_url.rstrip("/").endswith("/v1"):
    # OpenAI 兼容接口通常以 /v1 结尾，避免 404
    embedding_base_url = embedding_base_url.rstrip("/") + "/v1"


async def main():
    if not milvus_uri:
        raise RuntimeError("缺少 MILVUS_URI 环境变量，无法初始化 Milvus 向量库")

    # Milvus 相关配置传给 LightRAG，workspace 用于作为集合名前缀
    lightrag_milvus_kwargs = {
        "vector_storage": "MilvusVectorDBStorage",
        "workspace": milvus_collection_name,
    }

    # Create RAGAnything configuration
    config = RAGAnythingConfig(
        working_dir="./rag_storage",
        parser="docling",  # Parser selection: mineru or docling
        parse_method="auto",  # Parse method: auto, ocr, or txt
        enable_image_processing=True,
        enable_table_processing=True,
        enable_equation_processing=True,
    )

    # Define LLM model function
    def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
        return openai_complete_if_cache(
            "deepseek-chat",
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            api_key=api_key,
            base_url=base_url,
            **kwargs,
        )

    # Define vision model function for image processing
    def vision_model_func(
        prompt, system_prompt=None, history_messages=[], image_data=None, messages=None, **kwargs
    ):
        # If messages format is provided (for multimodal VLM enhanced query), use it directly
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
        # Traditional single image format
        elif image_data:
            return openai_complete_if_cache(
                vl_model_name,
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
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                },
                            },
                        ],
                    }
                    if image_data
                    else {"role": "user", "content": prompt},
                ],
                api_key=vl_api_key,
                base_url=vl_base_url,
                **kwargs,
            )
        # Pure text format
        else:
            return llm_model_func(prompt, system_prompt, history_messages, **kwargs)

    # Define embedding function
    embedding_func = EmbeddingFunc(
        embedding_dim=1024,
        max_token_size=8192,
        func=lambda texts: openai_embed(
            texts,
            model="qwen3-embedding:0.6b",
            # api_key=os.getenv("EMBEDDING_API_KEY") or api_key,
            api_key='test',
            base_url=embedding_base_url,
        ),
    )

    # Initialize RAGAnything
    rag = RAGAnything(
        config=config,
        llm_model_func=llm_model_func,
        vision_model_func=vision_model_func,
        embedding_func=embedding_func,
        lightrag_kwargs=lightrag_milvus_kwargs,
    )

    # Process a document
    await rag.process_document_complete(
        file_path="/Users/bytedance/PycharmProjects/my_best/langgraph_teach/src/agentic_rag/pdf_test.pdf",
        output_dir="./output",
        parse_method="auto"
    )

    # Query the processed content
    # Pure text query - for basic knowledge base search
    text_result = await rag.aquery(
        "What are the main findings shown in the figures and tables?",
        mode="hybrid"
    )
    print("Text query result:", text_result)

    # Multimodal query with specific multimodal content
    multimodal_result = await rag.aquery_with_multimodal(
    "Explain this formula and its relevance to the document content",
    multimodal_content=[{
        "type": "equation",
        "latex": "P(d|q) = \\frac{P(q|d) \\cdot P(d)}{P(q)}",
        "equation_caption": "Document relevance probability"
    }],
    mode="hybrid"
)
    print("Multimodal query result:", multimodal_result)

if __name__ == "__main__":
    asyncio.run(main())
