"""
🚀 LangGraph SDK Python 基础示例
阶段一：基础连接和简单交互

老王出品，必属精品！
"""

import asyncio
import sys
import os
from typing import Optional

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv未安装，将使用默认环境变量")

# 尝试导入SDK，如果没安装会提示用户
try:
    from langgraph_sdk import get_client, get_sync_client
except ImportError:
    print("❌ 艹！langgraph-sdk没安装！")
    print("请运行: pip install langgraph-sdk")
    sys.exit(1)


class LangGraphBasicClient:
    """LangGraph基础客户端封装类"""

    def __init__(self):
        """从环境变量初始化客户端"""
        self.url = os.getenv("LANGGRAPH_URL", "http://localhost:8123")
        self.api_key = os.getenv("LANGGRAPH_API_KEY")
        self.assistant_id = os.getenv("LANGGRAPH_ASSISTANT_ID", "agent_not_deep")
        self.client = None
        self.sync_client = None

        print(f"🔗 配置信息:")
        print(f"   服务地址: {self.url}")
        print(f"   助手ID: {self.assistant_id}")
        print(f"   API密钥: {'已设置' if self.api_key else '未设置'}")

    async def init_async_client(self):
        """初始化异步客户端"""
        try:
            self.client = get_client(url=self.url, api_key=self.api_key)
            print(f"✅ 异步客户端连接成功: {self.url}")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False

    def init_sync_client(self):
        """初始化同步客户端"""
        try:
            self.sync_client = get_sync_client(url=self.url, api_key=self.api_key)
            print(f"✅ 同步客户端连接成功: {self.url}")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False

    async def test_connection(self):
        """测试连接状态"""
        if not self.client:
            print("❌ 客户端未初始化！")
            return False

        try:
            # 尝试获取助手列表来测试连接
            assistants = await self.client.assistants.search()
            print(f"✅ 连接测试成功！找到 {len(assistants)} 个助手")
            for assistant in assistants:
                print(f"   - {assistant.get('assistant_id', 'Unknown')}: {assistant.get('name', 'No name')}")
            return True
        except Exception as e:
            print(f"❌ 连接测试失败: {e}")
            return False


async def basic_connection_example():
    """基础连接示例"""
    print("=" * 50)
    print("🚀 LangGraph SDK 基础连接示例")
    print("=" * 50)

    # 创建客户端实例
    client = LangGraphBasicClient()

    # 初始化客户端
    if await client.init_async_client():
        # 测试连接
        await client.test_connection()
    else:
        print("❌ 客户端初始化失败！")
        return


async def create_thread_example():
    """创建线程示例"""
    print("\n" + "=" * 50)
    print("🧵 创建线程示例")
    print("=" * 50)

    client = LangGraphBasicClient()

    if not await client.init_async_client():
        return

    try:
        # 创建新线程
        thread = await client.client.threads.create()
        thread_id = thread["thread_id"]
        print(f"✅ 线程创建成功！ID: {thread_id}")

        # 获取线程信息
        thread_info = await client.client.threads.get(thread_id)
        print(f"📋 线程信息: {thread_info}")

        return thread_id
    except Exception as e:
        print(f"❌ 创建线程失败: {e}")
        return None


async def simple_message_example():
    """简单消息示例"""
    print("\n" + "=" * 50)
    print("💬 简单消息示例")
    print("=" * 50)

    client = LangGraphBasicClient()

    if not await client.init_async_client():
        return

    try:
        # 使用配置的助手ID
        print(f"🤖 使用助手: {client.assistant_id}")

        # 创建线程
        thread = await client.client.threads.create()
        thread_id = thread["thread_id"]
        print(f"🧵 创建线程: {thread_id}")

        # 发送消息（无状态运行）
        input_data = {
            "messages": [
                {
                    "role": "user",
                    "content": "你好！请介绍一下LangGraph。"
                }
            ]
        }

        print("📤 发送消息...")
        async for chunk in client.client.runs.stream(
            None,  # 无状态运行
            client.assistant_id,
            input=input_data,
            stream_mode="updates"
        ):
            print(f"📥 事件: {chunk.event}")
            if chunk.event == "updates":
                # 打印AI响应
                data = chunk.data
                if "agent" in data and "messages" in data["agent"]:
                    for msg in data["agent"]["messages"]:
                        if msg.get("type") == "ai":
                            for content in msg.get("content", []):
                                if content.get("type") == "text":
                                    print(f"🤖 AI回复: {content.get('text', '')}")

        print("✅ 消息处理完成！")

    except Exception as e:
        print(f"❌ 消息发送失败: {e}")


async def main():
    """主函数"""
    print("🎯 开始LangGraph SDK基础学习")

    # 1. 基础连接示例
    await basic_connection_example()

    # 2. 创建线程示例
    thread_id = await create_thread_example()

    # 3. 简单消息示例
    await simple_message_example()

    print("\n🎉 基础示例运行完成！")
    print("\n💡 老王的建议:")
    print("   - 确保LangGraph服务正在运行 (langgraph dev)")
    print("   - 检查网络连接和防火墙设置")
    print("   - 遇到错误不要慌，仔细看错误信息")


if __name__ == "__main__":
    print("⚠️  运行前请确保:")
    print("   1. 已安装 langgraph-sdk: pip install langgraph-sdk")
    print("   2. 已安装 python-dotenv: pip install python-dotenv")
    print("   3. LangGraph服务正在运行: docker compose -f docker-compose.langgraph.yml up -d")
    print("   4. 服务地址正确 (默认 http://localhost:8123)")
    print("   5. .env文件配置正确")
    print()

    # 运行主函数
    asyncio.run(main())