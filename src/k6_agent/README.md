# K6 Agent 🚀

**Enterprise-grade AI-powered K6 Performance Testing Platform**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-2.0.0-green.svg)]()

基于 [DeepAgents](./libs/deepagents/) 框架和 [K6](https://k6.io/) 性能测试工具构建的智能性能测试平台。通过自然语言交互，自动完成性能测试脚本生成、执行、分析和报告生成的全流程。

## ✨ 核心特性

- 🤖 **自然语言交互** - 用对话方式描述测试需求，AI 自动生成专业 K6 脚本
- 📊 **智能分析** - 自动分析测试结果，定位性能瓶颈，提供优化建议
- 📈 **专业报告** - 生成包含图表的 HTML 专业报告，支持 MCP Chart Server
- 🧠 **知识增强** - 集成 RAG 知识库，获取性能测试最佳实践
- 🏢 **企业级** - 内置缓存、限流、审计日志、监控等中间件

## 🏗️ 架构

```
k6_agent/
├── agents/              # 子智能体
│   ├── script_generator.py    # K6 脚本生成专家
│   ├── test_executor.py       # 测试执行专家
│   ├── result_analyzer.py     # 结果分析专家
│   └── report_generator.py    # 报告生成专家
├── core/                # 核心组件
│   ├── orchestrator.py        # 智能体编排器
│   ├── config.py              # 配置管理
│   └── prompts.py             # 系统提示词
├── k6/                  # K6 集成
│   └── scenarios.py           # 场景、执行器、阈值
├── knowledge/           # 知识检索 (RAG)
│   ├── client.py              # RAG API 客户端
│   └── retriever.py           # 知识检索工具
├── middleware/          # 企业中间件
│   ├── validation.py          # 输入输出验证
│   ├── monitoring.py          # 性能监控
│   └── enterprise.py          # 缓存/限流/审计
├── tools/               # LangChain 工具
│   ├── k6_tools.py            # 脚本生成工具
│   ├── execution_tools.py     # 执行工具
│   └── analysis_tools.py      # 分析工具
└── utils/               # 工具类
    ├── chart_generator.py     # 图表类型定义
    └── mcp_charts.py          # MCP 图表生成
```

## 🚀 快速开始

### 安装

```bash
# 基础安装
pip install -e .

# 包含图表支持
pip install -e ".[charts]"

# 开发环境
pip install -e ".[dev]"
```

### 环境配置

```bash
# 必需
export OPENAI_API_KEY="your-api-key"

# 可选 - 知识库 API
export KNOWLEDGE_API_URL="http://your-rag-api:8000"

# 可选 - K6 配置
export K6_BINARY_PATH="/usr/local/bin/k6"
export K6_OUTPUT_DIR="./results"
```

### 基础使用

```python
from k6_agent import create_k6_agent, K6AgentConfig

# 创建配置
config = K6AgentConfig()

# 创建智能体 (基于最新 DeepAgents API)
agent = create_k6_agent(
    config=config,
    enable_knowledge_retrieval=True,
    debug=True,  # 可选：启用调试模式
)

# 执行性能测试
result = agent.invoke({
    "messages": [{"role": "user", "content": "对 http://api.example.com/users 进行负载测试，100并发，持续5分钟"}]
})

# 使用持久化存储
from langgraph.checkpoint.memory import MemorySaver

agent = create_k6_agent(
    checkpointer=MemorySaver(),  # 持久化会话状态
    name="my-k6-agent",
)
```

### 脚本生成

```python
from k6_agent import K6ScriptGenerator, ApiEndpoint, HttpMethod

generator = K6ScriptGenerator()
script = generator.generate_script(
    endpoints=[
        ApiEndpoint(
            url="http://api.example.com/users",
            method=HttpMethod.GET,
            headers={"Authorization": "Bearer ${TOKEN}"},
        )
    ],
    vus=100,
    duration="5m",
)
print(script)
```

### 图表生成

```python
from k6_agent import MCPChartGenerator, TestResult

# 从 K6 JSON 结果加载
with open("./results/test.json") as f:
    k6_data = json.load(f)

result = TestResult.from_k6_json(k6_data, "Load Test")

# 生成图表
chart_gen = MCPChartGenerator(llm=my_llm)
charts = chart_gen.generate_all_charts([result], output_dir="./charts")
```

## 📋 支持的测试类型

| 类型 | 执行器 | 描述 |
|------|--------|------|
| 负载测试 | `ramping-vus` | 逐步增加虚拟用户 |
| 压力测试 | `constant-vus` | 固定高并发 |
| 浸泡测试 | `constant-vus` | 长时间稳定负载 |
| 尖峰测试 | `ramping-vus` | 突发流量模拟 |
| 容量测试 | `ramping-arrival-rate` | 确定系统容量上限 |

## 🧠 知识库集成

支持通过 RAG API 获取性能测试知识：

```python
from k6_agent.knowledge import KnowledgeRetriever

retriever = KnowledgeRetriever(api_url="http://rag-api:8000")

# 场景设计知识
design_tips = retriever.retrieve_scenario_design("电商秒杀场景")

# 瓶颈诊断知识
diagnosis = retriever.retrieve_bottleneck_diagnosis("数据库连接池耗尽")
```

## 📊 报告生成

自动生成专业 HTML 报告：

```python
from k6_agent.agents import ReportGeneratorAgent

generator = ReportGeneratorAgent(output_dir="./reports")
report_path = generator.generate_report(
    result_path="./results/load_test.json",
    config=ReportConfig(
        title="API 负载测试报告",
        include_charts=True,
    )
)
```

报告包含：
- ✅ 测试状态总览（通过/失败）
- 📈 关键指标卡片（请求数、吞吐量、成功率、错误率）
- ⏱️ 响应时间分析表（平均、P50、P90、P95、P99）
- 📦 数据传输统计
- 🎯 阈值合规检查

## 🔧 K6 场景配置

```python
from k6_agent import K6Options, K6Scenario, ExecutorType, Stage

# 阶梯式负载场景
options = K6Options(
    scenarios={
        "load_test": K6Scenario(
            executor=ExecutorType.RAMPING_VUS,
            stages=[
                Stage(duration="1m", target=50),
                Stage(duration="3m", target=100),
                Stage(duration="1m", target=0),
            ],
        )
    },
    thresholds={
        "http_req_duration": ["p(95)<500"],
        "http_req_failed": ["rate<0.01"],
    },
)
```

## 🛠️ 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 代码检查
ruff check src/

# 类型检查
mypy src/k6_agent/
```

## 📚 相关资源

- [K6 官方文档](https://grafana.com/docs/k6/latest/)
- [K6 GitHub](https://github.com/grafana/k6)
- [DeepAgents 框架](https://github.com/langchain-ai/deepagents)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)

## 📄 License

MIT License - 详见 [LICENSE](LICENSE) 文件

