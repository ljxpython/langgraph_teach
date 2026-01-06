"""
SubAgent 和 Backend 本质的实战示例

这个文件通过实际代码演示：
1. SubAgent 是如何通过 create_agent 创建的
2. Backend 抽象层的价值和可插拔性
"""
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.agents.middleware.subagents import SubAgentMiddleware
from langchain.tools import BaseTool, ToolRuntime
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from deepagents2 import create_deep_agent
from deepagents2.backends.composite import CompositeBackend
from deepagents2.backends.state import StateBackend
from deepagents2.backends.store import StoreBackend
from deepagents2.middleware.filesystem import FilesystemMiddleware


# ============================================================================
# 示例 1: SubAgent 的本质 - 通过 create_agent 创建
# ============================================================================

def example_1_subagent_essence():
    """演示 SubAgent 是如何通过 create_agent 创建的"""
    
    print("=" * 80)
    print("示例 1: SubAgent 的本质")
    print("=" * 80)
    
    # 步骤 1: 定义 SubAgent 配置（只是一个字典）
    code_reviewer = {
        "name": "code-reviewer",
        "description": "专门审查代码质量、风格和潜在问题的专家",
        "system_prompt": "你是一个代码审查专家。仔细检查代码的质量、风格、性能和安全问题。",
        "tools": [],  # 可以有自己的工具
    }
    
    print("\n1️⃣ SubAgent 配置（只是字典）:")
    print(f"   类型: {type(code_reviewer)}")
    print(f"   内容: {code_reviewer}")
    
    # 步骤 2: 模拟 SubAgentMiddleware 内部的 _get_subagents 函数
    # 这就是 SubAgent 配置被转换为真正 Agent 的地方
    print("\n2️⃣ 通过 create_agent 创建真正的 Agent:")
    
    # 这就是框架内部做的事情！
    actual_agent = create_agent(
        model="openai:gpt-4o-mini",  # 或者从配置中获取
        system_prompt=code_reviewer["system_prompt"],
        tools=code_reviewer["tools"],
        middleware=[],  # 可以添加中间件
    )
    
    print(f"   类型: {type(actual_agent)}")
    print(f"   是否是 Runnable: {hasattr(actual_agent, 'invoke')}")
    
    # 步骤 3: 存储在 subagent_graphs 字典中
    subagent_graphs = {
        code_reviewer["name"]: actual_agent
    }
# pylint: disable
    
    print("\n3️⃣ 存储在 subagent_graphs 字典中:")
    print(f"   subagent_graphs = {list(subagent_graphs.keys())}")
    
    # 步骤 4: 运行时调用（模拟 task 工具的行为）
    print("\n4️⃣ 运行时调用（就像调用普通 Agent）:")
    
    # 准备输入状态
    subagent_state = {
        "messages": [HumanMessage(content="审查这段代码: def foo(): pass")]
    }
    
    print(f"   调用: subagent_graphs['code-reviewer'].invoke(state)")
    print(f"   输入: {subagent_state['messages'][0].content}")
    
    # 实际调用（注释掉以避免真实 API 调用）
    # result = subagent_graphs["code-reviewer"].invoke(subagent_state)
    # print(f"   输出: {result['messages'][-1].content}")
    
    print("\n✅ 结论: SubAgent 配置 → create_agent → 真正的 Agent → 存储在闭包中 → 运行时调用")


# ============================================================================
# 示例 2: Backend 的价值 - 统一接口，多种实现
# ============================================================================

def example_2_backend_abstraction():
    """演示 Backend 抽象层的价值"""
    
    print("\n" + "=" * 80)
    print("示例 2: Backend 的价值 - 统一接口，多种实现")
    print("=" * 80)
    
    # 场景 1: 开发环境 - 使用 StateBackend（临时存储）
    print("\n📦 场景 1: 开发环境 - StateBackend")
    print("-" * 80)
    
    agent_dev = create_deep_agent(
        model="openai:gpt-4o-mini",
        middleware=[
            FilesystemMiddleware(
                backend=lambda rt: StateBackend(rt)  # 临时存储
            )
        ],
        checkpointer=MemorySaver(),
    )
    
    print("✅ 创建成功: 文件存储在 Agent State 中")
    print("   - 持久化: 通过 Checkpointer")
    print("   - 跨会话: ❌ (每个线程独立)")
    print("   - 适用: 开发、测试、临时文件")
    
    # 场景 2: 生产环境 - 使用 StoreBackend（持久存储）
    print("\n📦 场景 2: 生产环境 - StoreBackend")
    print("-" * 80)
    
    store = InMemoryStore()  # 生产环境可以用 PostgresStore
    
    agent_prod = create_deep_agent(
        model="openai:gpt-4o-mini",
        middleware=[
            FilesystemMiddleware(
                backend=lambda rt: StoreBackend(rt, namespace=("user-files",))
            )
        ],
        checkpointer=MemorySaver(),
        store=store,
    )
    
    print("✅ 创建成功: 文件存储在 LangGraph Store 中")
    print("   - 持久化: ✅ (永久保存)")
    print("   - 跨会话: ✅ (所有线程共享)")
    print("   - 适用: 用户偏好、长期记忆、知识库")
    
    # 场景 3: 企业环境 - 使用 CompositeBackend（混合路由）
    print("\n📦 场景 3: 企业环境 - CompositeBackend")
    print("-" * 80)
    
    agent_enterprise = create_deep_agent(
        model="openai:gpt-4o-mini",
        middleware=[
            FilesystemMiddleware(
                backend=CompositeBackend(
                    default=lambda rt: StateBackend(rt),  # 默认：临时存储
                    routes={
                        "/memories/": lambda rt: StoreBackend(rt, namespace=("memories",)),
                        "/projects/": lambda rt: StoreBackend(rt, namespace=("projects",)),
                    }
                )
            )
        ],
        checkpointer=MemorySaver(),
        store=store,
    )
    
    print("✅ 创建成功: 根据路径路由到不同 Backend")
    print("   路由规则:")
    print("   - /memories/user.json  → StoreBackend (持久化)")
    print("   - /projects/app.py     → StoreBackend (持久化)")
    print("   - /temp/cache.txt      → StateBackend (临时)")
    print("   - 适用: 企业级应用、复杂存储需求")
    
    print("\n✅ 结论: 相同的 FilesystemMiddleware 代码，不同的 Backend 实现")
    print("   → 无需修改工具代码，只需切换 Backend 配置")


# ============================================================================
# 示例 3: 完整示例 - SubAgent + Backend 组合
# ============================================================================

def example_3_complete_example():
    """完整示例：SubAgent 和 Backend 的组合使用"""
    
    print("\n" + "=" * 80)
    print("示例 3: 完整示例 - SubAgent + Backend 组合")
    print("=" * 80)
    
    # 定义专业的子智能体
    subagents = [
        {
            "name": "file-analyzer",
            "description": "分析文件内容、结构和依赖关系的专家",
            "system_prompt": "你是文件分析专家。分析文件的内容、结构、依赖关系和潜在问题。",
            "tools": [],  # 会继承主 Agent 的文件工具
        },
        {
            "name": "code-generator",
            "description": "根据需求生成高质量代码的专家",
            "system_prompt": "你是代码生成专家。根据需求生成清晰、高效、可维护的代码。",
            "tools": [],
        }
    ]
    
    # 创建企业级 Agent
    store = InMemoryStore()
    
    agent = create_deep_agent(
        model="openai:gpt-4o-mini",
        middleware=[
            # 文件系统中间件 + 混合 Backend
            FilesystemMiddleware(
                backend=CompositeBackend(
                    default=lambda rt: StateBackend(rt),
                    routes={
                        "/knowledge/": lambda rt: StoreBackend(rt, namespace=("knowledge",)),
                    }
                )
            ),
            # 子智能体中间件
            SubAgentMiddleware(
                default_model="openai:gpt-4o-mini",
                subagents=subagents,
                general_purpose_agent=True,  # 包含通用子智能体
            ),
        ],
        checkpointer=MemorySaver(),
        store=store,
    )
    
    print("\n✅ 创建成功！Agent 具备以下能力:")
    print("\n📁 文件操作能力:")
    print("   - 7 个文件工具 (ls, read, write, edit, glob, grep, execute)")
    print("   - 智能路由: /knowledge/ → 持久存储, 其他 → 临时存储")
    
    print("\n🤖 子智能体能力:")
    print("   - file-analyzer: 分析文件")
    print("   - code-generator: 生成代码")
    print("   - general-purpose: 通用任务")
    
    print("\n💡 使用示例:")
    print("   用户: '分析 /app.py 并生成测试代码'")
    print("   主 Agent: 决定调用 task 工具")
    print("   → task('分析 /app.py', 'file-analyzer')")
    print("   → file-analyzer 调用 read_file('/app.py')")
    print("   → 返回分析结果")
    print("   → task('生成测试代码', 'code-generator')")
    print("   → code-generator 生成测试代码")
    print("   → 返回最终结果")


# ============================================================================
# 主函数
# ============================================================================

if __name__ == "__main__":
    # 运行所有示例
    example_1_subagent_essence()
    example_2_backend_abstraction()
    example_3_complete_example()
    
    print("\n" + "=" * 80)
    print("🎉 所有示例运行完成！")
    print("=" * 80)
    print("\n核心要点:")
    print("1. SubAgent 本质 = create_agent 创建的 CompiledStateGraph")
    print("2. Backend 本质 = 统一接口 + 多种实现 + 可插拔设计")
    print("3. 两者结合 = 强大、灵活、可扩展的企业级 Agent 框架")

