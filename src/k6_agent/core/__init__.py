"""Core components for K6 Performance Testing Agent.

This module provides the core framework components including:
- Agent orchestration and creation
- Configuration management
- System prompts for agents
"""

from k6_agent.core.config import (
    K6AgentConfig,
    K6Config,
    Environment,
    MonitoringConfig,
    ReportConfig,
    KnowledgeConfig,
)
from k6_agent.core.prompts import (
    ORCHESTRATOR_PROMPT,
    SCRIPT_GENERATOR_PROMPT,
    TEST_EXECUTOR_PROMPT,
    RESULT_ANALYZER_PROMPT,
    REPORT_GENERATOR_PROMPT,
)

__all__ = [
    # Configuration
    "K6AgentConfig",
    "K6Config",
    "Environment",
    "MonitoringConfig",
    "ReportConfig",
    "KnowledgeConfig",
    # Prompts
    "ORCHESTRATOR_PROMPT",
    "SCRIPT_GENERATOR_PROMPT",
    "TEST_EXECUTOR_PROMPT",
    "RESULT_ANALYZER_PROMPT",
    "REPORT_GENERATOR_PROMPT",
]

