from tavily import TavilyClient
import os 
from dotenv import load_dotenv

load_dotenv()

client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
    )

def tavily_search(query: str):
    response = client.search(
        query=query,
        max_results=5
     )

    result = []

    for i , r in enumerate(response["results"] , 1):
        title = r.get("title" , "Unknown")
        url   = r.get("url" , "Unknown")
        snippet = r.get("content", "").strip()

        # keep only the first 300 characters of the snippet to avoid wall-of-text 

        if len(snippet) > 300:
            snippet = snippet[:300].rstrip()[0] + "..."

        result.append(f"{i}. **{title}**\n{url}\n{snippet}\n") 
    
    return "\n".join(result)

