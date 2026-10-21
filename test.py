from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights
from backend import run_travel_agent

# res = tavily_search("Best travel destinations in Europe")

# res = search_flights("India to London", limit=5)

user_input = input("Enter travel req")

response = run_travel_agent(
    user_input=user_input,
    thread_id="test_user"
)

print(response["answer"])