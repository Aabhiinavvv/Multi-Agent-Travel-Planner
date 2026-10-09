import os 
import certifi 
from dotenv import load_dotenv 

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from typing import TypedDict, Annotated
import operator 
import uuid
import psycopg
from psycopg.rows import dict_row

from langgraph.graph import StateGraph, START , END
from langgraph.checkpoint.postgres import PostgresSaver 

from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)
from langchain_groq import ChatGroq
from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights

def get_database_url():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set.")
    if "sslmode" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url += f"{separator}sslmode=require"
    return database_url
        

GROQ_API_KEY = OS.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set.")


llm = ChatGroq(
    model = "llama-3.3-70b-versatile",
    api_key = GROQ_API_KEY,
)

#STATE
class TravelState(TypeDict):
    messages: Annotated[list[AnyMessage],operator.add]
    user_query:str
    flight_results:str
    hotel_results:str
    itinerary:str
    llm_calls:int

# FLIGHT AGENT 

def flight_agent(state:TravelState):
    query = state["user_query"]
    flight_data =search_flights(query)
    return {
        "flight_results":flight_data,
        "messages":[
            AIMessages(content="Flight results fetched")
        ],
        "llm_calls":state.get("llm_calls",0)+1


    }

#HOTEL AGENT

def hotel_agent(state:TravelState):
    query= f"best hotels for{state['user_query']}"
    hotel_results = tavily_search(query)

    return { 
        "hotel_results": hotel_results,
        "messages":[
            AIMessage(content="hotel information fetched"),

        ],
        "llm_calls":state.get("llm_calls",0)+1

    }

