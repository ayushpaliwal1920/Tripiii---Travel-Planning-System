
import os
import certifi
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_groq import ChatGroq

# ============================================================
# 1. ENVIRONMENT CONFIGURATION
# ============================================================

# Load API keys and other configuration from the .env file.
load_dotenv()

# Configure SSL certificate paths for secure HTTPS requests.
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

# Read API keys from environment variables.
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=GROQ_API_KEY,
)

# Tavily is required for this configuration.
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY is missing from .env")


# ============================================================
# 2. CONFIGURE THE THREE MCP SERVERS
# ============================================================

client = MultiServerMCPClient({

    # SERVER 1: Tavily
    # Connects to Tavily's remote MCP server over HTTP.
    "tavily": {
        "transport": "streamable_http",
        "url": "https://mcp.tavily.com/mcp",
        "headers": {
            "Authorization": f"Bearer {TAVILY_API_KEY}"
        },
    },

    # SERVER 2: AviationStack
    # Starts the AviationStack MCP package as a local process.
    # Requires uvx to be installed and available on PATH.
    "aviationstack": {
        "transport": "stdio",
        "command": "uvx",
        "args": [
            "aviationstack-mcp"
        ],
        "env": {
            # This variable name must match the MCP package's
            # documented API-key environment variable.
            "AVIATION_STACK_API_KEY": AVIATIONSTACK_API_KEY or ""
        },
    },

    # SERVER 3: Your custom Weather MCP server
    # Launches your Python script using the project's venv.
    "weather": {
        "transport": "stdio",
        "command": (
            r"E:\Tripiii---Travel-Planning-System"
            r"\.venv\Scripts\python.exe"
        ),
        "args": [
            r"E:\Tripiii---Travel-Planning-System"
            r"\custom_weather_mcpServer.py"
        ],
        "env": {
            "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY or ""
        },
    },
})


# ============================================================
# 3. GLOBAL TOOL REGISTRY
# ============================================================

# MCP tools are discovered once and cached here.
# This avoids repeatedly requesting the same tool list.
all_tools = {}

# Individual tool references.
search_tool = None
current_weather_tool = None
forecast_tool = None

# Dictionary for AviationStack tools.
aviation_tools = {}


# ============================================================
# 4. INITIALIZE ALL MCP TOOLS
# ============================================================

async def initialize_mcp():
    """
    Discover tools exposed by all configured MCP servers,
    cache them, and assign the tools used by Tripiii.
    """

    global all_tools
    global search_tool
    global aviation_tools
    global current_weather_tool
    global forecast_tool

    # Do not discover tools again if initialization succeeded.
    if all_tools:
        return all_tools

    # Ask the configured MCP servers for their available tools.
    tools = await client.get_tools()

    # Build a dictionary for quick lookup by tool name.
    discovered_tools = {
        tool.name: tool
        for tool in tools
    }

    print("\n========== AVAILABLE MCP TOOLS ==========")

    for name in discovered_tools:
        print(name)

    print("=========================================\n")

    # Find Tavily's search tool.
    search_tool = discovered_tools.get("tavily_search")

    # Find the current-weather tool.
    current_weather_tool = discovered_tools.get(
        "get_current_weather"
    )

    # Find the forecast tool.
    forecast_tool = discovered_tools.get("get_forecast")

    # Store the tools that belong to AviationStack.
    # This excludes the known Tavily and weather tool names.
    non_aviation_names = {
        "tavily_search",
        "get_current_weather",
        "get_forecast",
    }

    discovered_aviation_tools = {
        name: tool
        for name, tool in discovered_tools.items()
        if name not in non_aviation_names
    }

    # Validate that the tools needed by this application exist.
    if search_tool is None:
        raise RuntimeError(
            "Tavily search tool not found. "
            f"Available tools: {list(discovered_tools)}"
        )

    if current_weather_tool is None:
        raise RuntimeError(
            "get_current_weather was not found. "
            "Check your custom Weather MCP server."
        )

    if forecast_tool is None:
        raise RuntimeError(
            "get_forecast was not found. "
            "Check that it has the @mcp.tool() decorator."
        )

    # Cache the discovered tools after successful validation.
    all_tools = discovered_tools
    aviation_tools = discovered_aviation_tools

    return all_tools


# ============================================================
# 5. GET ALL AVAILABLE TOOLS
# ============================================================

async def get_all_tools():
    """Initialize MCP servers and return all discovered tools."""

    return await initialize_mcp()


# ============================================================
# 6. TAVILY SEARCH FUNCTION
# ============================================================

async def tavily_mcp_search(query: str):
    """
    Search the web through Tavily MCP.

    Example:
        await tavily_mcp_search("Best hotels in Jaipur")
    """

    await initialize_mcp()

    return await search_tool.ainvoke({
        "query": query
    })


# ============================================================
# 7. AVIATIONSTACK TOOL FUNCTION
# ============================================================

async def aviation_mcp_call(
    tool_name: str,
    tool_args: dict | None = None,
):
    """
    Call an AviationStack MCP tool by name.

    Examples:
        await aviation_mcp_call("list_airports")
        await aviation_mcp_call("list_airlines")
    """

    await initialize_mcp()

    # Look up the requested tool by its exact name.
    tool = aviation_tools.get(tool_name)

    if tool is None:
        raise ValueError(
            f"Aviation tool '{tool_name}' was not found. "
            f"Available candidate tools: {list(aviation_tools)}"
        )

    # Execute the selected MCP tool asynchronously.
    return await tool.ainvoke(tool_args or {})


# ============================================================
# 8. CURRENT WEATHER FUNCTION
# ============================================================

async def weather_mcp_call(city: str):
    """
    Get current weather for a city.

    Example:
        await weather_mcp_call("Dehradun")
    """

    await initialize_mcp()

    return await current_weather_tool.ainvoke({
        "city": city
    })


# ============================================================
# 9. WEATHER FORECAST FUNCTION
# ============================================================

async def forecast_mcp_call(city: str):
    """
    Get forecast information for a city.

    Example:
        await forecast_mcp_call("Jaipur")
    """

    await initialize_mcp()

    return await forecast_tool.ainvoke({
        "city": city
    })

# Destination extractor : 

def extract_destination(query : str):
    prompt = f""" Extract only the destination city or country 
                Query : {query}
                Return only destination name .
    """

    response = llm.invoke(prompt)

    return response.content.strip()