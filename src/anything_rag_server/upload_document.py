"""
通过 RAG-Anything 将文档导入指定向量库（Milvus）。
使用 server.py 中的配置读取逻辑，保持参数一致。
"""

import argparse
import asyncio
import sys
import atexit
from pathlib import Path
from typing import Optional

from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
from raganything import RAGAnything, RAGAnythingConfig

# 允许脚本直接运行（未安装包时也能找到 src/anything_rag_server）
PROJECT_SRC = Path(__file__).resolve().parents[1]
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

from anything_rag_server.server import load_settings


def build_rag(
    collection_name: Optional[str] = None,
    enable_image: Optional[bool] = None,
    enable_table: Optional[bool] = None,
    enable_equation: Optional[bool] = None,
):
    settings = load_settings()
    target_collection = collection_name or settings.milvus_collection

    enable_image = settings.enable_image if enable_image is None else enable_image
    enable_table = settings.enable_table if enable_table is None else enable_table
    enable_equation = settings.enable_equation if enable_equation is None else enable_equation

    # 如果未配置 VLM，自动关闭图片解析，避免 text-only 模型调用 image_data 报错
    if enable_image and not settings.vlm_model:
        print("[warn] 未配置 IMAGE_PARSER_MODEL，已自动关闭图片解析（如需开启，请在 .env 设置 IMAGE_PARSER_*）")
        enable_image = False

    embedding_func = EmbeddingFunc(
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

    def vision_model_func(
        prompt,
        system_prompt=None,
        history_messages=None,
        image_data=None,
        messages=None,
        **kwargs,
    ):
        # 优先走多模态消息/图片模型
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
                    {"role": "system", "content": system_prompt} if system_prompt else None,
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

    config = RAGAnythingConfig(
        working_dir=settings.working_dir,
        parser=settings.parser,
        parse_method=settings.parse_method,
        enable_image_processing=enable_image,
        enable_table_processing=enable_table,
        enable_equation_processing=enable_equation,
    )

    return RAGAnything(
        config=config,
        llm_model_func=llm_model_func,
        vision_model_func=vision_model_func,
        embedding_func=embedding_func,
        lightrag_kwargs={
            "vector_storage": "MilvusVectorDBStorage",
            "workspace": target_collection,
        }
        if settings.milvus_uri
        else None,
    )


async def ingest(
    file_path: str,
    output_dir: Optional[str] = None,
    parse_method: Optional[str] = None,
    collection_name: Optional[str] = None,
    enable_image: Optional[bool] = None,
    enable_table: Optional[bool] = None,
    enable_equation: Optional[bool] = None,
):
    rag = build_rag(
        collection_name=collection_name,
        enable_image=enable_image,
        enable_table=enable_table,
        enable_equation=enable_equation,
    )
    try:
        await rag.process_document_complete(
            file_path=file_path,
            output_dir=output_dir or "./output",
            parse_method=parse_method or rag.config.parse_method,
        )
        print(f"✅ 已导入 {file_path} 到集合 {collection_name or '默认集合'}")
    finally:
        # 主线程下提前收尾，避免 atexit 时无事件循环的警告
        try:
            await rag.finalize_storages()
            # 移除在 __post_init__ 中注册的 atexit 关闭钩子，避免重复收尾时缺少事件循环的警告
            try:
                atexit.unregister(rag.close)
            except Exception:
                pass
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] 资源回收失败：{exc}")


def main():
    parser = argparse.ArgumentParser(description="导入文档到 Milvus 向量库")
    parser.add_argument("--file", required=True, help="待导入的文件路径")
    parser.add_argument("--output-dir", default="./output", help="解析输出目录")
    parser.add_argument("--parse-method", default=None, help="覆盖解析方法（auto/ocr/txt）")
    parser.add_argument(
        "--collection",
        default=None,
        help="指定目标集合/表名，默认使用环境变量 MILVUS_COLLECTION_NAME",
    )
    parser.add_argument(
        "--disable-image",
        action="store_true",
        help="禁用图片解析，避免无视觉模型时报错",
    )
    parser.add_argument(
        "--disable-table",
        action="store_true",
        help="禁用表格解析",
    )
    parser.add_argument(
        "--disable-equation",
        action="store_true",
        help="禁用公式解析",
    )
    args = parser.parse_args()

    asyncio.run(
        ingest(
            args.file,
            args.output_dir,
            args.parse_method,
            args.collection,
            enable_image=not args.disable_image if args.disable_image else None,
            enable_table=not args.disable_table if args.disable_table else None,
            enable_equation=not args.disable_equation if args.disable_equation else None,
        )
    )


if __name__ == "__main__":
    main()
