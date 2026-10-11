import os
import requests
from dotenv import load_dotenv


load_dotenv()


def tavily_search(query):
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY environment variable is not set.")

    response = requests.post(
        "https://api.tavily.com/search",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"query": query, "max_results": 5},
        timeout=30,
    )
    response.raise_for_status()
    search_data = response.json()

    results = []

    for i, r in enumerate(search_data["results"], 1):

        title = r.get("title", "unknown")
        url = r.get("url", "")
        snippet = r.get("content", "").strip()

        
        if len(snippet) > 300:
            snippet = snippet[:300].rsplit(" ", 1)[0] + "..."

        
        results.append(
            f"{i}. **{title}**\n"
            f"   {url}\n"
            f"   {snippet}"
        )

    return "\n\n".join(results)
