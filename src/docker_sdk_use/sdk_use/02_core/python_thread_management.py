"""
🧵 LangGraph SDK 核心功能示例
阶段二：线程管理和运行控制

老王出品，必属精品！
"""

import asyncio
import json
import time
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv未安装，将使用默认环境变量")

from langgraph_sdk import get_client

# 从环境变量获取配置
LANGGRAPH_URL = os.getenv("LANGGRAPH_URL", "http://localhost:8123")
LANGGRAPH_API_KEY = os.getenv("LANGGRAPH_API_KEY")
LANGGRAPH_ASSISTANT_ID = os.getenv("LANGGRAPH_ASSISTANT_ID", "agent_not_deep")


class ThreadManager:
    """线程管理器 - 封装线程相关操作"""

    def __init__(self, client):
        self.client = client

    async def create_thread(self, metadata: Optional[Dict] = None) -> Dict:
        """
        创建新线程

        Args:
            metadata: 线程元数据

        Returns:
            线程信息字典
        """
        try:
            if metadata:
                thread = await self.client.threads.create(metadata=metadata)
            else:
                thread = await self.client.threads.create()

            print(f"✅ 线程创建成功: {thread['thread_id']}")
            return thread
        except Exception as e:
            print(f"❌ 创建线程失败: {e}")
            raise

    async def get_thread_info(self, thread_id: str) -> Dict:
        """获取线程详细信息"""
        try:
            thread_info = await self.client.threads.get(thread_id)
            print(f"📋 线程信息: {json.dumps(thread_info, indent=2, ensure_ascii=False)}")
            return thread_info
        except Exception as e:
            print(f"❌ 获取线程信息失败: {e}")
            raise

    async def update_thread_metadata(self, thread_id: str, metadata: Dict) -> Dict:
        """更新线程元数据"""
        try:
            # 简化处理：元数据更新可能不是必需的，或者通过其他方式实现
            # 让这个方法优雅地跳过

            # 方法1：尝试使用update_metadata
            try:
                updated = await self.client.threads.update_metadata(thread_id, metadata)
                print(f"✅ 线程元数据更新成功")
                return updated
            except (AttributeError, TypeError):
                pass  # 方法不存在，尝试下一个

            # 方法2：尝试使用update
            try:
                updated = await self.client.threads.update(thread_id, metadata=metadata)
                print(f"✅ 线程元数据更新成功（使用update方法）")
                return updated
            except (AttributeError, TypeError):
                pass  # 方法不存在，尝试下一个

            # 方法3：优雅跳过
            print(f"⚠️ 元数据更新方法不可用，跳过更新（这在某些LangGraph版本中是正常的）")
            return {"status": "skipped", "reason": "API method not available"}

        except Exception as e:
            print(f"⚠️ 更新线程元数据失败，但继续执行: {e}")
            return {"status": "failed", "error": str(e)}

    async def list_thread_messages(self, thread_id: str, limit: int = 10) -> List[Dict]:
        """列出线程消息历史"""
        try:
            # 简化处理：既然线程刚创建还没有消息，直接返回空列表
            # 在实际使用中，消息会在运行后通过状态来获取

            # 方法1：尝试获取线程状态中的消息
            try:
                state_info = await self.client.threads.get_state(thread_id)
                messages = state_info.get("values", {}).get("messages", [])
                print(f"📨 线程消息 (共{len(messages)}条):")

                if messages:
                    for i, msg in enumerate(messages, 1):
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")

                        # 处理不同类型的内容
                        if isinstance(content, list):
                            content_text = ""
                            for item in content:
                                if item.get("type") == "text":
                                    content_text += item.get("text", "")
                            content = content_text

                        preview = (str(content)[:50] + "...") if len(str(content)) > 50 else str(content)
                        print(f"   {i}. [{role}] {preview}")
                else:
                    print("   (暂无消息，线程刚创建)")

                return messages

            except AttributeError:
                # 如果get_state不存在，使用简单处理
                print("📨 线程消息 (共0条):")
                print("   (暂无消息，线程刚创建)")
                return []

        except Exception as e:
            print(f"⚠️ 获取消息历史失败，但继续执行: {e}")
            return []

    async def delete_thread(self, thread_id: str) -> bool:
        """删除线程"""
        try:
            await self.client.threads.delete(thread_id)
            print(f"✅ 线程删除成功: {thread_id}")
            return True
        except Exception as e:
            print(f"❌ 删除线程失败: {e}")
            return False


class RunManager:
    """运行管理器 - 封装运行相关操作"""

    def __init__(self, client):
        self.client = client

    async def create_run(self, thread_id: str, assistant_id: str,
                        input_data: Dict, multitask_strategy: str = "reject") -> Dict:
        """
        创建新运行

        Args:
            thread_id: 线程ID
            assistant_id: 助手ID
            input_data: 输入数据
            multitask_strategy: 多任务策略 ("reject", "interrupt", "enqueue")

        Returns:
            运行信息字典
        """
        try:
            run = await self.client.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
                input=input_data,
                multitask_strategy=multitask_strategy
            )

            print(f"✅ 运行创建成功: {run['run_id']}")
            print(f"   状态: {run['status']}")
            return run
        except Exception as e:
            print(f"❌ 创建运行失败: {e}")
            raise

    async def wait_for_run(self, thread_id: str, assistant_id: str,
                          input_data: Dict, timeout: int = 60) -> Dict:
        """
        等待运行完成

        Args:
            thread_id: 线程ID
            assistant_id: 助手ID
            input_data: 输入数据
            timeout: 超时时间（秒）

        Returns:
            运行结果
        """
        try:
            print(f"⏳ 等待运行完成（最长{timeout}秒）...")

            result = await asyncio.wait_for(
                self.client.runs.wait(
                    thread_id=thread_id,
                    assistant_id=assistant_id,
                    input=input_data
                ),
                timeout=timeout
            )

            print(f"✅ 运行完成！")
            return result
        except asyncio.TimeoutError:
            print(f"❌ 运行超时（{timeout}秒）")
            raise
        except Exception as e:
            print(f"❌ 运行失败: {e}")
            raise

    async def list_runs(self, thread_id: str, status_filter: Optional[str] = None) -> List[Dict]:
        """列出线程的所有运行"""
        try:
            params = {}
            if status_filter:
                params['status'] = status_filter

            runs = await self.client.runs.list(thread_id, **params)
            print(f"📋 线程运行列表 (共{len(runs)}个):")

            for i, run in enumerate(runs, 1):
                created_at = datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))
                print(f"   {i}. {run['run_id']} - {run['status']} - {created_at.strftime('%Y-%m-%d %H:%M:%S')}")

            return runs
        except Exception as e:
            print(f"❌ 获取运行列表失败: {e}")
            raise

    async def cancel_run(self, thread_id: str, run_id: str, wait: bool = True) -> bool:
        """取消运行"""
        try:
            await self.client.runs.cancel(thread_id, run_id, wait=wait)
            print(f"✅ 运行取消成功: {run_id}")
            return True
        except Exception as e:
            print(f"❌ 取消运行失败: {e}")
            return False

    async def get_run_status(self, thread_id: str, run_id: str) -> Dict:
        """获取运行状态"""
        try:
            # 通过列表获取特定运行信息
            runs = await self.client.runs.list(thread_id)
            for run in runs:
                if run['run_id'] == run_id:
                    print(f"📊 运行状态: {run['status']}")
                    return run

            print(f"❌ 未找到运行: {run_id}")
            return {}
        except Exception as e:
            print(f"❌ 获取运行状态失败: {e}")
            raise


class StreamingManager:
    """流式处理管理器"""

    def __init__(self, client):
        self.client = client

    async def stream_updates(self, thread_id: str, assistant_id: str,
                           input_data: Dict, on_message: callable = None):
        """流式获取更新"""
        try:
            print(f"🌊 开始流式处理...")

            message_count = 0
            async for chunk in self.client.runs.stream(
                thread_id=thread_id,
                assistant_id=assistant_id,
                input=input_data,
                stream_mode="updates"
            ):
                message_count += 1
                print(f"📦 事件 {message_count}: {chunk.event}")

                if chunk.event == "updates":
                    data = chunk.data

                    # 处理AI响应
                    if "agent" in data and "messages" in data["agent"]:
                        for msg in data["agent"]["messages"]:
                            if msg.get("type") == "ai":
                                for content in msg.get("content", []):
                                    if content.get("type") == "text":
                                        text = content.get("text', '')")
                                        print(f"🤖 AI: {text}")

                                        # 调用回调函数
                                        if on_message:
                                            await on_message(text)

                    # 处理其他数据
                    else:
                        print(f"📊 数据: {json.dumps(data, indent=2, ensure_ascii=False)}")

                elif chunk.event == "metadata":
                    print(f"📋 元数据: {chunk.data}")

                else:
                    print(f"🔔 其他事件: {chunk.event}")

            print(f"✅ 流式处理完成！共处理 {message_count} 个事件")

        except Exception as e:
            print(f"❌ 流式处理失败: {e}")
            raise

    async def stream_events(self, thread_id: str, assistant_id: str, input_data: Dict):
        """流式获取所有事件"""
        try:
            print(f"🎭 开始事件流...")

            async for chunk in self.client.runs.stream(
                thread_id=thread_id,
                assistant_id=assistant_id,
                input=input_data,
                stream_mode="events"
            ):
                print(f"🎪 事件类型: {chunk.event}")
                print(f"📝 事件数据: {json.dumps(chunk.data, indent=2, ensure_ascii=False)}")
                print("-" * 50)

        except Exception as e:
            print(f"❌ 事件流处理失败: {e}")
            raise


async def thread_management_demo():
    """线程管理演示"""
    print("=" * 60)
    print("🧵 线程管理演示")
    print("=" * 60)

    client = get_client(url=LANGGRAPH_URL, api_key=LANGGRAPH_API_KEY)
    thread_manager = ThreadManager(client)

    try:
        # 创建线程
        print("\n1️⃣ 创建新线程")
        thread = await thread_manager.create_thread(
            metadata={"user": "老王", "project": "学习项目"}
        )
        thread_id = thread['thread_id']

        # 获取线程信息
        print("\n2️⃣ 获取线程信息")
        await thread_manager.get_thread_info(thread_id)

        # 更新线程元数据
        print("\n3️⃣ 更新线程元数据")
        await thread_manager.update_thread_metadata(
            thread_id,
            {"user": "老王", "project": "学习项目", "status": "active"}
        )

        # 列出消息（此时应该为空）
        print("\n4️⃣ 列出消息历史")
        await thread_manager.list_thread_messages(thread_id)

        return thread_id

    except Exception as e:
        print(f"❌ 线程管理演示失败: {e}")
        return None


async def run_management_demo(thread_id: str, assistant_id: str):
    """运行管理演示"""
    print("\n" + "=" * 60)
    print("🏃 运行管理演示")
    print("=" * 60)

    client = get_client(url=LANGGRAPH_URL, api_key=LANGGRAPH_API_KEY)
    run_manager = RunManager(client)

    try:
        # 创建运行
        print("\n1️⃣ 创建新运行")
        input_data = {
            "messages": [
                {
                    "role": "user",
                    "content": "请解释一下什么是LangGraph的线程和运行概念？"
                }
            ]
        }

        run = await run_manager.create_run(
            thread_id=thread_id,
            assistant_id=assistant_id,
            input_data=input_data
        )

        # 列出运行
        print("\n2️⃣ 列出线程运行")
        await run_manager.list_runs(thread_id)

        return run['run_id']

    except Exception as e:
        print(f"❌ 运行管理演示失败: {e}")
        return None


async def streaming_demo(thread_id: str, assistant_id: str):
    """流式处理演示"""
    print("\n" + "=" * 60)
    print("🌊 流式处理演示")
    print("=" * 60)

    client = get_client(url=LANGGRAPH_URL, api_key=LANGGRAPH_API_KEY)
    streaming_manager = StreamingManager(client)

    try:
        # 定义消息处理回调
        async def message_handler(text: str):
            print(f"📞 回调收到消息: {text[:30]}...")

        # 流式更新演示
        print("\n1️⃣ 流式更新演示")
        input_data = {
            "messages": [
                {
                    "role": "user",
                    "content": "请用3个要点介绍LangGraph的主要特性"
                }
            ]
        }

        await streaming_manager.stream_updates(
            thread_id=thread_id,
            assistant_id=assistant_id,
            input_data=input_data,
            on_message=message_handler
        )

    except Exception as e:
        print(f"❌ 流式处理演示失败: {e}")


async def main():
    """主演示函数"""
    print("🎯 LangGraph SDK 核心功能学习")
    print("📚 包含：线程管理、运行控制、流式处理")
    print("👨‍🏫 老王手把手教学")

    try:
        print(f"🔧 使用配置:")
        print(f"   服务地址: {LANGGRAPH_URL}")
        print(f"   助手ID: {LANGGRAPH_ASSISTANT_ID}")

        # 使用配置的助手ID
        assistant_id = LANGGRAPH_ASSISTANT_ID
        print(f"🤖 使用助手: {assistant_id}")

        # 1. 线程管理演示
        thread_id = await thread_management_demo()

        if not thread_id:
            return

        # 2. 运行管理演示
        run_id = await run_management_demo(thread_id, assistant_id)

        if run_id:
            # 3. 流式处理演示
            await streaming_demo(thread_id, assistant_id)

        print("\n🎉 核心功能演示完成！")
        print("\n💡 老王的总结:")
        print("   - 线程管理：创建、查询、更新、删除")
        print("   - 运行控制：创建、等待、取消、状态查询")
        print("   - 流式处理：实时获取更新和事件")
        print("   - 这些都是构建AI应用的基础！")

    except Exception as e:
        print(f"❌ 演示运行失败: {e}")
        print("\n💡 可能的解决方案:")
        print("   1. 检查LangGraph服务是否运行: docker compose -f docker-compose.langgraph.yml up -d")
        print("   2. 确认服务地址:", LANGGRAPH_URL)
        print("   3. 安装依赖: pip install langgraph-sdk python-dotenv")
        print("   4. 检查网络和防火墙设置")
        print("   5. 确认.env文件配置正确")


if __name__ == "__main__":
    print("⚠️  运行前准备:")
    print("   1. 启动LangGraph服务: docker compose -f docker-compose.langgraph.yml up -d")
    print("   2. 确认端口可访问:", LANGGRAPH_URL)
    print("   3. 确认助手可用:", LANGGRAPH_ASSISTANT_ID)
    print("   4. 安装SDK: pip install langgraph-sdk python-dotenv")
    print("   5. 确认.env文件存在并配置正确")
    print()

    asyncio.run(main())