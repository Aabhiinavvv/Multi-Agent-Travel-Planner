from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights
res = search_flights("plan a 7 days nepal trip from bangladesh ")
from tools.backend import run_travel_agent

#res = run_travel_agent



#print(res)


user_input = input("enter ypur inout")
response = run_travel_agent(
    user_input = user_input,

)

print("\n final response :\n")
print(response['answer'])
