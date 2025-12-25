"""
🚀 LangGraph SDK 高级功能示例
阶段三：并发处理、状态管理、人工干预

老王出品，必属精品！
"""

import asyncio
import json
import time
import os
from typing import Dict, List, Optional, Any, Callable
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


class ConcurrencyManager:
    """并发管理器 - 处理多任务和并发场景"""

    def __init__(self, client):
        self.client = client

    async def batch_runs(self, assistant_id: str, tasks: List[Dict],
                        multitask_strategy: str = "reject") -> List[Dict]:
        """
        批量运行任务

        Args:
            assistant_id: 助手ID
            tasks: 任务列表，每个任务包含input_data
            multitask_strategy: 多任务策略

        Returns:
            运行结果列表
        """
        print(f"🚀 开始批量运行 {len(tasks)} 个任务")

        results = []
        threads = []

        # 为每个任务创建线程
        for i, task in enumerate(tasks):
            try:
                thread = await self.client.threads.create(
                    metadata={"batch_id": f"batch_{int(time.time())}", "task_index": i}
                )
                threads.append(thread)
                print(f"🧵 创建线程 {i+1}: {thread['thread_id']}")
            except Exception as e:
                print(f"❌ 创建线程 {i+1} 失败: {e}")
                threads.append(None)

        # 并发执行任务
        semaphore = asyncio.Semaphore(3)  # 限制并发数

        async def run_task(task_index: int, thread: Dict, task_data: Dict):
            async with semaphore:
                if not thread:
                    return {"task_index": task_index, "error": "Thread creation failed"}

                try:
                    start_time = time.time()

                    # 修复：LangGraph SDK的wait方法不支持timeout参数
                    # 使用asyncio.wait_for包装
                    async def run_without_timeout():
                        return await self.client.runs.wait(
                            thread_id=thread['thread_id'],
                            assistant_id=assistant_id,
                            input=task_data['input']
                        )

                    # 设置60秒超时
                    result = await asyncio.wait_for(run_without_timeout(), timeout=60)

                    duration = time.time() - start_time

                    return {
                        "task_index": task_index,
                        "thread_id": thread['thread_id'],
                        "duration": duration,
                        "result": result,
                        "success": True
                    }
                except asyncio.TimeoutError:
                    return {
                        "task_index": task_index,
                        "thread_id": thread.get('thread_id') if thread else None,
                        "error": "Task timeout (60s)",
                        "success": False
                    }
                except Exception as e:
                    return {
                        "task_index": task_index,
                        "thread_id": thread.get('thread_id') if thread else None,
                        "error": str(e),
                        "success": False
                    }

        # 执行所有任务
        start_time = time.time()
        tasks_to_run = [
            run_task(i, thread, task)
            for i, (thread, task) in enumerate(zip(threads, tasks))
        ]

        results = await asyncio.gather(*tasks_to_run, return_exceptions=True)
        total_duration = time.time() - start_time

        # 统计结果
        successful = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        failed = len(results) - successful

        print(f"✅ 批量运行完成！")
        print(f"   成功: {successful}, 失败: {failed}")
        print(f"   总耗时: {total_duration:.2f}秒")

        return results

    async def interrupt_running_task(self, thread_id: str, new_task: Dict):
        """
        中断正在运行的任务并启动新任务

        Args:
            thread_id: 线程ID
            new_task: 新任务数据
        """
        try:
            print(f"🛑 中断线程 {thread_id} 的当前任务")

            # 创建中断策略的新运行，使用配置的助手ID
            assistant_id = new_task.get('assistant_id', LANGGRAPH_ASSISTANT_ID)

            run = await self.client.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
                input=new_task['input'],
                multitask_strategy="interrupt"  # 中断策略
            )

            print(f"✅ 新任务已启动，将中断当前任务: {run['run_id']}")
            return run

        except Exception as e:
            print(f"❌ 任务中断失败: {e}")
            raise


class StateManager:
    """状态管理器 - 管理检查点和状态恢复"""

    def __init__(self, client):
        self.client = client

    async def save_checkpoint(self, thread_id: str, checkpoint_data: Dict):
        """保存检查点"""
        try:
            # 通过更新线程元数据保存检查点
            metadata = {
                "checkpoint": checkpoint_data,
                "checkpoint_time": datetime.now().isoformat(),
                "checkpoint_version": "1.0"
            }

            await self.client.threads.update(thread_id, metadata=metadata)
            print(f"💾 检查点保存成功: {thread_id}")
            return True

        except Exception as e:
            print(f"❌ 保存检查点失败: {e}")
            return False

    async def load_checkpoint(self, thread_id: str) -> Optional[Dict]:
        """加载检查点"""
        try:
            thread_info = await self.client.threads.get(thread_id)
            metadata = thread_info.get('metadata', {})
            checkpoint = metadata.get('checkpoint')

            if checkpoint:
                print(f"📂 检查点加载成功: {thread_id}")
                return checkpoint
            else:
                print(f"⚠️ 未找到检查点: {thread_id}")
                return None

        except Exception as e:
            print(f"❌ 加载检查点失败: {e}")
            return None

    async def list_checkpoints(self, thread_id: str) -> List[Dict]:
        """列出所有检查点（通过线程历史）"""
        try:
            # 获取线程的运行历史
            runs = await self.client.runs.list(thread_id)
            checkpoints = []

            for run in runs:
                if run.get('metadata', {}).get('checkpoint'):
                    checkpoints.append({
                        'run_id': run['run_id'],
                        'created_at': run['created_at'],
                        'checkpoint': run['metadata']['checkpoint']
                    })

            print(f"📋 找到 {len(checkpoints)} 个检查点")
            return checkpoints

        except Exception as e:
            print(f"❌ 列出检查点失败: {e}")
            return []

    async def restore_from_checkpoint(self, thread_id: str, checkpoint_index: int = -1):
        """从检查点恢复"""
        try:
            checkpoints = await self.list_checkpoints(thread_id)
            if not checkpoints:
                print("❌ 没有可用的检查点")
                return False

            if abs(checkpoint_index) > len(checkpoints):
                print("❌ 检查点索引超出范围")
                return False

            checkpoint = checkpoints[checkpoint_index]
            print(f"🔄 从检查点恢复: {checkpoint['run_id']}")

            # 这里可以根据检查点数据恢复状态
            # 实际实现取决于具体的应用场景
            return True

        except Exception as e:
            print(f"❌ 恢复检查点失败: {e}")
            return False


class HumanInTheLoopManager:
    """人工干预管理器"""

    def __init__(self, client):
        self.client = client
        self.pending_approvals = {}

    async def create_interrupted_run(self, thread_id: str, assistant_id: str,
                                   input_data: Dict, interrupt_after: List[str] = None):
        """创建可中断的运行"""
        try:
            print(f"🛑 创建可中断运行，将在指定节点后暂停")

            run = await self.client.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
                input=input_data,
                interrupt_after=interrupt_after or ["human_review"]
            )

            # 记录等待人工干预的任务
            self.pending_approvals[run['run_id']] = {
                'thread_id': thread_id,
                'assistant_id': assistant_id,
                'created_at': datetime.now().isoformat(),
                'status': 'pending_approval'
            }

            print(f"✅ 可中断运行创建成功: {run['run_id']}")
            return run

        except Exception as e:
            print(f"❌ 创建可中断运行失败: {e}")
            raise

    async def approve_and_continue(self, thread_id: str, run_id: str,
                                 approval_data: Dict = None):
        """批准并继续运行"""
        try:
            if run_id not in self.pending_approvals:
                print(f"❌ 未找到等待批准的运行: {run_id}")
                return False

            print(f"✅ 批准运行继续: {run_id}")

            # 更新批准状态
            self.pending_approvals[run_id]['status'] = 'approved'
            self.pending_approvals[run_id]['approved_at'] = datetime.now().isoformat()
            self.pending_approvals[run_id]['approval_data'] = approval_data

            # 这里应该调用相应的API来继续运行
            # 具体实现取决于LangGraph的具体API
            return True

        except Exception as e:
            print(f"❌ 批准继续失败: {e}")
            return False

    async def reject_and_rollback(self, thread_id: str, run_id: str,
                                 reason: str = "Rejected by human"):
        """拒绝并回滚"""
        try:
            if run_id not in self.pending_approvals:
                print(f"❌ 未找到等待批准的运行: {run_id}")
                return False

            print(f"❌ 拒绝运行，执行回滚: {run_id} - {reason}")

            # 更新拒绝状态
            self.pending_approvals[run_id]['status'] = 'rejected'
            self.pending_approvals[run_id]['rejected_at'] = datetime.now().isoformat()
            self.pending_approvals[run_id]['rejection_reason'] = reason

            # 这里应该调用相应的API来回滚运行
            # 具体实现取决于LangGraph的具体API
            return True

        except Exception as e:
            print(f"❌ 回滚失败: {e}")
            return False

    async def list_pending_approvals(self) -> List[Dict]:
        """列出等待批准的任务"""
        pending = [
            {**info, 'run_id': run_id}
            for run_id, info in self.pending_approvals.items()
            if info['status'] == 'pending_approval'
        ]

        print(f"📋 待批准任务: {len(pending)}")
        for task in pending:
            print(f"   - {task['run_id']}: {task['created_at']}")

        return pending


async def concurrency_demo():
    """并发处理演示"""
    print("=" * 60)
    print("🚀 并发处理演示")
    print("=" * 60)

    client = get_client(url=LANGGRAPH_URL, api_key=LANGGRAPH_API_KEY)
    concurrency_manager = ConcurrencyManager(client)

    try:
        # 准备批量任务
        tasks = [
            {
                "input": {
                    "messages": [
                        {"role": "user", "content": f"请解释Python中的第{i+1}个重要概念"}
                    ]
                }
            }
            for i in range(5)
        ]

        # 执行批量运行，使用配置的助手ID
        results = await concurrency_manager.batch_runs(
            assistant_id=LANGGRAPH_ASSISTANT_ID,
            tasks=tasks
        )

        # 显示结果
        print("\n📊 批量运行结果:")
        for result in results:
            if isinstance(result, dict):
                if result.get('success'):
                    print(f"   ✅ 任务 {result['task_index']+1}: {result['duration']:.2f}秒")
                else:
                    print(f"   ❌ 任务 {result['task_index']+1}: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ 并发演示失败: {e}")


async def state_management_demo():
    """状态管理演示"""
    print("\n" + "=" * 60)
    print("💾 状态管理演示")
    print("=" * 60)

    client = get_client(url=LANGGRAPH_URL, api_key=LANGGRAPH_API_KEY)
    state_manager = StateManager(client)

    try:
        # 创建测试线程
        thread = await client.threads.create(
            metadata={"demo_type": "state_management"}
        )
        thread_id = thread['thread_id']
        print(f"🧵 创建测试线程: {thread_id}")

        # 保存检查点
        checkpoint_data = {
            "user_preferences": {"language": "zh-CN", "style": "formal"},
            "conversation_context": {"topic": "LangGraph学习", "level": "advanced"},
            "progress": {"completed_lessons": 5, "current_lesson": 6}
        }

        await state_manager.save_checkpoint(thread_id, checkpoint_data)

        # 加载检查点
        loaded_checkpoint = await state_manager.load_checkpoint(thread_id)
        if loaded_checkpoint:
            print(f"📂 加载的检查点数据: {json.dumps(loaded_checkpoint, indent=2, ensure_ascii=False)}")

    except Exception as e:
        print(f"❌ 状态管理演示失败: {e}")


async def human_in_the_loop_demo():
    """人工干预演示"""
    print("\n" + "=" * 60)
    print("👥 人工干预演示")
    print("=" * 60)

    client = get_client(url=LANGGRAPH_URL, api_key=LANGGRAPH_API_KEY)
    htl_manager = HumanInTheLoopManager(client)

    try:
        # 创建测试线程
        thread = await client.threads.create(
            metadata={"demo_type": "human_in_the_loop"}
        )
        thread_id = thread['thread_id']
        print(f"🧵 创建测试线程: {thread_id}")

        # 创建需要人工干预的运行
        input_data = {
            "messages": [
                {"role": "user", "content": "请帮我生成一个复杂的AI项目计划"}
            ]
        }

        # 注意：这里假设agent支持interrupt_after功能
        # 实际使用时需要根据具体的agent配置调整
        run = await htl_manager.create_interrupted_run(
            thread_id=thread_id,
            assistant_id=LANGGRAPH_ASSISTANT_ID,
            input_data=input_data,
            interrupt_after=["planning", "review"]
        )

        # 查看待批准任务
        await htl_manager.list_pending_approvals()

        # 模拟人工批准
        if run['run_id'] in htl_manager.pending_approvals:
            approval_data = {
                "approved_by": "老王",
                "comments": "计划看起来不错，继续执行",
                "modifications": {"timeline": "2 weeks", "budget": "moderate"}
            }

            await htl_manager.approve_and_continue(
                thread_id=thread_id,
                run_id=run['run_id'],
                approval_data=approval_data
            )

    except Exception as e:
        print(f"❌ 人工干预演示失败: {e}")
        print("💡 注意：这个演示需要agent支持interrupt功能")


async def main():
    """主演示函数"""
    print("🎯 LangGraph SDK 高级功能学习")
    print("📚 包含：并发处理、状态管理、人工干预")
    print("👨‍🏫 老王高级教学")

    try:
        print(f"🔧 使用配置:")
        print(f"   服务地址: {LANGGRAPH_URL}")
        print(f"   助手ID: {LANGGRAPH_ASSISTANT_ID}")

        # 1. 并发处理演示
        await concurrency_demo()

        # 2. 状态管理演示
        await state_management_demo()

        # 3. 人工干预演示
        await human_in_the_loop_demo()

        print("\n🎉 高级功能演示完成！")
        print("\n💡 老王的总结:")
        print("   - 并发处理：批量任务、性能优化、资源管理")
        print("   - 状态管理：检查点、状态恢复、时间旅行")
        print("   - 人工干预：审批流程、质量控制、回滚机制")
        print("   - 这些功能让你构建生产级AI应用！")

    except Exception as e:
        print(f"❌ 演示运行失败: {e}")
        print("\n💡 可能的解决方案:")
        print("   1. 检查服务是否运行: docker compose -f docker-compose.langgraph.yml up -d")
        print("   2. 确认端口:", LANGGRAPH_URL)
        print("   3. 检查助手:", LANGGRAPH_ASSISTANT_ID)
        print("   4. 确认网络连接")
        print("   5. 确认.env文件配置正确")


if __name__ == "__main__":
    print("⚠️  运行前准备:")
    print("   1. 启动项目服务: docker compose -f docker-compose.langgraph.yml up -d")
    print("   2. 确认服务可访问:", LANGGRAPH_URL)
    print("   3. 确认助手可用:", LANGGRAPH_ASSISTANT_ID)
    print("   4. 安装SDK: pip install langgraph-sdk python-dotenv")
    print("   5. 确认.env文件存在并配置正确")
    print()

    asyncio.run(main())