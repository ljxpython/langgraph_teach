import asyncio
import base64
import mimetypes
import sys
from pathlib import Path
from typing import Dict, List

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_rag.engines.file_chat_engine import FileChatEngineFactory
from langchain_core.messages import HumanMessage

# 重新加载环境变量确保使用最新配置
from dotenv import load_dotenv

load_dotenv(".env", override=True)


engine = asyncio.run(FileChatEngineFactory.create_engine())

graph = engine.graph


def file_to_content_block(file_path: Path) -> Dict:
    """将文件转换为LangChain可用的内容块"""
    mime, _ = mimetypes.guess_type(str(file_path))
    if not mime:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            mime = "application/pdf"
        elif suffix in {".png", ".jpg", ".jpeg"}:
            mime = f"image/{suffix.strip('.')}"
        else:
            mime = "application/octet-stream"

    data = file_path.read_bytes()
    b64_data = base64.b64encode(data).decode("utf-8")

    if mime.startswith("image/"):
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime};base64,{b64_data}",
                "metadata": {"name": file_path.name},
            },
        }

    return {
        "type": "file",
        "source_type": "base64",
        "mime_type": mime,
        "data": b64_data,
        "metadata": {"filename": file_path.name},
    }


async def run_self_test():
    """仿照 file_agent，自 src/data 加载资料执行一次完整对话"""
    print("🚀 开始自测 file_rag 管线")
    engine = await FileChatEngineFactory.create_engine()

    data_dir = Path(__file__).resolve().parent.parent / "data"
    if not data_dir.exists():
        print(f"❌ 数据目录不存在: {data_dir}")
        return

    supported_suffixes = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp"}
    content_blocks: List[Dict] = [
        {
            "type": "text",
            "text": "请汇总这些资料的要点，并提取图片中的关键信息。",
        }
    ]

    loaded_files = 0
    for data_file in sorted(data_dir.iterdir()):
        if not data_file.is_file():
            continue
        if data_file.suffix.lower() not in supported_suffixes:
            print(f"ℹ️ 跳过不支持的文件: {data_file.name}")
            continue
        try:
            block = file_to_content_block(data_file)
            content_blocks.append(block)
            loaded_files += 1
            print(f"✅ 已加载文件: {data_file.name}")
        except Exception as exc:
            print(f"⚠️ 加载文件失败 {data_file.name}: {exc}")

    if loaded_files == 0:
        print("❌ 数据目录没有可用的PDF或图片，自测终止")
        return

    message = HumanMessage(content=content_blocks)
    print("🔄 调用引擎处理资料...")
    result = await engine.graph.ainvoke({"messages": [message]})
    ai_response = result["messages"][-1].content
    print("🤖 AI 回复：")
    print(ai_response)


if __name__ == "__main__":
    try:
        asyncio.run(run_self_test())
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断测试")
    except Exception as e:
        print(f"\n💥 自测失败: {e}")
        import traceback

        traceback.print_exc()
