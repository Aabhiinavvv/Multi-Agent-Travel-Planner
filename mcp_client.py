"""Lazy MCP client setup for TripMate's Python agent workflow.

API keys are validated only when their corresponding MCP service is used. This
allows the FastAPI health page to start even when optional integrations are not
configured yet.
"""
from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import certifi
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient


PROJECT_DIR = Path(__file__).resolve().parent
WEATHER_SERVER_PATH = PROJECT_DIR / "custom_weather_mcp_server.py"

load_dotenv(PROJECT_DIR / ".env", override=False)
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

_clients: dict[str, MultiServerMCPClient] = {}
_tool_cache: dict[str, dict[str, Any]] = {}


def _required_env(name: str) -> str:
    """Return a configured environment variable or raise a useful error."""
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"{name} is not configured. Add it to the project .env file "
            "or provide it as an environment variable."
        )
    return value


def _server_client(server_name: str) -> MultiServerMCPClient:
    """Create one MCP client per service so missing keys stay isolated."""
    if server_name in _clients:
        return _clients[server_name]

    if server_name == "tavily":
        api_key = _required_env("TAVILY_API_KEY")
        config = {
            "tavily": {
                "transport": "streamable_http",
                "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={api_key}",
            }
        }
    elif server_name == "aviationstack":
        api_key = _required_env("AVIATIONSTACK_API_KEY")
        uvx_command = shutil.which("uvx") or "uvx"
        aviation_env = os.environ.copy()
        aviation_env["AVIATION_STACK_API_KEY"] = api_key
        config = {
            "aviationstack": {
                "transport": "stdio",
                "command": uvx_command,
                "args": ["aviationstack-mcp"],
                "env": aviation_env,
            }
        }
    elif server_name == "weather":
        api_key = _required_env("OPENWEATHER_API_KEY")
        if not WEATHER_SERVER_PATH.is_file():
            raise FileNotFoundError(
                f"Weather MCP server not found: {WEATHER_SERVER_PATH}"
            )
        weather_env = os.environ.copy()
        weather_env["OPENWEATHER_API_KEY"] = api_key
        config = {
            "weather": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(WEATHER_SERVER_PATH)],
                "env": weather_env,
            }
        }
    else:
        raise ValueError(f"Unknown MCP server: {server_name}")

    client = MultiServerMCPClient(config)
    _clients[server_name] = client
    return client


async def _server_tools(server_name: str) -> dict[str, Any]:
    """Load and cache tools for one configured MCP server."""
    if server_name not in _tool_cache:
        client = _server_client(server_name)
        tools = await client.get_tools(server_name=server_name)
        _tool_cache[server_name] = {tool.name: tool for tool in tools}

        if not _tool_cache[server_name]:
            raise RuntimeError(
                f"{server_name} MCP connected but returned no tools."
            )

    return _tool_cache[server_name]


async def get_all_tools() -> list[Any]:
    """Load tools independently; a failed service does not block the others."""
    all_tools: list[Any] = []
    for server_name in ("tavily", "aviationstack", "weather"):
        try:
            tools = list((await _server_tools(server_name)).values())
            all_tools.extend(tools)
            print(f"\\nAvailable tools from {server_name} MCP:")
            for tool in tools:
                print(f"  - {tool.name}")
        except Exception as exc:
            print(f"\\nCould not connect to {server_name} MCP: {exc}")
    return all_tools


async def tavily_mcp_search(query: str) -> Any:
    """Search web pages through Tavily MCP."""
    if not query or not query.strip():
        raise ValueError("Tavily search query cannot be empty.")
    tools = await _server_tools("tavily")
    tool = tools.get("tavily_search")
    if tool is None:
        raise RuntimeError(
            "Tavily MCP did not expose 'tavily_search'. "
            f"Available tools: {', '.join(sorted(tools)) or 'none'}"
        )
    return await tool.ainvoke({"query": query.strip()})


async def aviation_mcp_call(
    tool_name: str,
    tool_args: dict[str, Any] | None = None,
) -> Any:
    """Invoke a named AviationStack MCP tool."""
    tools = await _server_tools("aviationstack")
    tool = tools.get(tool_name)
    if tool is None:
        raise ValueError(
            f"AviationStack tool '{tool_name}' was not found. "
            f"Available tools: {', '.join(sorted(tools)) or 'none'}"
        )
    return await tool.ainvoke(tool_args or {})


async def weather_mcp_call(
    tool_name: str,
    tool_args: dict[str, Any] | None = None,
) -> Any:
    """Invoke a named custom Weather MCP tool."""
    tools = await _server_tools("weather")
    tool = tools.get(tool_name)
    if tool is None:
        raise ValueError(
            f"Weather tool '{tool_name}' was not found. "
            f"Available tools: {', '.join(sorted(tools)) or 'none'}"
        )
    return await tool.ainvoke(tool_args or {})


def extract_destination(query: str) -> str:
    """Extract a likely destination phrase from a natural-language trip query.

    The supervisor's structured destination takes precedence in backend.py.
    This helper is a lightweight fallback and deliberately returns an empty
    string rather than guessing when the query does not name a destination.
    """
    text = str(query or "").strip()
    if not text:
        return ""

    patterns = (
        r"\bfrom\s+.+?\s+to\s+(.+)$",
        r"\b(?:destination\s*(?:is|:)|trip\s+to|travel\s+to|"
        r"travelling\s+to|traveling\s+to|visit|visiting|explore|to)\s+(.+)$",
        r"\b(?:trip|travel|vacation|holiday|stay)\s+in\s+(.+)$",
    )
    match = None
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            break

    if not match:
        return ""

    candidate = match.group(1).strip(" \t,.;:!?")
    candidate = re.split(
        r"\s+(?:from|for|during|between|with|under|within|in|starting|"
        r"departing|leaving|on|next)\b|[,;.!?]",
        candidate,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    candidate = re.sub(
        r"^(?:the city of|city of)\s+",
        "",
        candidate,
        flags=re.IGNORECASE,
    )
    return candidate.strip()


async def weather_mcp_search(city: str) -> Any:
    """Get current weather for a destination city."""
    city = str(city or "").strip()
    if not city:
        raise ValueError("A destination city is required for weather lookup.")
    return await weather_mcp_call(
        "get_current_weather",
        {"city": city},
    )


async def forecast_mcp_search(city: str) -> Any:
    """Get the short-range forecast for a destination city."""
    city = str(city or "").strip()
    if not city:
        raise ValueError("A destination city is required for forecast lookup.")
    return await weather_mcp_call(
        "get_forecast",
        {"city": city},
    )
