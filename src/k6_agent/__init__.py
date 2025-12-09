"""K6 Performance Testing Agent - Enterprise-grade AI-powered performance testing platform.

This package provides a professional-grade AI agent for K6 performance testing,
built on the DeepAgents framework with integrated RAG knowledge retrieval.

Architecture:
    k6_agent/
    ├── agents/              # Sub-agent implementations
    │   ├── script_generator.py    # K6 script generation expert
    │   ├── test_executor.py       # Test execution and monitoring
    │   ├── result_analyzer.py     # Performance analysis and bottleneck detection
    │   └── report_generator.py    # Professional report generation with charts
    ├── core/                # Core framework components
    │   ├── orchestrator.py        # Main agent orchestration
    │   ├── config.py              # Configuration management
    │   └── prompts.py             # System prompts for agents
    ├── k6/                  # K6 integration layer
    │   └── scenarios.py           # K6 scenarios, executors, and test types
    ├── knowledge/           # Knowledge retrieval integration (RAG)
    │   ├── client.py              # RAG API client (all query modes)
    │   └── retriever.py           # Knowledge retrieval tools for each phase
    ├── middleware/          # Enterprise middleware stack
    │   ├── validation.py          # Input/output validation
    │   ├── monitoring.py          # Performance monitoring
    │   └── enterprise.py          # Caching, rate limiting, audit logging
    ├── tools/               # LangChain agent tools
    │   ├── k6_tools.py            # K6 script generation tools
    │   ├── execution_tools.py     # Test execution tools
    │   └── analysis_tools.py      # Analysis and reporting tools
    └── utils/               # Utilities
        ├── chart_generator.py     # Chart types and specs
        └── mcp_charts.py          # MCP Chart Server integration (AntV)

Example:
    >>> from k6_agent import create_k6_agent, K6AgentConfig
    >>>
    >>> config = K6AgentConfig()
    >>> agent = create_k6_agent(config=config, enable_knowledge_retrieval=True)
    >>>
    >>> # Run a performance test
    >>> result = agent.invoke({
    ...     "messages": [{"role": "user", "content": "对我的API进行负载测试"}]
    ... })

Version: 2.0.0
"""
# pragma: no cover  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002YUhFeVV3PT06MTcwNWE5YjU=

__version__ = "2.0.0"
__author__ = "Performance Testing Team"

from k6_agent.core.config import K6AgentConfig, K6Config, Environment
from k6_agent.k6.scenarios import (
    K6Options,
    K6Scenario,
    ExecutorType,
    Stage,
    CustomMetric,
    TestData,
)
from k6_agent.tools.k6_tools import K6ScriptGenerator, ApiEndpoint, HttpMethod
from k6_agent.utils import (
    MCPChartGenerator,
    ChartType,
    ChartSpec,
    TestResult,
    Colors,
)
# fmt: off  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002YUhFeVV3PT06MTcwNWE5YjU=


# Lazy import of agent to avoid import errors if deepagents is not available
def create_k6_agent(*args, **kwargs):
    """Create a K6 performance testing agent.

    This function creates an enterprise-grade performance testing agent with:
    - Specialized sub-agents for different testing phases (script, executor, analyzer, reporter)
    - Integrated RAG knowledge retrieval for best practices
    - Built-in filesystem, todo list, and summarization middleware from DeepAgents

    Args:
        model: Language model to use (optional, defaults to Claude Sonnet 4).
        config: K6AgentConfig instance (optional).
        tools: Additional tools to add to the agent (optional).
        middleware: Additional middleware to apply (optional).
        debug: Enable debug mode (default: False).
        checkpointer: Optional checkpointer for persisting agent state.
        store: Optional store for persistent storage.
        cache: Optional cache for the agent.
        enable_knowledge_retrieval: Enable RAG knowledge integration (default: True).
        knowledge_api_url: URL of the RAG knowledge API (optional).
        name: Name of the agent (default: "k6-agent").
        workspace_dir: Root directory for filesystem operations. All file paths
            will be virtual paths relative to this directory (e.g., /k6_scripts/test.js).
            Defaults to current working directory.
        **kwargs: Additional arguments passed to create_deep_agent.

    Returns:
        CompiledStateGraph: The configured K6 performance testing agent.

    Example:
        >>> agent = create_k6_agent(debug=True)
        >>> result = agent.invoke({
        ...     "messages": [{"role": "user", "content": "Create a load test"}]
        ... })

    Note:
        The filesystem middleware uses virtual paths starting with '/'.
        For example:
        - /k6_scripts/load_test.js -> {workspace_dir}/k6_scripts/load_test.js
        - /k6_results/output.json -> {workspace_dir}/k6_results/output.json

        Never use Windows absolute paths (like C: drive paths).
    """
    from k6_agent.core.orchestrator import create_k6_agent as _create_agent
    return _create_agent(*args, **kwargs)
# pylint: disable  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002YUhFeVV3PT06MTcwNWE5YjU=


__all__ = [
    # Main agent factory
    "create_k6_agent",
    # Configuration
    "K6AgentConfig",
    "K6Config",
    "Environment",
    # K6 scenarios
    "K6Options",
    "K6Scenario",
    "ExecutorType",
    "Stage",
    "CustomMetric",
    "TestData",
    # Script generation
    "K6ScriptGenerator",
    "ApiEndpoint",
    "HttpMethod",
    # Chart generation (MCP)
    "MCPChartGenerator",
    "ChartType",
    "ChartSpec",
    "TestResult",
    "Colors",
    # Version
    "__version__",
]

# pylint: disable  My80OmFIVnBZMlhtblk3a3ZiUG1yS002YUhFeVV3PT06MTcwNWE5YjU=
