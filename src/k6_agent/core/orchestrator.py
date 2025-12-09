"""K6 Performance Testing Agent Orchestrator.

This module provides the main agent creation function that assembles
all components into a complete performance testing agent.

Based on the latest DeepAgents framework:
https://github.com/langchain-ai/deepagents
"""
from typing import Optional, List, Any, Dict, Sequence
from pathlib import Path
# noqa  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002V1c5eWRBPT06NTM4NzQwMmY=

from deepagents import create_deep_agent, SubAgent
from deepagents.backends import FilesystemBackend
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer
from langgraph.cache.base import BaseCache

from k6_agent.core.config import K6AgentConfig, KnowledgeConfig
from k6_agent.core.prompts import (
    ORCHESTRATOR_PROMPT,
    SCRIPT_GENERATOR_PROMPT,
    SCRIPT_GENERATOR_PROMPT_CONTINUED,
    TEST_EXECUTOR_PROMPT,
    RESULT_ANALYZER_PROMPT,
    REPORT_GENERATOR_PROMPT,
)


def create_k6_agent(
    model: Optional[Any] = None,
    config: Optional[K6AgentConfig] = None,
    tools: Optional[Sequence[Any]] = None,
    middleware: Optional[Sequence[Any]] = None,
    debug: bool = False,
    checkpointer: Optional[Checkpointer] = None,
    store: Optional[BaseStore] = None,
    cache: Optional[BaseCache] = None,
    enable_knowledge_retrieval: bool = True,
    knowledge_api_url: Optional[str] = None,
    name: str = "k6-agent",
    workspace_dir: Optional[str] = None,
    **kwargs,
):
    """Create a K6 performance testing agent.

    This function creates an enterprise-grade performance testing agent with:
    - Specialized sub-agents for different testing phases (script, executor, analyzer, reporter)
    - Integrated RAG knowledge retrieval for best practices
    - Built-in filesystem, todo list, and summarization middleware

    Args:
        model: Language model to use (optional, defaults to Claude Sonnet 4).
        config: K6AgentConfig instance (optional).
        tools: Additional tools to add to the agent.
        middleware: Additional middleware to apply after standard middleware.
        debug: Enable debug mode.
        checkpointer: Optional checkpointer for persisting agent state.
        store: Optional store for persistent storage.
        cache: Optional cache for the agent.
        enable_knowledge_retrieval: Enable RAG knowledge integration.
        knowledge_api_url: URL of the RAG knowledge API.
        name: Name of the agent.
        workspace_dir: Root directory for filesystem operations. All file paths
            will be virtual paths relative to this directory (e.g., /k6_scripts/test.js).
            Defaults to current working directory.
        **kwargs: Additional arguments passed to create_deep_agent.

    Returns:
        CompiledStateGraph: The configured K6 performance testing agent.

    Example:
        >>> agent = create_k6_agent(debug=True)
        >>> result = agent.invoke({
        ...     "messages": [{"role": "user", "content": "Create a load test for my API"}]
        ... })

    Note:
        The filesystem middleware uses virtual paths starting with '/'.
        For example:
        - /k6_scripts/load_test.js -> {workspace_dir}/k6_scripts/load_test.js
        - /k6_results/output.json -> {workspace_dir}/k6_results/output.json

        Never use Windows absolute paths (like C: drive paths).
    """

    # Initialize configuration
    if config is None:
        config = K6AgentConfig.from_env()

    # Override debug setting
    if debug:
        config.debug = True

    # Build tools list
    agent_tools = _create_agent_tools(config, enable_knowledge_retrieval, knowledge_api_url)
    if tools:
        agent_tools.extend(list(tools))

    # Build middleware stack
    agent_middleware = list(middleware) if middleware else []

    # Create sub-agents
    subagents = _create_subagents(config, enable_knowledge_retrieval, knowledge_api_url)

    # Build system prompt
    system_prompt = ORCHESTRATOR_PROMPT

    # Create filesystem backend with virtual mode enabled
    # This maps virtual paths like /k6_scripts/test.js to the workspace directory
    root_dir = workspace_dir or str(config.workspace_dir.resolve())
    backend = FilesystemBackend(root_dir=root_dir, virtual_mode=True)

    # Create the agent using latest DeepAgents API
    agent = create_deep_agent(
        model=model,
        tools=agent_tools,
        system_prompt=system_prompt,
        middleware=agent_middleware,
        subagents=subagents,
        checkpointer=checkpointer,
        store=store,
        cache=cache,
        backend=backend,
        debug=config.debug,
        name=name,
        **kwargs,
    )

    return agent


def _create_agent_tools(
    config: K6AgentConfig,
    enable_knowledge: bool,
    knowledge_api_url: Optional[str],
) -> List[Any]:
    """Create the agent's tool set."""
    from k6_agent.tools.k6_tools import (
        create_k6_script_tool,
        create_k6_validation_tool,
    )
    from k6_agent.tools.execution_tools import (
        create_k6_run_tool,
        create_k6_cloud_tool,
    )
    from k6_agent.tools.analysis_tools import (
        create_result_parser_tool,
        create_metrics_analyzer_tool,
    )
    
    tools = [
        create_k6_script_tool(),
        create_k6_validation_tool(),
        create_k6_run_tool(),
        create_k6_cloud_tool(),
        create_result_parser_tool(),
        create_metrics_analyzer_tool(),
    ]
    
    # Add knowledge retrieval tools if enabled
    if enable_knowledge and config.knowledge.enabled:
        from k6_agent.knowledge import (
            KnowledgeClient,
            create_knowledge_retrieval_tool,
            create_scenario_design_tool,
            create_script_optimization_tool,
            create_analysis_guide_tool,
            create_bottleneck_diagnosis_tool,
        )
        
        api_url = knowledge_api_url or config.knowledge.api_url
        client = KnowledgeClient(
            api_url=api_url,
            api_key=config.knowledge.api_key,
            timeout=config.knowledge.timeout,
        )
# fmt: off  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002V1c5eWRBPT06NTM4NzQwMmY=
        
        tools.extend([
            create_knowledge_retrieval_tool(client),
            create_scenario_design_tool(client),
            create_script_optimization_tool(client),
            create_analysis_guide_tool(client),
            create_bottleneck_diagnosis_tool(client),
        ])
    
    return tools


def _create_middleware_stack(config: K6AgentConfig) -> List[Any]:
    """Create additional middleware stack.

    Note: DeepAgents already includes built-in middleware:
    - TodoListMiddleware: For task management
    - FilesystemMiddleware: For file operations (ls, read, write, edit, glob, grep, execute)
    - SubAgentMiddleware: For sub-agent orchestration
    - SummarizationMiddleware: For context window management
    - AnthropicPromptCachingMiddleware: For cost optimization

    This function adds custom middleware for the K6 agent.
    """
    middleware: List[Any] = []
# fmt: off  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002V1c5eWRBPT06NTM4NzQwMmY=

    # Custom middleware can be added here if needed
    # Example: Add validation or monitoring middleware
    # if config.environment == Environment.PRODUCTION:
    #     middleware.append(ProductionMonitoringMiddleware())

    return middleware


def _create_subagents(
    config: K6AgentConfig,
    enable_knowledge: bool,
    knowledge_api_url: Optional[str],
) -> List[SubAgent]:
    """Create specialized sub-agents using DeepAgents SubAgent TypedDict format.

    Each SubAgent has:
        - name: Agent identifier
        - description: Used by main agent to decide when to invoke
        - system_prompt: Instructions for the sub-agent
        - tools: Tools available to the sub-agent
    """
    subagents: List[SubAgent] = []

    # Script Generator Sub-Agent
    script_generator_tools: List[Any] = []
    from k6_agent.tools.k6_tools import create_k6_script_tool, create_k6_validation_tool
    script_generator_tools.extend([
        create_k6_script_tool(),
        create_k6_validation_tool(),
    ])

    if enable_knowledge and config.knowledge.enabled:
        from k6_agent.knowledge import (
            KnowledgeClient,
            create_scenario_design_tool,
            create_script_optimization_tool,
        )
        api_url = knowledge_api_url or config.knowledge.api_url
        client = KnowledgeClient(api_url=api_url, api_key=config.knowledge.api_key)
        script_generator_tools.extend([
            create_scenario_design_tool(client),
            create_script_optimization_tool(client),
        ])

    # SubAgent is a TypedDict, so we use dict syntax
    subagents.append({
        "name": "script-generator",
        "description": "Expert in K6 script generation with modern scenarios, executors (ramping-vus, constant-arrival-rate, etc.), and best practices. Use this agent when you need to create or optimize K6 test scripts.",
        "system_prompt": SCRIPT_GENERATOR_PROMPT + SCRIPT_GENERATOR_PROMPT_CONTINUED,
        "tools": script_generator_tools,
    })

    # Test Executor Sub-Agent
    from k6_agent.tools.execution_tools import create_k6_run_tool, create_k6_cloud_tool
    subagents.append({
        "name": "test-executor",
        "description": "Expert in K6 test execution, monitoring, and cloud integration. Use this agent when you need to run K6 tests locally or in K6 Cloud.",
        "system_prompt": TEST_EXECUTOR_PROMPT,
        "tools": [create_k6_run_tool(), create_k6_cloud_tool()],
    })

    # Result Analyzer Sub-Agent
    analyzer_tools: List[Any] = []
    from k6_agent.tools.analysis_tools import (
        create_result_parser_tool,
        create_metrics_analyzer_tool,
    )
    analyzer_tools.extend([
        create_result_parser_tool(),
        create_metrics_analyzer_tool(),
    ])

    if enable_knowledge and config.knowledge.enabled:
        from k6_agent.knowledge import (
            KnowledgeClient,
            create_analysis_guide_tool,
            create_bottleneck_diagnosis_tool,
        )
        api_url = knowledge_api_url or config.knowledge.api_url
        client = KnowledgeClient(api_url=api_url, api_key=config.knowledge.api_key)
        analyzer_tools.extend([
            create_analysis_guide_tool(client),
            create_bottleneck_diagnosis_tool(client),
        ])

    subagents.append({
        "name": "result-analyzer",
        "description": "Expert in performance analysis, bottleneck detection, and metrics interpretation. Use this agent to analyze K6 test results and identify performance issues.",
        "system_prompt": RESULT_ANALYZER_PROMPT,
        "tools": analyzer_tools,
    })

    # Report Generator Sub-Agent
    from k6_agent.tools.report_tools import (
        create_chart_generation_tool,
        create_report_generation_tool,
        create_quick_summary_tool,
    )

    # Get LLM for chart generation if available
    report_llm = None  # Can be configured to use LLM for MCP chart generation

    report_tools = [
        create_chart_generation_tool(llm=report_llm),
        create_report_generation_tool(llm=report_llm),
        create_quick_summary_tool(),
    ]

    subagents.append({
        "name": "report-generator",
        "description": "Expert in professional performance report generation with charts and visualizations. Use this agent to create comprehensive HTML reports with response time charts, throughput analysis, error rate visualizations, and executive summaries from K6 test results.",
        "system_prompt": REPORT_GENERATOR_PROMPT,
        "tools": report_tools,
    })

    return subagents
# noqa  My80OmFIVnBZMlhtblk3a3ZiUG1yS002V1c5eWRBPT06NTM4NzQwMmY=

