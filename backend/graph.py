"""LangGraph planner-executor graph.
planner -> itinerary -> weather -> budget --(over budget)--> planner (re-plan)
                                         \\--(ok / max replans)--> summary"""
import asyncio, json, os, sys
from datetime import date, timedelta
from pathlib import Path
from typing import TypedDict
from langgraph.graph import StateGraph, END
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import rag, tools

HERE = Path(__file__).parent
TIERS = ["mid", "budget", "budget"]
FLIGHT_IDX = [1, 1, 0]
MAX_ACT = [10**9, 10**9, 1500]

class S(TypedDict, total=False):
    req: dict; replans: int; over: bool; plan: list; tier: str; flight_idx: int; max_act: int
    research: dict; days: list; weather: dict; cost: dict; final: dict

async def mcp_calls(calls):
    """Call MCP tools over one stdio session."""
    params = StdioServerParameters(command=sys.executable, args=[str(HERE / "mcp_server.py")])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            return [json.loads((await s.call_tool(n, a)).content[0].text) for n, a in calls]

def tavily(q):
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        return []
    from tavily import TavilyClient
    try:
        res = TavilyClient(api_key=key).search(q, max_results=4)["results"]
        return [{"title": x.get("title", "Advisory"), "url": x.get("url", "#"), "snippet": x.get("content", "")[:220]} for x in res]
    except Exception:
        return []

async def planner(s: S):
    r = s.get("replans", 0)
    steps = ["Research visa, events and guide", "Build day-by-day itinerary", "Check weather",
             "Price flights and hotels, check budget"]
    if r:
        steps.insert(0, f"Re-plan #{r}: cheaper flight/hotel tier after budget overrun")
    i = min(r, 2)
    return {"plan": steps, "tier": TIERS[i], "flight_idx": FLIGHT_IDX[i], "max_act": MAX_ACT[i]}

async def itinerary(s: S):
    q = s["req"]; city = q["destination"].lower()
    research = s.get("research")
    if not research:
        ev = await asyncio.to_thread(tavily, f"{q['destination']} festivals events closures travel advisory {q['start_date']}")
        visa_map = {"bangkok": "thailand", "singapore": "singapore", "munnar": "india", "goa": "india",
                    "tokyo": "japan", "dubai": "uae", "paris": "france", "bali": "indonesia"}
        vk = "visa " + visa_map.get(city, city)
        research = {"visa": rag.search(vk)[0], "guide": rag.search("guide " + city)[0],
                    "insurance": rag.search("travel insurance")[0], "events": ev}
    all_acts = tools.ACTIVITIES.get(city, [])
    acts = [a for a in all_acts if a[2] <= s["max_act"]] or all_acts
    start = date.fromisoformat(q["start_date"]); days = []
    for i in range(q["days"]):
        picks = [acts[(2 * i + j) % len(acts)] for j in range(2)] if acts else []
        days.append({"day": i + 1, "date": (start + timedelta(days=i)).isoformat(),
                     "items": [{"name": n, "outdoor": o, "cost_inr": c} for n, o, c in picks]})
    return {"research": research, "days": days}

async def weather(s: S):
    q = s["req"]
    w = (await mcp_calls([("get_weather", {"city": q["destination"], "start": q["start_date"], "days": q["days"]})]))[0]
    days = s["days"]
    if w["available"]:
        indoor = [a for a in tools.ACTIVITIES.get(q["destination"].lower(), []) if not a[1]]
        for d, f in zip(days, w["days"]):
            d["weather"] = f
            if f["rain_pct"] >= 60:
                for it in d["items"]:
                    if it["outdoor"]:
                        alt = next((a for a in indoor if a[0] not in [x["name"] for x in d["items"]]), None)
                        if alt:
                            orig_name = it["name"]
                            it.update(note=f"Rain likely: swapped from {orig_name}", name=alt[0], outdoor=False, cost_inr=alt[2])
                        else:
                            it["note"] = "Rain likely: go early or carry rain gear"
    return {"weather": w, "days": days}

async def budget(s: S):
    q = s["req"]; city = q["destination"].lower(); cur = q["currency"].upper(); n = q["days"]
    fl, ho, fx, bd = await mcp_calls([
        ("search_flights", {"origin": q["origin"], "destination": city, "date": q["start_date"]}),
        ("search_hotels", {"city": city}),
        ("convert_currency", {"amount": 1, "from_cur": "INR", "to_cur": cur}),
        ("convert_currency", {"amount": q["budget"], "from_cur": cur, "to_cur": "INR"})])
    flight_options = fl.get("results", [])
    flight_idx = min(s["flight_idx"], len(flight_options) - 1) if flight_options else 0
    flight = flight_options[flight_idx] if flight_options else {"airline": "Standard Air", "stops": "direct", "price_inr": 15000}
    
    hotel_options = ho.get("results", [])
    matching_hotels = [h for h in hotel_options if h["tier"] == s["tier"]]
    hotel = max(matching_hotels or hotel_options or [{"name": "Standard Hotel", "price_per_night_inr": 3000, "rating": 4.0, "tier": "budget"}], key=lambda h: h["rating"])
    
    pax = q.get("travellers", 1)
    parts = {"Flights": flight["price_inr"] * pax,
             "Hotel": hotel["price_per_night_inr"] * max(n - 1, 1) * ((pax + 1) // 2),
             "Activities": sum(i["cost_inr"] for d in s["days"] for i in d["items"]) * pax,
             "Food & local transport": tools.FOOD_PER_DAY.get(city, 2500) * n * pax,
             "Insurance (estimate)": 800 * pax}
    total = sum(parts.values()); limit = bd["converted"]
    cheaper = [h for h in hotel_options if h["price_per_night_inr"] < hotel["price_per_night_inr"]]
    out = {"cost": {"parts_inr": parts, "total_inr": total, "limit_inr": limit, "rate": fx["rate"], "currency": cur,
                    "fx_source": fx["source"], "flight": flight, "hotel": hotel, "cheaper_hotels": cheaper}}
    if total > limit and s.get("replans", 0) < 2:
        out.update(over=True, replans=s.get("replans", 0) + 1)
    else:
        out["over"] = False
    return out

def route(s: S):
    return "planner" if s.get("over") else "summary"

async def summary(s: S):
    q, c, r = s["req"], s["cost"], s["research"]; rate = c["rate"]
    conv = lambda v: round(v * rate, 2)
    ok = c["total_inr"] <= c["limit_inr"]
    final = {
        "title": f"{q['days']}-day trip to {q['destination'].title()}",
        "within_budget": ok, "replans": s.get("replans", 0), "plan": s["plan"],
        "itinerary": s["days"], "weather_available": s["weather"]["available"],
        "cost": {"currency": c["currency"], "total": conv(c["total_inr"]), "budget": q["budget"],
                 "parts": {k: conv(v) for k, v in c["parts_inr"].items()}, "fx_source": c["fx_source"]},
        "flight": c["flight"], "hotel": c["hotel"],
        "cheaper_hotels": [{**h, "price_converted": conv(h["price_per_night_inr"])} for h in c["cheaper_hotels"]],
        "visa": r["visa"], "insurance": r["insurance"], "guide": r["guide"], "advisories": r["events"],
        "disclaimers": ["All prices are indicative (mock flight/hotel data) and may change; confirm before booking.",
                        "Visa rules change often: verify on the official embassy or government site cited above.",
                        "Check local advisories before departure."]}
    if not ok:
        final["warning"] = "Even after re-planning, the estimate exceeds your budget. Consider fewer days or a nearer destination."
    return {"final": final}

g = StateGraph(S)
for name, fn in [("planner", planner), ("itinerary", itinerary), ("weather", weather), ("budget", budget), ("summary", summary)]:
    g.add_node(name, fn)
g.set_entry_point("planner")
g.add_edge("planner", "itinerary"); g.add_edge("itinerary", "weather"); g.add_edge("weather", "budget")
g.add_conditional_edges("budget", route, {"planner": "planner", "summary": "summary"})
g.add_edge("summary", END)
app_graph = g.compile()
