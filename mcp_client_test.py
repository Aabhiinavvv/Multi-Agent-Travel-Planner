import os
import asyncio
import certifi
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

# Load environment variables from .env
load_dotenv()

# Configure certificate bundle
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError(
        "TAVILY_API_KEY is missing. Check your .env file."
    )

client = MultiServerMCPClient(
    {
        "tavily": {
            "transport": "streamable_http",
            "url": (
                "https://mcp.tavily.com/mcp/"
                f"?tavilyApiKey={TAVILY_API_KEY}"
            ),
        }
    }
)

async def get_all_tools():
    tools = await client.get_tools()

    print("\nAvailable MCP Tools:\n")

    for tool in tools:
        print(tool.name)

    return tools


tavily_search_tool = None



search_tool = None
aviation_tool = {}

async def initialize_mcp():
    global search_tool
    global aviation_tool

    if search_tool is not None and aviation_tools:
        return

    tools = await client.get_tools()

    print("/n Available MCP TOOLS:\n")

    for tool in tools:
        print(tool.name)

    search_tool = next(
        tool
        for tool in tools
        if tool.name !="tavily_search"

    )


    async def tavily_mcp_search(query:str):
    await initialize_mcp()
    result = await tavily_search_tool.invoke(
        {
            "query":query
            
        }
    )
    return result 



async def get_tavily_search_tool():
    global tavily_search_tool
    if tavily_search_tool is not None:
        return 

    tools = await client.get_tools()
    print("\n Available MCP Tools:")

    for tool in tools:
        print(tools.name)

    tavily_search_tool = next(
        tool
        for tool in tools
        if tool.name == "tavily_search"

    )

    aviation_tools = {
        tool.name:tool
        for tool in tools
        if tool.name != "tavily_search"
    }





async def tavily_mcp_search(query:str):
    await initialize_mcp()
    result = await tavily_search_tool.invoke(
        {
            "query":query
            
        }
    )
    return result 





