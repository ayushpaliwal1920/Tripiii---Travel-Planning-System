import os
import certifi
from dotenv import load_dotenv
import asyncio
load_dotenv()

# for path issues with SSL certificates in requests library

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from typing import TypedDict , Annotated
import operator
import uuid

import psycopg
from psycopg.rows import dict_row

from langgraph.graph import StateGraph , START , END
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver





from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    SystemMessage,
    AIMessage,
)

from langchain_groq import ChatGroq
# from tools.tavily_tool import tavily_search
# from tools.flight_tool import search_flights

from mcp_client import (
    tavily_mcp_search,
    aviation_mcp_call,
    extract_destination,
    forecast_mcp_call,
    weather_mcp_call,
)

def get_database_url():
    database_url = os.getenv("DATABASE_URL", "").strip()

    if not database_url:
        raise ValueError("DATABASE_URL is missing from .env")

    # Repair the specific malformed suffix.
    database_url = database_url.replace(
        "/agent_memory_pfd1sslmode=require",
        "/agent_memory_pfd1?sslmode=require",
    )

    # Ensure SSL mode is present.
    if "sslmode=" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url += f"{separator}sslmode=require"

    return database_url


url = get_database_url()

print("Database URL configured:", bool(url))
print("SSL required:", "sslmode=require" in url)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is missing. Please add it to your .env file."
    )

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=GROQ_API_KEY,
)

# State : 

class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    weather_result: str
    itinerary: str
    llm_calls: int


# Flight Agent : 


# def flight_agent(state: TravelState):
#     query = state["user_query"]
#     flight_data = search_flights(query)

#     return {
#         "flight_results": str(flight_data),
#         "messages": [
#             AIMessage(content="Flight results fetched.")
#         ],
#         "llm_calls": state.get("llm_calls", 0) + 1,
#     }

FLIGHT_AGENT_PROMPT = """
You are an expert travel flight planner.

User query: {query}

Airport information: {airport_data}
Airline information: {airline_data}

Provide concise guidance on:
1. Likely departure and arrival airports
2. Airlines serving the route, if supported by the data
3. Estimated airfare range, clearly labeled as an estimate
4. Typical flight duration
5. Peak-season pricing warnings
6. Booking advice

Do not invent live flight availability or prices.
"""

async def flight_agent(state: TravelState):
    print("\nInside flight agent")

    query = state["user_query"]

    try:
        airport = await aviation_mcp_call("list_airports")
        airlines = await aviation_mcp_call("list_airlines")

        prompt = FLIGHT_AGENT_PROMPT.format(
            query=query,
            airport_data=str(airport)[:1500],
            airline_data=str(airlines)[:1500],
        )

        response = await llm.ainvoke([
            SystemMessage(
                content="You are an expert travel flight planner."
            ),
            HumanMessage(content=prompt),
        ])

        flight_data = response.content

    except Exception as e:
        print(f"AviationStack/flight agent error: {e}")
        flight_data = (
            "Flight information is currently unavailable. "
            "Please verify routes, schedules, and prices with an airline."
        )

    return {
        "flight_results": str(flight_data),
        "messages": [
            AIMessage(content="Flight recommendations generated.")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# Hotel Agent :


async def hotel_agent(state: TravelState):
    query = f"Best hotels for {state['user_query']}"

    try:
        hotel_results = await tavily_mcp_search(query)
        hotel_text = str(hotel_results)[:4000]
    except Exception as e:
        print(f"Hotel search error: {e}")
        hotel_text = (
            "Hotel search is temporarily unavailable. "
            "Please verify hotel prices and availability independently."
        )

    return {
        "hotel_results": hotel_text,
        "messages": [
            AIMessage(content="Hotel search completed.")
        ],
        "llm_calls": state.get("llm_calls", 0),
    }


# Weather agent  :


async def weather_agent(state: TravelState):
    """Fetch current weather and forecast for the trip destination."""

    # Step 1: Extract the destination from the user's request.
    city = extract_destination(state["user_query"])

    try:
        # Step 2: Call both weather MCP tools asynchronously.
        weather_data = await weather_mcp_call(city)
        forecast_data = await forecast_mcp_call(city)

        # Step 3: Combine the results into readable text.
        weather_result = f"""
        Destination: {city}

        Current Weather:
        {weather_data}

        Weather Forecast:
        {forecast_data}
        """

    except Exception as e:
        print(f"Weather agent error: {e}")

        weather_result = (
            f"Weather information is unavailable for {city}. "
            "Check a reliable weather service before travelling."
        )

    # Step 4: Return the result to LangGraph state.
    return {
        "weather_result": weather_result,
        "messages": [
            AIMessage(content=f"Weather information processed for {city}.")
        ],
    }


# Itinerary Agent 


async def itinerary_agent(state: TravelState):
    """Create an itinerary using flight, hotel, and weather information."""

    prompt = f"""
    Create a practical, budget-aware travel itinerary.

    User query:
    {state['user_query'][:1500]}

    Flight information:
    {state['flight_results'][:2500]}

    Hotel information:
    {state['hotel_results'][:2500]}

    Weather information:
    {state['weather_result'][:2000]}

    Requirements:
    1. Create a concise day-by-day itinerary.
    2. Suggest indoor alternatives for poor weather.
    3. Consider weather when recommending outdoor activities.
    4. Clearly distinguish verified information from estimates.
    5. Do not invent confirmed bookings or live prices.
    6. If weather information is unavailable, state that clearly.
    """

    response = await llm.ainvoke([
        SystemMessage(
            content="You are an expert travel planner."
        ),
        HumanMessage(content=prompt),
    ])

    return {
        "itinerary": str(response.content),
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }



# final response agent : 

async def final_agent(state: TravelState):
    final_prompt = f"""
    Create the final travel plan for the user.

    User request:
    {state['user_query'][:1500]}

    Flight information:
    {state['flight_results'][:2000]}

    Hotel suggestions:
    {state['hotel_results'][:2500]}

    Itinerary:
    {state['itinerary'][:3000]}

    Weather information:
    {state['weather_result'][:2000]}

    Use these sections:
    1. Trip Summary
    2. Flight Information
    3. Hotel Suggestions
    4. Day-by-Day Itinerary
    5. Estimated Budget
    6. Final Recommendations

    Be concise and practical.
    Clearly label estimated prices and unverified details.
    Never claim that a flight, hotel, or booking is confirmed unless verified.
"""

    response = await llm.ainvoke([
        SystemMessage(
            content="You are a professional AI travel planning assistant."
        ),
        HumanMessage(content=final_prompt),
    ])

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }

# Graph : 


# Create the LangGraph state machine
graph = StateGraph(TravelState)

# Register all agents
graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("weather_agent", weather_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_agent)

# Define the execution order
graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "weather_agent")
graph.add_edge("weather_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent", END)


# Checkpointer


DATABASE_URL = get_database_url()

connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

async def create_travel_graph():
    pool = AsyncConnectionPool(
        conninfo=DATABASE_URL,
        kwargs=connection_kwargs,
        min_size=1,
        max_size=10,
        open=False,
    )

    await pool.open(wait=True)

    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()

    compiled_graph = graph.compile(checkpointer=checkpointer)

    return compiled_graph, pool


travel_graph = None
db_pool = None

async def initialize_travel_graph():
    global travel_graph, db_pool

    if travel_graph is None:
        travel_graph, db_pool = await create_travel_graph()


# function for fast api

async def run_travel_agent(
    user_input: str,
    thread_id: str | None = None,
):
    await initialize_travel_graph()

    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    result = await travel_graph.ainvoke(
        {
            "messages": [HumanMessage(content=user_input)],
            "user_query": user_input,
            "flight_results": "",
            "hotel_results": "",
            "weather_result": "",
            "itinerary": "",
            "llm_calls": 0,
        },
        config=config,
    )

    return {
        "thread_id": thread_id,
        "answer": result["messages"][-1].content,
        "flight_results": result.get("flight_results", ""),
        "hotel_results": str(result.get("hotel_results", "")),
        "weather_result": result.get("weather_result", ""),
        "itinerary": result.get("itinerary", ""),
        "llm_calls": result.get("llm_calls", 0),
    }

