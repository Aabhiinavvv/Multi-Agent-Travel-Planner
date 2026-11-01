"""Regression tests for the recovered Python travel-agent application."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from mcp_client import extract_destination
from tools import backend
from tools.app import app


client = TestClient(app)


def test_python_health_starts_without_optional_api_keys(monkeypatch):
    for key in (
        "GROQ_API_KEY",
        "TAVILY_API_KEY",
        "AVIATIONSTACK_API_KEY",
        "OPENWEATHER_API_KEY",
        "DATABASE_URL",
    ):
        monkeypatch.delenv(key, raising=False)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["checkpoint_storage"].startswith("in-memory")


def test_python_home_serves_recovered_template():
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "TripMate" in response.text


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("Plan a 5-day trip from Delhi to Tokyo in April", "Tokyo"),
        ("I want to travel to Paris for a week", "Paris"),
        ("Plan a weekend stay in Kyoto with good food", "Kyoto"),
    ],
)
def test_extract_destination(query, expected):
    assert extract_destination(query) == expected


def test_extract_destination_does_not_guess_when_missing():
    assert extract_destination("Help me plan a nice holiday") == ""


class FakeGroq:
    """Deterministic LLM substitute; no external API key or network is used."""

    def invoke(self, messages):
        prompt = str(messages[-1].content)

        if "Determine whether the following request" in prompt:
            content = {"allowed": True, "reason": "Travel request"}
        elif "Choose only the specialist agents needed" in prompt:
            content = {
                "selected_agents": [
                    "flight_agent",
                    "hotel_agent",
                    "weather_agent",
                    "budget_agent",
                    "itinerary_agent",
                ],
                "trip_constraints": {
                    "destination": "Tokyo, Japan",
                    "origin": "Delhi, India",
                    "duration": "5 days",
                    "budget": "Moderate",
                    "travel_style": "Culture and food",
                    "special_preferences": [],
                },
                "reasoning": "All travel specialists are relevant.",
            }
        elif "You are a travel flight expert" in prompt:
            content = "Mock flight recommendations"
        elif "Analyze whether this trip is realistic" in prompt:
            content = "Mock budget assessment"
        elif "Create a complete travel itinerary" in prompt:
            content = "Mock draft itinerary"
        elif "Generate the final travel response" in prompt:
            content = "Mock finalized travel itinerary"
        else:
            content = "Mock specialist response"

        if isinstance(content, dict):
            content = json.dumps(content)
        return AIMessage(content=content)


@pytest.mark.parametrize("approved,feedback", [(True, ""), (False, "Add more vegetarian food options")])
def test_langgraph_workflow_draft_and_human_review(monkeypatch, approved, feedback):
    async def fake_aviation(tool_name, tool_args=None):
        return [{"name": "Mock airport or airline"}]

    async def fake_tavily(query):
        return "Mock hotel search results"

    async def fake_weather(city):
        return {"city": city, "temperature_c": 22}

    async def fake_forecast(city):
        return {"city": city, "forecast": []}

    monkeypatch.setattr(backend, "_get_llm", lambda: FakeGroq())
    monkeypatch.setattr(backend, "get_database_url", lambda: None)
    monkeypatch.setattr(backend, "aviation_mcp_call", fake_aviation)
    monkeypatch.setattr(backend, "tavily_mcp_search", fake_tavily)
    monkeypatch.setattr(backend, "weather_mcp_search", fake_weather)
    monkeypatch.setattr(backend, "forecast_mcp_search", fake_forecast)

    backend.close_resources()

    draft = backend.run_travel_agent(
        "Plan a 5-day trip from Delhi to Tokyo with a moderate budget."
    )

    assert draft["requires_approval"] is True
    assert draft["trip_constraints"]["destination"] == "Tokyo, Japan"
    assert draft["flight_results"] == "Mock flight recommendations"
    assert draft["hotel_results"] == "Mock hotel search results"
    assert "Mock draft itinerary" in draft["itinerary"]

    final = backend.resume_travel_agent(
        thread_id=draft["thread_id"],
        approved=approved,
        feedback=feedback,
    )

    assert final["requires_approval"] is False
    assert final["answer"] == "Mock finalized travel itinerary"
    assert final["thread_id"] == draft["thread_id"]

    backend.close_resources()
