# TripMate AI — Multi-Agent Travel Planner

TripMate AI is an intelligent travel planning platform powered by multi-agent coordination, input guardrails, and human-in-the-loop review.

## Architecture & Features

- **Supervisor Agent & Input Guardrails**:
  - Validates travel requests and blocks off-topic inquiries.
  - Dynamically activates relevant specialist agents.
  - Extracts trip constraints (destination, duration, budget, travel style, special preferences).
- **Specialist Multi-Agent Team**:
  - ✈️ **Flight Agent**: Airport identification, route options, airfare estimations, and booking tips.
  - 🏨 **Hotel Agent**: Curated accommodations across budget, boutique, and luxury tiers with neighborhood recommendations.
  - 🌦️ **Weather Agent**: Seasonal climate insights, precipitation chances, and packing checklist.
  - 💰 **Budget Agent**: Itemized expense breakdown and money-saving guidance.
  - 🗓️ **Itinerary Agent**: Cohesive day-by-day plan with morning, afternoon, and evening activities.
- **Human-in-the-Loop (HITL)**:
  - Generates an interactive draft for user review.
  - Approves plan to finalize or incorporates revision feedback.
- **User Experience**:
  - Saved trip history in local storage.
  - Print / PDF export ready.
  - Copy to clipboard.
  - Responsive, dark-mode glassmorphic interface.

## Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```
