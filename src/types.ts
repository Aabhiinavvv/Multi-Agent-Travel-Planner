export interface TripConstraints {
  destination: string;
  origin: string;
  duration: string;
  budget: string;
  travel_style: string;
  special_preferences: string[];
}

export type AgentName =
  | 'flight_agent'
  | 'hotel_agent'
  | 'weather_agent'
  | 'budget_agent'
  | 'itinerary_agent';

export interface TravelWorkflowData {
  guardrail_allowed: boolean;
  guardrail_reason?: string;
  selected_agents: AgentName[];
  trip_constraints: TripConstraints;
  supervisor_reasoning: string;
}

export interface TravelResponse extends TravelWorkflowData {
  success: boolean;
  error?: string;
  thread_id: string;
  user_query: string;
  requires_approval: boolean;
  approval_request?: string;
  answer?: string;
  flight_results?: string;
  hotel_results?: string;
  weather_results?: string;
  budget_results?: string;
  itinerary?: string;
  timestamp?: number;
}

export interface SavedTrip {
  id: string;
  thread_id: string;
  title: string;
  destination: string;
  user_query: string;
  answer: string;
  flight_results: string;
  hotel_results: string;
  weather_results: string;
  budget_results: string;
  itinerary: string;
  selected_agents: AgentName[];
  supervisor_reasoning: string;
  created_at: number;
}
