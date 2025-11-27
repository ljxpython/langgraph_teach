import anyio
from fastmcp import FastMCP


mcp = FastMCP(name="CalculatorServer")

@mcp.tool
def add(a: int, b: int) -> int:
    """Adds two integer numbers together."""
    return a + b


def cpu_intensive_task(data: str) -> str:
    # Some heavy computation that could block the event loop
    return 'test'

@mcp.tool
async def wrapped_cpu_task(data: str) -> str:
    """CPU-intensive task wrapped to prevent blocking."""
    return await anyio.to_thread.run_sync(cpu_intensive_task, data)

@mcp.tool
def sub(a: int, b: int) -> int:
    """Subtracts two integer numbers."""
    return a - b


if __name__ == '__main__':
    mcp.run(transport='sse',host='0.0.0.0',port=8001)
