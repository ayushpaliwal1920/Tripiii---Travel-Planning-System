
import os
import certifi
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY is missing from .env")

client = MultiServerMCPClient(
    {
        "tavily": {
            "transport": "streamable_http",
            "url": "https://mcp.tavily.com/mcp",
            "headers": {
                "Authorization": f"Bearer {TAVILY_API_KEY}"
            },
        }
    }
)

tavily_search_tool = None


async def get_all_tools():
    tools = await client.get_tools()

    print("\nAvailable MCP tools:")
    for tool in tools:
        print(tool.name)

    return tools


async def get_tavily_search_tool():
    global tavily_search_tool

    if tavily_search_tool is not None:
        return tavily_search_tool

    tools = await client.get_tools()

    for tool in tools:
        print(tool.name)

    tavily_search_tool = next(
        (tool for tool in tools if tool.name == "tavily_search"),
        None,
    )

    if tavily_search_tool is None:
        raise RuntimeError(
            "The MCP server did not expose a tool named 'tavily_search'."
        )

    return tavily_search_tool


async def tavily_mcp_search(query: str):
    tool = await get_tavily_search_tool()
    return await tool.ainvoke({"query": query})
