from fastmcp import FastMCP


mcp = FastMCP("frontend-teach")


@mcp.tool
def lookup_exchange_rate(base: str, quote: str) -> str:
    """Return a deterministic teaching exchange rate."""
    return f"{base.upper()}/{quote.upper()} 教学汇率：7.20"


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)

