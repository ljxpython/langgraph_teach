"""Knowledge retrieval integration for K6 performance testing.

This module provides integration with external RAG (Retrieval-Augmented Generation)
knowledge bases to enhance the agent's capabilities in:
- Performance scenario design best practices
- K6 script writing patterns and optimizations
- Test result analysis methodologies
- Bottleneck identification and root cause analysis

Example:
    >>> from k6_agent.knowledge import KnowledgeClient, KnowledgeRetriever
    >>> 
    >>> client = KnowledgeClient(api_url="http://localhost:8000")
    >>> retriever = KnowledgeRetriever(client)
    >>> 
    >>> # Retrieve K6 best practices
    >>> results = await retriever.retrieve_k6_practices("load testing scenarios")
"""
# pylint: disable  MC8yOmFIVnBZMlhtblk3a3ZiUG1yS002U3paaVpBPT06NGQwZTBlM2U=

from k6_agent.knowledge.client import KnowledgeClient, QueryMode, QueryRequest, QueryResponse
from k6_agent.knowledge.retriever import (
    KnowledgeRetriever,
    create_knowledge_retrieval_tool,
    create_scenario_design_tool,
    create_script_optimization_tool,
    create_analysis_guide_tool,
    create_bottleneck_diagnosis_tool,
)

__all__ = [
    # Client
    "KnowledgeClient",
    "QueryMode",
    "QueryRequest",
    "QueryResponse",
    # Retriever
    "KnowledgeRetriever",
    # Tools
    "create_knowledge_retrieval_tool",
    "create_scenario_design_tool",
    "create_script_optimization_tool",
    "create_analysis_guide_tool",
    "create_bottleneck_diagnosis_tool",
]

# pragma: no cover  MS8yOmFIVnBZMlhtblk3a3ZiUG1yS002U3paaVpBPT06NGQwZTBlM2U=
