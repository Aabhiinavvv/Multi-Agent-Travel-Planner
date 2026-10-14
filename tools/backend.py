
import os
import asyncio
import uuid
import certifi

from dotenv import load_dotenv
from typing import TypedDict, Annotated
import operator

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver

from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)

from langchain_groq import ChatGroq

from tools.tavily_tool import tavily_search
from mcp_client import aviation_mcp_call


# ==========================================
# 1. ENVIRONMENT CONFIGURATION
# ==========================================

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


def get_database_url():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL environment variable is not set."
        )

    if "sslmode=" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url += f"{separator}sslmode=require"

    return database_url


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY environment variable is not set."
    )


# ==========================================
# 2. INITIALIZE LLM
# ==========================================

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=GROQ_API_KEY,
)


# ==========================================
# 3. DEFINE LANGGRAPH STATE
# ==========================================

class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    itinerary: str
    final_answer: str
    llm_calls: int


# ==========================================
# 4. FLIGHT AGENT
# ==========================================

FLIGHT_AGENT_PROMPT = """
You are an expert travel flight planner.

User Query:
{query}

Airport Information:
{airport_data}

Airline Information:
{airline_data}

Generate:
1. Likely departure airport
2. Likely arrival airport
3. Airlines serving this route
4. Typical flight duration
5. Estimated airfare range
6. Peak season pricing warning
7. Booking advice

Be concise and practical.

Do not invent live flight availability or verified ticket prices.
Clearly label estimates and missing information.
"""


def flight_agent(state: TravelState):
    print("\nInside Flight Agent")

    query = state["user_query"]

    try:
        # Retrieve airport and airline information from MCP.
        airports = asyncio.run(
            aviation_mcp_call("list_airports")
        )

        airlines = asyncio.run(
            aviation_mcp_call("list_airlines")
        )

        print("\nAirports:", airports)
        print("\nAirlines:", airlines)

        prompt = FLIGHT_AGENT_PROMPT.format(
            query=query,
            airport_data=str(airports)[:3000],
            airline_data=str(airlines)[:3000],
        )

        response = llm.invoke([
            SystemMessage(
                content="You are an expert travel flight planner."
            ),
            HumanMessage(content=prompt),
        ])

        flight_data = str(response.content)

        return {
            "flight_results": flight_data,
            "messages": [
                response,
            ],
            "llm_calls": state.get("llm_calls", 0) + 1,
        }

    except Exception as e:
        print("Flight Agent Error:", repr(e))

        return {
            "flight_results": (
                "Flight information could not be retrieved. "
                "Reason: " + str(e)
            ),
            "messages": [
                AIMessage(
                    content="Flight search encountered an error."
                )
            ],
        }


# ==========================================
# 5. HOTEL AGENT
# ==========================================

def hotel_agent(state: TravelState):
    print("\nInside Hotel Agent")

    query = (
        "Find suitable hotels, locations and available price "
        "information for this trip: "
        + state["user_query"]
    )

    try:
        hotel_data = tavily_search(query)

        return {
            "hotel_results": str(hotel_data),
            "messages": [
                AIMessage(
                    content="Hotel information search completed."
                )
            ],
        }

    except Exception as e:
        print("Hotel Agent Error:", repr(e))

        return {
            "hotel_results": (
                "Hotel information could not be retrieved. "
                "Reason: " + str(e)
            ),
            "messages": [
                AIMessage(
                    content="Hotel search encountered an error."
                )
            ],
        }


# ==========================================
# 6. ITINERARY AGENT
# ==========================================

def itinerary_agent(state: TravelState):
    print("\nInside Itinerary Agent")

    prompt = f"""
Create a complete travel itinerary.

User Query:
{state['user_query']}

Flight Results:
{state['flight_results']}

Hotel Results:
{state['hotel_results']}

Requirements:
- Make the itinerary practical and easy to follow.
- Respect the user's stated budget.
- Organize the plan day by day.
- Consider travel time and geographical distance.
- Clearly label estimates and missing information.
- Do not invent confirmed bookings or live prices.
"""

    response = llm.invoke([
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


# ==========================================
# 7. FINAL RESPONSE AGENT
# ==========================================

def final_agent(state: TravelState):
    print("\nInside Final Response Agent")

    final_prompt = f"""
Generate the final travel plan for the user.

User Request:
{state['user_query']}

Flights:
{state['flight_results']}

Hotels:
{state['hotel_results']}

Itinerary:
{state['itinerary']}

Organize the response into these sections:

1. Trip Summary
2. Flight Information
3. Hotel Suggestions
4. Day-by-Day Itinerary
5. Estimated Budget
6. Final Recommendations

Requirements:
- Be clear, practical and easy to understand.
- Do not invent flight availability or hotel prices.
- Explain when pricing or booking information is unavailable.
- Distinguish estimates from verified information.
"""

    response = llm.invoke([
        SystemMessage(
            content=(
                "You are a professional AI travel planning assistant. "
                "Use the supplied information accurately."
            )
        ),
        HumanMessage(content=final_prompt),
    ])

    return {
        "final_answer": str(response.content),
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ==========================================
# 8. BUILD LANGGRAPH WORKFLOW
# ==========================================

graph = StateGraph(TravelState)

graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_agent)

graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent", END)


# ==========================================
# 9. POSTGRESQL CHECKPOINTER
# ==========================================

DATABASE_URL = get_database_url()

connection_pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=5,
    kwargs={
        "autocommit": True,
        "row_factory": dict_row,
        "prepare_threshold": 0,
    },
    check=ConnectionPool.check_connection,
    open=True,
)

checkpointer = PostgresSaver(connection_pool)
checkpointer.setup()

travel_graph = graph.compile(
    checkpointer=checkpointer
)


# ==========================================
# 10. FUNCTION CALLED BY FASTAPI
# ==========================================

def run_travel_agent(
    user_input: str,
    thread_id: str | None = None,
):
    if not user_input.strip():
        raise ValueError("Please enter a travel request.")

    if not thread_id:
        thread_id = f"user-{uuid.uuid4().hex}"

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    initial_state: TravelState = {
        "messages": [
            HumanMessage(content=user_input)
        ],
        "user_query": user_input,
        "flight_results": "",
        "hotel_results": "",
        "itinerary": "",
        "final_answer": "",
        "llm_calls": 0,
    }

    result = travel_graph.invoke(
        initial_state,
        config=config,
    )

    return {
        "thread_id": thread_id,
        "answer": result.get("final_answer", ""),
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "itinerary": result.get("itinerary", ""),
        "llm_calls": result.get("llm_calls", 0),
    }
