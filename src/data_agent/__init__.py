"""Data Collection Agent Module.

This module provides a LangGraph-based agent for collecting API data and storing it
in a knowledge base through a three-node workflow:

1. Node 1: Fetch API addresses (from user input or auto-parsing)
2. Node 2: Parallel crawl API data using crawl4ai
3. Node 3: Parallel insert data into RAG knowledge base

Example:
    >>> from src.data_agent import create_data_collection_agent
    >>> agent, rag_url, api_key = create_data_collection_agent(
    ...     rag_api_url="http://localhost:8000"
    ... )
    >>> result = agent.invoke({
    ...     "api_urls": ["https://example.com/api"],
    ...     "rag_api_url": "http://localhost:8000"
    ... })
"""

from .agent import (
    DataCollectionState,
    APIEndpoint,
    CrawledContent,
    fetch_api_addresses,
    crawl_api_data,
    insert_to_knowledge_base,
    create_data_collection_graph,
    create_data_collection_agent,
)

__all__ = [
    "DataCollectionState",
    "APIEndpoint",
    "CrawledContent",
    "fetch_api_addresses",
    "crawl_api_data",
    "insert_to_knowledge_base",
    "create_data_collection_graph",
    "create_data_collection_agent",
]
