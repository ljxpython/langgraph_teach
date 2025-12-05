# DeepAgents 框架完整学习资料 📚

> 一套完整的 DeepAgents 框架学习资料，包含深度解析、示例代码、快速参考和可视化图表

## 📖 文档目录

### 1. [DeepAgents框架深度解析.md](DeepAgents框架深度解析.md) 🎓
**完整的框架深度解析文档**

包含内容：
- ✅ 框架概览和架构
- ✅ 核心概念详解
- ✅ Middleware 中间件详解（FilesystemMiddleware, SubAgentMiddleware, SummarizationMiddleware, HumanInTheLoopMiddleware）
- ✅ SubAgent 子智能体详解（定义、使用场景、并行处理）
- ✅ Backend 后端存储详解（StateBackend, StoreBackend, SandboxBackend, CompositeBackend）
- ✅ Store 长期记忆详解
- ✅ Interrupt_on 人机交互详解
- ✅ 5 个完整应用案例
- ✅ 最佳实践总结
- ✅ 常见问题 FAQ

**适合**: 深入学习框架原理和设计思想

---

### 2. [DeepAgents示例代码.py](DeepAgents示例代码.py) 💻
**可运行的完整示例代码**

包含 6 个实际示例：
1. **基础文件管理助手** - 最简单的入门示例
2. **代码分析助手（带子智能体）** - 演示子智能体的使用
3. **不同 Backend 的使用** - 对比 StateBackend、StoreBackend、CompositeBackend
4. **人机交互配置** - 演示 interrupt_on 的使用
5. **企业级应用** - 所有功能组合的完整示例
6. **并行子智能体研究** - 演示并行处理能力

**适合**: 动手实践，快速上手

---

### 3. [DeepAgents快速参考.md](DeepAgents快速参考.md) ⚡
**速查手册**

包含内容：
- ✅ 核心参数速查表
- ✅ 默认工具速查表
- ✅ Backend 类型对比表
- ✅ 子智能体配置模板
- ✅ 人机交互配置模板
- ✅ 常用配置模板（开发/生产/企业级）
- ✅ 最佳实践清单
- ✅ 故障排查指南

**适合**: 日常开发时快速查阅

---

## 🎨 可视化图表

文档中包含多个 Mermaid 图表，帮助理解框架架构：

### 1. DeepAgents 框架整体架构
展示了中间件层、存储层、子智能体和持久化组件之间的关系

### 2. 文件操作流程
演示 FilesystemMiddleware 如何处理文件操作请求

### 3. 子智能体并行执行流程
展示主 Agent 如何并行调度多个子智能体

### 4. CompositeBackend 路由机制
说明混合存储如何根据路径前缀路由到不同的 Backend

### 5. 人机交互中断流程
详细展示 interrupt_on 的工作流程

### 6. Middleware 执行顺序
展示 7 个默认中间件的执行顺序和职责

### 7. 不同应用场景的配置选择
决策树帮助选择合适的配置方案

---

## 🚀 快速开始

### 最简单的示例

```python
from deepagents import create_deep_agent

# 创建 Agent
agent = create_deep_agent(
    system_prompt="你是一个智能助手"
)

# 使用 Agent
result = agent.invoke({
    "messages": [{"role": "user", "content": "创建一个文件 /test.txt"}]
})

print(result)
```

### 企业级配置示例

```python
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import MemorySaver

# 配置存储
store = InMemoryStore()
checkpointer = MemorySaver()

# 配置混合 Backend
composite_backend = CompositeBackend(
    default=lambda rt: StateBackend(rt),
    routes={
        "/memories/": lambda rt: StoreBackend(rt),
        "/projects/": lambda rt: StoreBackend(rt),
    }
)

# 定义子智能体
subagents = [
    {
        "name": "code-reviewer",
        "description": "代码审查专家",
        "system_prompt": "你是代码审查专家...",
    },
]

# 创建 Agent
agent = create_deep_agent(
    backend=composite_backend,
    store=store,
    checkpointer=checkpointer,
    subagents=subagents,
    interrupt_on={
        "execute": True,
        "write_file": True,
    },
    system_prompt="你是企业级 AI 助手"
)
```

---

## 📊 核心概念速览

### Middleware（中间件）
给 AI 加装的功能模块，每个中间件负责一个特定功能：
- **FilesystemMiddleware**: 文件操作（ls, read, write, edit, glob, grep, execute）
- **SubAgentMiddleware**: 子智能体调度
- **SummarizationMiddleware**: 对话历史压缩
- **HumanInTheLoopMiddleware**: 人机交互控制

### Backend（后端存储）
决定文件存储在哪里：
- **StateBackend**: 临时存储（不跨会话）
- **StoreBackend**: 持久存储（跨会话）
- **SandboxBackend**: 沙箱执行（支持命令）
- **CompositeBackend**: 混合路由（企业级）

### SubAgent（子智能体）
让主 Agent 能够委派任务给专业助手：
- 🎯 任务隔离
- ⚡ 并行处理
- 💰 节省 Token

### Store（长期记忆）
跨会话持久化存储，用于保存需要长期记住的信息

### Interrupt_on（人机交互）
控制 AI 在执行哪些操作前需要人类批准

---

## 🎯 学习路径建议

### 初学者
1. 阅读 [DeepAgents框架深度解析.md](DeepAgents框架深度解析.md) 的"框架概览"部分
2. 运行 [DeepAgents示例代码.py](DeepAgents示例代码.py) 的示例 1 和示例 2
3. 参考 [DeepAgents快速参考.md](DeepAgents快速参考.md) 进行实践

### 进阶开发者
1. 深入阅读 [DeepAgents框架深度解析.md](DeepAgents框架深度解析.md) 的所有章节
2. 运行所有示例代码，理解不同配置的差异
3. 根据实际需求定制子智能体和 Backend 配置

### 企业级应用
1. 学习 CompositeBackend 的路由机制
2. 设计合理的文件组织结构（/memories/, /projects/, /cache/）
3. 配置完善的人机交互策略
4. 参考示例 5 构建企业级应用

---

## 💡 最佳实践

### ✅ 推荐做法
- ✅ 使用 CompositeBackend 组合不同存储策略
- ✅ 为敏感操作配置 interrupt_on
- ✅ 使用子智能体隔离复杂任务
- ✅ 将长期记忆存储在 /memories/ 路径
- ✅ 开发时开启 debug 模式

### ❌ 避免做法
- ❌ 不要在简单任务中使用子智能体
- ❌ 不要在生产环境关闭所有 interrupt_on
- ❌ 不要混用不同的 Store 实例
- ❌ 不要在没有 Checkpointer 时使用 interrupt_on

---

## 🔗 相关资源

- 📖 [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- 📖 [LangChain 官方文档](https://python.langchain.com/)
- 💻 [DeepAgents GitHub](https://github.com/langchain-ai/deepagents)

---

## 📝 文档更新日志

- **2024-01-XX**: 创建完整学习资料
  - 深度解析文档（1500+ 行）
  - 6 个完整示例代码
  - 快速参考手册
  - 7 个可视化图表

---

**Happy Learning! 🎉**

