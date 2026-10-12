from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights

# res = tavily_search("Best travel destinations in Europe")

res = search_flights("India to London", limit=5)

print(res)