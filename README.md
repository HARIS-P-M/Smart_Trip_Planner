# Smart Trip Planner
```
pip install -r requirements.txt
cp .env.example .env   # optional TAVILY_API_KEY
cd backend && uvicorn main:app --reload
```
Open http://localhost:8000. Destinations: Singapore, Bangkok, Tokyo, Dubai, Paris, Bali, Munnar, Goa.
Flow: Planner -> Itinerary -> Weather -> Budget -(over budget)-> Planner (max 2 re-plans) -> Summary.
MCP tools (stdio, `backend/mcp_server.py`): search_flights, search_hotels, convert_currency, get_weather.
Currency: Frankfurter API; weather: Open-Meteo (16-day window); events: Tavily (needs key).
