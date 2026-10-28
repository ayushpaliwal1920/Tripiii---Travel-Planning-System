# TOOLS TESTS : 

# from tools.tavily_tool import tavily_search
# from tools.flight_tool import search_flights
# from backend import run_travel_agent

# # res = tavily_search("Best travel destinations in Europe")

# # res = search_flights("India to London", limit=5)

# user_input = input("Enter travel req")

# response = run_travel_agent(
#     user_input=user_input,
#     thread_id="test_user"
# )

# print(response["answer"])


#   MCP TESTS : 


import asyncio
from dotenv import load_dotenv
from mcp_client import get_all_tools, tavily_mcp_search

load_dotenv()

async def main():
    query = "Latest news about Messi."

    # Step 1: List tools from the configured MCP servers
    tools = await get_all_tools()

    print("\nMCP tools loaded successfully.")

    # Step 2: Test the Tavily search tool
    result = await tavily_mcp_search(query)

    print("\nTavily search results:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
