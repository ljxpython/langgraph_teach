"""
DeepAgents 框架完整示例代码
演示所有核心功能的使用
"""
import os

from deepagents import create_deep_agent
from deepagents.backends import StateBackend, StoreBackend, CompositeBackend
from langchain.chat_models import init_chat_model
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic
from langchain.agents.middleware import InterruptOnConfig
from langchain_core.tools import tool
os.environ["DEEPSEEK_API_KEY"] = "sk-12fe20a839dc4a8f8f995c92cce35215"
model = init_chat_model("deepseek:deepseek-chat")

# ============================================================================
# 示例 1: 基础文件管理助手
# ============================================================================
def example_1_basic_file_manager():
    """最简单的文件管理助手"""
    print("=" * 60)
    print("示例 1: 基础文件管理助手")
    print("=" * 60)
    
    # 创建最简单的 Agent（使用所有默认配置）
    agent = create_deep_agent(
        model=model,
        system_prompt="你是一个文件管理助手，帮助用户管理文件"
    )
    
    # 使用示例
    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": "创建一个项目结构：包含 src/, tests/, docs/ 三个目录"
        }]
    })
    
    print(result)


# ============================================================================
# 示例 2: 带子智能体的代码分析助手
# ============================================================================
def example_2_code_analyzer_with_subagents():
    """使用子智能体进行代码分析"""
    print("=" * 60)
    print("示例 2: 代码分析助手（带子智能体）")
    print("=" * 60)
    
    # 定义自定义工具
    @tool
    def run_linter(file_path: str) -> str:
        """运行代码检查工具"""
        return f"Linting {file_path}: Found 3 issues"
    
    # 定义专业子智能体
    code_reviewer = {
        "name": "code-reviewer",
        "description": "代码审查专家，审查代码质量和安全性",
        "system_prompt": """你是一个代码审查专家。
        审查代码时关注：
        1. 代码风格和规范
        2. 潜在的 bug
        3. 性能问题
        4. 安全漏洞
        
        返回详细的审查报告。""",
        "tools": [run_linter],
    }
    
    doc_generator = {
        "name": "doc-generator",
        "description": "文档生成专家，为代码生成详细的文档",
        "system_prompt": """你是一个技术文档专家。
        生成的文档应包括：
        1. API 文档
        2. 使用示例
        3. 架构说明
        
        使用 Markdown 格式。""",
        "tools": [],
    }
    
    # 创建 Agent
    agent = create_deep_agent(
        subagents=[code_reviewer, doc_generator],
        system_prompt="""你是一个代码分析助手。
        
        工作流程：
        1. 分析代码库结构
        2. 调用 code-reviewer 审查代码
        3. 调用 doc-generator 生成文档
        4. 汇总结果并提供改进建议
        """
    )
    
    # 使用示例
    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": "分析 /src 目录下的所有 Python 代码"
        }]
    })
    
    print(result)
# pragma: no cover  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002ZVRrM2VnPT06ZGQwMjY2MGM=


# ============================================================================
# 示例 3: 使用不同的 Backend
# ============================================================================
def example_3_different_backends():
    """演示不同 Backend 的使用"""
    print("=" * 60)
    print("示例 3: 不同 Backend 的使用")
    print("=" * 60)
    
    # 3.1 StateBackend - 临时存储
    print("\n3.1 StateBackend - 临时存储（默认）")
    agent_state = create_deep_agent(
        backend=lambda rt: StateBackend(rt),
        checkpointer=MemorySaver(),
    )
    
    # 3.2 StoreBackend - 持久存储
    print("\n3.2 StoreBackend - 持久存储")
    store = InMemoryStore()
    agent_store = create_deep_agent(
        backend=lambda rt: StoreBackend(rt),
        store=store,
        checkpointer=MemorySaver(),
    )
    
    # 3.3 CompositeBackend - 混合存储（推荐）
    print("\n3.3 CompositeBackend - 混合存储")
    composite_backend = CompositeBackend(
        default=lambda rt: StateBackend(rt),  # 默认临时存储
        routes={
            "/memories/": lambda rt: StoreBackend(rt),  # 长期记忆
            "/cache/": lambda rt: StateBackend(rt),     # 临时缓存
        }
    )
# noqa  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002ZVRrM2VnPT06ZGQwMjY2MGM=
    
    agent_composite = create_deep_agent(
        model=model,
        backend=composite_backend,
        store=store,
        checkpointer=MemorySaver(),
    )
    
    # 使用示例
    config = {"configurable": {"thread_id": "session-1"}}
    
    result = agent_composite.invoke({
        "messages": [{
            "role": "user",
            "content": """
            1. 在 /test.py 创建测试脚本（临时存储）
            2. 在 /memories/user_prefs.json 保存用户偏好（持久存储）
            3. 在 /cache/temp.txt 创建临时文件（临时存储）
            """
        }]
    }, config=config)
    
    print(result)


# ============================================================================
# 示例 4: 人机交互配置
# ============================================================================
def example_4_human_in_the_loop():
    """演示人机交互功能"""
    print("=" * 60)
    print("示例 4: 人机交互配置")
    print("=" * 60)

    # 配置人机交互
    interrupt_on = {
        "execute": True,  # 执行命令前需要批准
        "write_file": InterruptOnConfig(
            interrupt_before=True,   # 写文件前需要批准
            interrupt_after=False,   # 写文件后不需要确认
        ),
        "edit_file": True,  # 编辑文件前需要批准
    }

    # 创建 Agent
    checkpointer = MemorySaver()
    agent = create_deep_agent(
        checkpointer=checkpointer,
        interrupt_on=interrupt_on,
        system_prompt="你是一个安全的文件管理助手"
    )

    # 配置
    config = {"configurable": {"thread_id": "safe-session"}}

    # 第一步：用户请求（会触发中断）
    print("\n第一步：发起请求")
    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": "创建文件 /important.txt，内容是 'Secret Data'"
        }]
    }, config=config)

    print("Agent 已暂停，等待批准...")
    print(f"待执行操作: {result}")

    # 第二步：批准执行
    print("\n第二步：批准执行")
    result = agent.invoke(None, config=config)
    print(f"执行结果: {result}")


# ============================================================================
# 示例 5: 完整企业级应用
# ============================================================================
def example_5_enterprise_application():
    """完整的企业级应用示例"""
    print("=" * 60)
    print("示例 5: 企业级应用（所有功能组合）")
    print("=" * 60)

    # 1. 配置模型
    model = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        temperature=0,
    )

    # 2. 配置存储
    store = InMemoryStore()
    checkpointer = MemorySaver()

    # 3. 配置混合 Backend
    composite_backend = CompositeBackend(
        default=lambda rt: StateBackend(rt),  # 默认临时存储
        routes={
            "/memories/": lambda rt: StoreBackend(rt),   # 长期记忆
            "/projects/": lambda rt: StoreBackend(rt),   # 项目文件
        }
    )

    # 4. 定义子智能体
    subagents = [
        {
            "name": "code-reviewer",
            "description": "代码审查专家",
            "system_prompt": "你是代码审查专家，关注代码质量、安全性和最佳实践。",
        },
        {
            "name": "doc-writer",
            "description": "技术文档编写专家",
            "system_prompt": "你是技术文档专家，生成清晰、专业的文档。",
        },
    ]
# type: ignore  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002ZVRrM2VnPT06ZGQwMjY2MGM=

    # 5. 配置人机交互
    interrupt_on = {
        "execute": True,
        "write_file": True,
        "edit_file": True,
    }

    # 6. 创建 Agent
    agent = create_deep_agent(
        model=model,
        subagents=subagents,
        backend=composite_backend,
        store=store,
        checkpointer=checkpointer,
        interrupt_on=interrupt_on,
        debug=True,
        system_prompt="""你是一个企业级 AI 助手。

        核心能力：
        1. 文件管理：读写编辑文件
        2. 代码分析：审查代码质量
        3. 文档生成：自动生成技术文档
        4. 长期记忆：记住用户偏好和历史信息

        文件组织：
        - /projects/：项目文件（持久化）
        - /memories/：用户偏好和历史（持久化）
        - 其他：临时工作文件
        """
    )

    # 7. 使用示例
    config = {"configurable": {"thread_id": "enterprise-1"}}

    print("\n场景 1: 创建新项目")
    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": """
            创建一个新的 Python 项目 'user-service'，包括：
            1. 基础项目结构
            2. 用户管理 API
            3. 单元测试

            我的偏好：
            - 使用 FastAPI 框架
            - 代码风格：Black
            """
        }]
    }, config=config)

    print(result)

    print("\n场景 2: 跨会话使用（记住偏好）")
    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": "帮我写一个数据验证函数"
        }]
    }, config={"configurable": {"thread_id": "new-session"}})

    print(result)


# ============================================================================
# 示例 6: 并行子智能体研究
# ============================================================================
def example_6_parallel_research():
    """演示并行子智能体进行研究"""
    print("=" * 60)
    print("示例 6: 并行子智能体研究")
    print("=" * 60)

    agent = create_deep_agent(
        system_prompt="""你是一个研究助手。

        当需要研究多个独立主题时：
        1. 为每个主题启动一个独立的 task 子智能体
        2. 并行执行所有研究任务
        3. 收集所有结果
        4. 综合分析并生成报告
        """
    )

    # 使用示例
    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": """
            研究以下三个 AI 框架并比较：
            1. LangChain
            2. LlamaIndex
            3. AutoGPT

            对比维度：
            - 核心功能
            - 优缺点
            - 适用场景
            """
        }]
    })

    print(result)


# ============================================================================
# 主函数
# ============================================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DeepAgents 框架完整示例")
    print("=" * 60 + "\n")

    # 运行所有示例
    examples = [
        # ("基础文件管理", example_1_basic_file_manager),
        # ("代码分析（子智能体）", example_2_code_analyzer_with_subagents),
        ("不同 Backend", example_3_different_backends),
        # ("人机交互", example_4_human_in_the_loop),
        # ("企业级应用", example_5_enterprise_application),
        # ("并行研究", example_6_parallel_research),
    ]

    for name, func in examples:
        try:
            print(f"\n{'=' * 60}")
            print(f"运行示例: {name}")
            print(f"{'=' * 60}\n")
            func()
        except Exception as e:
            print(f"❌ 示例 {name} 执行失败: {e}")

        print("\n" + "-" * 60 + "\n")

    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)

