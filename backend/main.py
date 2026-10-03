from pathlib import Path
from typing import Optional
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import tools
from graph import app_graph

app = FastAPI(title="Smart Trip Planner")

class PlanRequest(BaseModel):
    destination: Optional[str] = None
    origin: Optional[str] = "Chennai"
    start_date: Optional[str] = None
    days: Optional[int] = None
    budget: Optional[float] = None
    currency: str = "INR"
    travellers: int = 1

@app.post("/api/plan")
async def plan(r: PlanRequest):
    missing = {"destination": "Where would you like to go?", "start_date": "What is your start date?",
               "days": "How many days?", "budget": "What is your total budget?"}
    asks = [q for k, q in missing.items() if not getattr(r, k)]
    if asks:
        return {"needs_input": asks}
    dest_clean = r.destination.strip().lower() if r.destination else ""
    if dest_clean not in tools.ACTIVITIES:
        return {"needs_input": ["Supported destinations: " + ", ".join(c.title() for c in tools.ACTIVITIES) + "."]}
    
    req_dict = r.model_dump()
    req_dict["destination"] = dest_clean
    out = await app_graph.ainvoke({"req": req_dict, "replans": 0})
    return out["final"]

frontend_dir = Path(__file__).parent.parent / "frontend"
app.mount("/", StaticFiles(directory=frontend_dir, html=True))
