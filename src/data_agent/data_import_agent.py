"""Data Collection Agent using LangGraph with Send API (Optimized Version).

This is the optimized version using Send API for true parallel execution.

Workflow:
1. Node 0: Extract URLs from user messages using LLM
2. Node 1: Fetch API addresses (merge all URL sources)
3. Node 2: Crawl Orchestrator - Dispatch crawl workers
4. Node 3: Crawl Worker - Crawl single URL (parallel via Send API)
5. Node 4: Filter Orchestrator - Dispatch filter workers
6. Node 4.5: Filter Worker - Filter non-API content using LLM (parallel via Send API)
7. Node 5: Insert Orchestrator - Dispatch insert workers
8. Node 6: Insert Worker - Insert single document (parallel via Send API)

Benefits of Send API:
- True parallel execution visible in LangGraph
- Independent worker states
- Better error isolation
- Supports persistence and interrupts
- Avoids Windows event loop issues
"""
import asyncio
import logging
import concurrent.futures
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict, Annotated
import json
import operator

from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.types import Command, Send
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LinkPreviewConfig
import httpx
import os
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
# pylint: disable

# ============================================================================
# Windows Compatibility Fix
# ============================================================================

# Note: We do NOT set WindowsSelectorEventLoopPolicy globally anymore
# because it doesn't support subprocess operations needed by Playwright.
# Instead, we run the crawler in a separate thread with its own ProactorEventLoop.

logger = logging.getLogger(__name__)

# ============================================================================
# State Definitions
# ============================================================================

# 从仓库根目录 .env 加载环境变量（不覆盖已存在的系统环境变量）
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env", override=False)
_ = os.getenv("DEEPSEEK_API_KEY")
deepseek = ChatDeepSeek(model="deepseek-chat")

class DataCollectionState(MessagesState, total=False):
    """Main state for the data collection workflow."""
    # Input
    api_urls: List[str]
    user_input: Optional[str]

    # Node 0 output
    extracted_urls: List[str]

    # Node 1 output
    discovered_urls: List[str]

    # Node 3 output (Crawl workers write here)
    crawled_data: Annotated[List[Dict[str, Any]], operator.add]

    # Node 4 output (Filter workers write here)
    filtered_data: Annotated[List[Dict[str, Any]], operator.add]

    # Node 6 output (Insert workers write here)
    insertion_results: Annotated[List[Dict[str, Any]], operator.add]

    # Configuration
    llm: Optional[BaseChatModel]
    rag_api_url: str
    rag_api_key: Optional[str]

    # Error tracking
    error_messages: Annotated[List[str], operator.add]


class CrawlWorkerState(TypedDict):
    """State for individual crawl worker."""
    url: str
    crawled_data: Annotated[List[Dict[str, Any]], operator.add]
    error_messages: Annotated[List[str], operator.add]


class FilterWorkerState(TypedDict):
    """State for individual filter worker."""
    url: str
    content: Dict[str, Any]
    filtered_data: Annotated[List[Dict[str, Any]], operator.add]
    error_messages: Annotated[List[str], operator.add]


class InsertWorkerState(MessagesState):
    """State for individual insert worker."""
    url: str
    content: Dict[str, Any]
    rag_api_url: str
    rag_api_key: Optional[str]
    # insertion_results: Annotated[List[Dict[str, Any]], operator.add]
    error_messages: Annotated[List[str], operator.add]


# ============================================================================
# Node 0: Extract URLs from Messages (Same as before)
# ============================================================================

async def extract_urls_from_messages(state: DataCollectionState) -> Command:
    """Node 0: Extract URLs from user messages using LLM."""
    logger.info("Node 0: Extracting URLs from messages using LLM...")

    # Check if LLM is provided
    # llm = state.get("llm")
    llm = deepseek
    if not llm:
        logger.info("No LLM provided, skipping URL extraction from messages")
        return Command(goto="fetch_api_addresses")

    # Check if messages exist
    messages = state.get("messages", [])
    if not messages:
        logger.info("No messages to extract URLs from")
        return Command(goto="fetch_api_addresses")

    # Prepare system prompt for URL extraction
    system_prompt = """You are a helpful assistant that extracts URLs from user messages.

Your task:
1. Read the user's message carefully
2. Extract any URLs or web addresses mentioned
3. Return them in a JSON format

Return format:
{
    "urls": ["url1", "url2", ...],
    "explanation": "Brief explanation of what you found"
}

If no URLs are found, return an empty list."""

    try:
        # Invoke LLM
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            *messages
        ])

        # Parse response
        content = response.content
        logger.info(f"LLM response: {content[:200]}...")

        # Try to parse JSON
        try:
            import re
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content

            result = json.loads(json_str)
            extracted_urls = result.get("urls", [])
            explanation = result.get("explanation", "")

            logger.info(f"LLM extracted {len(extracted_urls)} URLs")
            if explanation:
                logger.info(f"Explanation: {explanation}")

            return Command(
                update={"extracted_urls": extracted_urls},
                goto="fetch_api_addresses"
            )

        except json.JSONDecodeError:
            # Fallback: use regex to extract URLs
            logger.warning("Failed to parse JSON, using regex fallback")
            import re
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            urls = re.findall(url_pattern, content)
            logger.info(f"Regex extracted {len(urls)} URLs")

            return Command(
                update={"extracted_urls": urls},
                goto="fetch_api_addresses"
            )

    except Exception as e:
        logger.error(f"Error extracting URLs from messages: {e}")
        return Command(
            update={"error_messages": [f"URL extraction error: {str(e)}"]},
            goto="fetch_api_addresses"
        )


# ============================================================================
# Node 1: Fetch API Addresses (Same as before)
# ============================================================================

# pylint: disable

async def fetch_api_addresses(state: DataCollectionState) -> Command:
    """Node 1: Fetch and merge API addresses from all sources."""
    logger.info("Node 1: Fetching API addresses...")

    api_urls = []

    # Mode 1: User provided URLs directly
    if state.get("api_urls"):
        user_urls = state["api_urls"]
        api_urls.extend(user_urls)
        logger.info(f"Using {len(user_urls)} user-provided URLs")

    # Mode 2: LLM-extracted URLs from messages
    if state.get("extracted_urls"):
        extracted_urls = state["extracted_urls"]
        api_urls.extend(extracted_urls)
        logger.info(f"Using {len(extracted_urls)} LLM-extracted URLs")

    # Mode 3: Auto-parse from documentation URL (simplified for now)
    if state.get("user_input"):
        user_input = state["user_input"]
        logger.info(f"Auto-parsing from: {user_input}")
        # Add user_input as a URL to crawl
        api_urls.append(user_input)

    # Remove duplicates
    api_urls = list(set(api_urls))

    if not api_urls:
        logger.warning("No API URLs found from any source")
        return Command(
            update={"api_urls": []},
            goto=END
        )

    logger.info(f"Total {len(api_urls)} unique URLs to crawl")

    return Command(
        update={"api_urls": api_urls},
        goto="crawl_orchestrator"
    )


# ============================================================================
# Node 2: Crawl Orchestrator (Send API)
# ============================================================================

def crawl_orchestrator_route(state: DataCollectionState):
    """Routing function for crawl orchestrator - returns Send list or next node.

    This function is used with add_conditional_edges to dispatch workers.
    """
    api_urls = state.get("api_urls", [])

    if not api_urls:
        logger.warning("No URLs to crawl, skipping to insert_orchestrator")
        return "insert_orchestrator"

    logger.info(f"Dispatching {len(api_urls)} crawl workers")

    # Return Send list to create parallel workers
    return [Send("crawl_worker", {"url": url}) for url in api_urls]


# ============================================================================
# Node 3: Crawl Worker (Parallel Execution)
# ============================================================================

def _sync_crawl_url(url: str) -> dict:
    """
    Synchronous function to crawl a URL.

    This function runs in a separate thread with its own event loop.
    This is necessary because:
    1. Playwright (used by crawl4ai) requires subprocess support
    2. Windows SelectorEventLoop doesn't support subprocess
    3. Running in a separate thread allows using ProactorEventLoop
    """
    async def _async_crawl():
        async with AsyncWebCrawler() as crawler:
            return await crawler.arun(url=url)

    # Create a new event loop for this thread
    # On Windows, this will be ProactorEventLoop which supports subprocesses
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_async_crawl())
        return {
            "success": result.success,
            "html": result.html if result.success else None,
            "markdown": result.markdown if result.success else None,
            "title": getattr(result, "title", ""),
            "description": getattr(result, "description", ""),
            "error_message": getattr(result, "error_message", None) if not result.success else None
        }
    finally:
        loop.close()


async def crawl_worker(state: CrawlWorkerState):
    """Node 3: Worker that crawls a single URL.

    Uses ThreadPoolExecutor to run the crawler in a separate thread,
    which avoids Windows event loop compatibility issues with Playwright.
    """
    url = state["url"]
    logger.info(f"Worker crawling: {url}")

    try:
        # Run the crawler in a separate thread with its own event loop
        # This avoids Windows event loop issues with Playwright/subprocess
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(executor, _sync_crawl_url, url)

        if result["success"]:
            logger.info(f"✓ Successfully crawled: {url}")
            return {
                "crawled_data": [{
                    "url": url,
                    "content": result["html"],
                    "markdown": result["markdown"],
                    "metadata": {
                        "title": result["title"],
                        "description": result["description"],
                    },
                    "success": True
                }]
            }
        else:
            logger.error(f"✗ Failed to crawl {url}: {result['error_message']}")
            return {
                "crawled_data": [{
                    "url": url,
                    "success": False,
                    "error": result["error_message"]
                }],
                "error_messages": [f"Crawl failed for {url}: {result['error_message']}"]
            }

    except Exception as e:
        logger.error(f"✗ Exception crawling {url}: {e}")
        return {
            "crawled_data": [{
                "url": url,
                "success": False,
                "error": str(e)
            }],
            "error_messages": [f"Crawl exception for {url}: {str(e)}"]
        }


# ============================================================================
# Node 4: Filter Orchestrator (Send API)
# ============================================================================

def filter_orchestrator_route(state: DataCollectionState):
    """Routing function for filter orchestrator - returns Send list or next node.

    This function is used with add_conditional_edges to dispatch filter workers.
    """
    crawled_data = state.get("crawled_data", [])

    # Filter successful crawls
    successful_crawls = [item for item in crawled_data if item.get("success")]

    if not successful_crawls:
        logger.warning("No successful crawls to filter, skipping to insert_orchestrator")
        return "insert_orchestrator"

    logger.info(f"Dispatching {len(successful_crawls)} filter workers")

    # Return Send list to create parallel workers
    return [
        Send("filter_worker", {
            "url": item["url"],
            "content": item
        })
        for item in successful_crawls
    ]


# ============================================================================
# Node 4.5: Filter Worker (Parallel Execution)
# ============================================================================

FILTER_SYSTEM_PROMPT = """你是一个API文档过滤专家。

输入是一段 Markdown 格式的网页内容。请提取并保留以下与 API 接口相关的内容：
- API 端点 (URL paths)
- HTTP 方法 (GET, POST, PUT, DELETE 等)
- 请求参数和请求体
- 响应格式和状态码
- 认证信息
- 代码示例

过滤掉以下无关内容：
- 导航菜单、页脚
- 广告和推广内容
- 通用介绍和欢迎语
- 版权声明
- 与 API 无关的链接

直接返回过滤后的 Markdown 内容，不要添加任何解释或说明。
如果内容中没有 API 相关信息，返回 "NO_API_CONTENT"。
"""


async def filter_worker(state: FilterWorkerState):
    """Node 4.5: Worker that filters a single document using LLM."""
    url = state["url"]
    content = state["content"]

    logger.info(f"Worker filtering: {url}")

    try:
        markdown_content = content.get("markdown", "")

        if not markdown_content:
            logger.warning(f"No markdown content to filter for {url}")
            return {
                "filtered_data": [{
                    "url": url,
                    "content": content.get("content", ""),
                    "markdown": "",
                    "metadata": content.get("metadata", {}),
                    "success": True,
                    "filtered": False
                }]
            }

        # Use LLM to filter content
        response = await deepseek.ainvoke([
            SystemMessage(content=FILTER_SYSTEM_PROMPT),
            HumanMessage(content=f"请过滤以下内容，只保留与 API 接口相关的部分：\n\n{markdown_content[:50000]}")
        ])

        filtered_markdown = response.content.strip()

        # Check if no API content was found
        if filtered_markdown == "NO_API_CONTENT":
            logger.info(f"No API content found in {url}")
            return {
                "filtered_data": [{
                    "url": url,
                    "content": content.get("content", ""),
                    "markdown": "",
                    "metadata": content.get("metadata", {}),
                    "success": True,
                    "filtered": True,
                    "has_api_content": False
                }]
            }

        logger.info(f"✓ Filtered {url}: {len(markdown_content)} -> {len(filtered_markdown)} chars")

        return {
            "filtered_data": [{
                "url": url,
                "content": content.get("content", ""),
                "markdown": filtered_markdown,
                "metadata": content.get("metadata", {}),
                "success": True,
                "filtered": True,
                "has_api_content": True
            }]
        }

    except Exception as e:
        logger.error(f"✗ Exception filtering {url}: {e}")
        # On error, pass through original content
        return {
            "filtered_data": [{
                "url": url,
                "content": content.get("content", ""),
                "markdown": content.get("markdown", ""),
                "metadata": content.get("metadata", {}),
                "success": True,
                "filtered": False,
                "filter_error": str(e)
            }],
            "error_messages": [f"Filter exception for {url}: {str(e)}"]
        }


# ============================================================================
# Node 5: Insert Orchestrator (Send API)
# ============================================================================

def insert_orchestrator_route(state: DataCollectionState):
    """Routing function for insert orchestrator - returns Send list or END.

    This function is used with add_conditional_edges to dispatch workers.
    Uses filtered_data from filter workers instead of raw crawled_data.
    """
    filtered_data = state.get("filtered_data", [])
    rag_api_url = state.get("rag_api_url", "http://localhost:9621")
    rag_api_key = state.get("rag_api_key")

    # Filter successful items that have API content
    items_to_insert = [
        item for item in filtered_data
        if item.get("success") and item.get("markdown")  # Only insert if has content
    ]

    if not items_to_insert:
        logger.warning("No filtered data with API content to insert, ending workflow")
        return END

    logger.info(f"Dispatching {len(items_to_insert)} insert workers")

    # Return Send list to create parallel workers
    return [
        Send("insert_worker", {
            "url": item["url"],
            "content": item,
            "rag_api_url": rag_api_url,
            "rag_api_key": rag_api_key
        })
        for item in items_to_insert
    ]


# ============================================================================
# Node 5: Insert Worker (Parallel Execution)
# ============================================================================

async def insert_worker(state: InsertWorkerState):
    """Node 5: Worker that inserts a single document into RAG."""
    url = state["url"]
    content = state["content"]
    rag_api_url = state["rag_api_url"]
    rag_api_key = state.get("rag_api_key")

    logger.info(f"Worker inserting: {url}")

    try:
        # Prepare document
        text_content = content.get("markdown", "")
        # return {
        #     "messages": [AIMessage(content=f"{url} 成功了")]
        # }
        # Insert into RAG
        async with httpx.AsyncClient() as client:
            headers = {}
            if rag_api_key:
                headers["Authorization"] = f"Bearer {rag_api_key}"

            response = await client.post(
                f"{rag_api_url}/documents/text",
                json={
                    "file_source": url,
                    "text": text_content
                },
                headers=headers,
                timeout=30.0
            )

            if response.status_code == 200:
                result = response.json()
                track_id = result.get("track_id", "unknown")
                logger.info(f"✓ Inserted {url} with track_id: {track_id}")

                # Return as AIMessage for frontend display
                success_message = f"✅ 已成功将 {url} 的 API 文档插入到知识库中 (track_id: {track_id})"
                return {
                    "messages": [AIMessage(content=success_message)]
                }
            else:
                logger.error(f"✗ Failed to insert {url}: {response.status_code}")
                error_message = f"❌ 插入 {url} 失败: HTTP {response.status_code}"
                return {
                    "messages": [AIMessage(content=error_message)],
                    "error_messages": [f"Insert failed for {url}: HTTP {response.status_code}"]
                }

    except Exception as e:
        logger.error(f"✗ Exception inserting {url}: {e}")
        error_message = f"❌ 插入 {url} 时发生错误: {str(e)}"
        return {
            "messages": [AIMessage(content=error_message)],
            "error_messages": [f"Insert exception for {url}: {str(e)}"]
        }


# ============================================================================
# Graph Construction
# ============================================================================

def create_data_collection_graph() -> StateGraph:
    """Create the optimized data collection graph using Send API."""

    # Create graph
    builder = StateGraph(DataCollectionState)

    # Add nodes
    builder.add_node("extract_urls_from_messages", extract_urls_from_messages)
    builder.add_node("fetch_api_addresses", fetch_api_addresses)
    builder.add_node("crawl_orchestrator", lambda state: {})  # 同步点，路由由 crawl_orchestrator_route 处理
    builder.add_node("crawl_worker", crawl_worker)
    builder.add_node("filter_orchestrator", lambda state: {})  # 同步点，路由由 filter_orchestrator_route 处理
    builder.add_node("filter_worker", filter_worker)
    builder.add_node("insert_orchestrator", lambda state: {})  # 同步点，路由由 insert_orchestrator_route 处理
    builder.add_node("insert_worker", insert_worker)

    # Add edges
    builder.add_edge(START, "extract_urls_from_messages")

    # Send API: crawl_orchestrator 分发 crawl_worker
    builder.add_conditional_edges(
        "crawl_orchestrator",
        crawl_orchestrator_route,  # 路由函数返回 Send 列表或字符串
        ["crawl_worker", "filter_orchestrator"],
    )

    # 所有 crawl_worker 完成后汇聚到 filter_orchestrator
    builder.add_edge("crawl_worker", "filter_orchestrator")

    # Send API: filter_orchestrator 分发 filter_worker
    builder.add_conditional_edges(
        "filter_orchestrator",
        filter_orchestrator_route,  # 路由函数返回 Send 列表或字符串
        ["filter_worker", "insert_orchestrator"],
    )

    # 所有 filter_worker 完成后汇聚到 insert_orchestrator
    builder.add_edge("filter_worker", "insert_orchestrator")

    # Send API: insert_orchestrator 分发 insert_worker
    builder.add_conditional_edges(
        "insert_orchestrator",
        insert_orchestrator_route,  # 路由函数返回 Send 列表或 END
        ["insert_worker", END],
    )

    # 所有 insert_worker 完成后结束
    builder.add_edge("insert_worker", END)

    # Compile
    graph = builder.compile()

    return graph

agent = create_data_collection_graph()
# ============================================================================
# Helper Functions
# ============================================================================

async def run_data_collection_workflow(
    messages: Optional[List[Dict[str, str]]] = None,
    api_urls: Optional[list] = None,
    user_input: Optional[str] = None,
    llm: Optional[BaseChatModel] = None,
    rag_api_url: str = "http://localhost:8000",
    rag_api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the optimized data collection workflow using Send API."""

    # Create graph
    graph = create_data_collection_graph()

    # Prepare initial state
    initial_state = {
        "api_urls": api_urls or [],
        "user_input": user_input,
        "llm": llm,
        "rag_api_url": rag_api_url,
        "rag_api_key": rag_api_key,
        "crawled_data": [],
        "insertion_results": [],
        "error_messages": [],
    }

    # Add messages if provided
    if messages:
        initial_state["messages"] = messages

    # Run workflow
    result = await graph.ainvoke(initial_state)

    return result


if __name__ == "__main__":
    # Example usage
    async def main():
        from langchain_deepseek import ChatDeepSeek

        llm = ChatDeepSeek(model="deepseek-chat", temperature=0)

        result = await run_data_collection_workflow(
            messages=[{
                "role": "user",
                "content": "请爬取 https://www.example.com"
            }],
            llm=llm,
            rag_api_url="http://localhost:8000",
        )

        print(f"Crawled: {len(result.get('crawled_data', []))}")
        print(f"Inserted: {len(result.get('insertion_results', []))}")

    asyncio.run(main())
