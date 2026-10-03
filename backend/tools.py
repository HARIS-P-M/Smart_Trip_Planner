"""Mock travel data + tool logic (exposed through the MCP server)."""
import json, urllib.request, urllib.parse
from datetime import date, timedelta

BASE_FARE = {
    "singapore": 24000,
    "bangkok": 20000,
    "munnar": 6500,
    "tokyo": 42000,
    "dubai": 22000,
    "paris": 48000,
    "bali": 25000,
    "goa": 5500,
}  # INR return, per person
FLIGHT_TYPES = [("BudgetJet", 1.0, "1 stop"), ("SkyConnect", 1.25, "non-stop"), ("Premium Air", 1.7, "non-stop")]
HOTELS = {
    "singapore": [
        ("Lion City Pod Hostel", 2800, 3.9, "budget"),
        ("Merlion Budget Inn", 4800, 4.0, "budget"),
        ("Orchard Central Suites", 9500, 4.3, "mid"),
        ("Marina Grand", 22000, 4.7, "luxury"),
    ],
    "bangkok": [
        ("Sukhumvit Backpackers", 1500, 3.8, "budget"),
        ("Riverside Comfort", 4200, 4.2, "mid"),
        ("Siam Palace Hotel", 12000, 4.6, "luxury"),
    ],
    "munnar": [
        ("Tea Valley Homestay", 1800, 4.1, "budget"),
        ("Mist Meadows Resort", 5500, 4.4, "mid"),
        ("Cloud9 Luxury Estate", 13000, 4.7, "luxury"),
    ],
    "tokyo": [
        ("Asakusa Pod Inn", 3200, 4.1, "budget"),
        ("Shinjuku Central Suites", 8500, 4.4, "mid"),
        ("Grand Hyatt Tokyo", 28000, 4.8, "luxury"),
    ],
    "dubai": [
        ("Deira Budget Lodge", 2500, 3.9, "budget"),
        ("Marina View Apartments", 7000, 4.3, "mid"),
        ("Burj Al Arab Suites", 32000, 4.9, "luxury"),
    ],
    "paris": [
        ("Montmartre Hostel", 3500, 4.0, "budget"),
        ("Hôtel Seine Central", 9800, 4.3, "mid"),
        ("Ritz Paris Luxury Villa", 35000, 4.9, "luxury"),
    ],
    "bali": [
        ("Ubud Tropical Hostel", 1600, 4.2, "budget"),
        ("Canggu Beach Villa", 4500, 4.5, "mid"),
        ("Ayana Resort & Spa", 18000, 4.8, "luxury"),
    ],
    "goa": [
        ("Anjuna Backpackers Nest", 1200, 4.0, "budget"),
        ("Candolim Beach Resort", 3800, 4.3, "mid"),
        ("Taj Exotica Resort & Spa", 15000, 4.8, "luxury"),
    ],
}
# (name, outdoor?, cost INR)
ACTIVITIES = {
    "singapore": [
        ("Gardens by the Bay light show", True, 1500),
        ("Merlion Park & Marina Bay walk", True, 0),
        ("ArtScience Museum", False, 2200),
        ("Chinatown & Maxwell hawker centre", True, 600),
        ("Singapore Zoo / River Wonders", True, 3800),
        ("Jewel Changi & Rain Vortex", False, 0),
        ("Sentosa Island day", True, 3000),
    ],
    "bangkok": [
        ("Grand Palace & Wat Pho", True, 1300),
        ("Chao Phraya river boat", True, 300),
        ("Jim Thompson House", False, 500),
        ("Chatuchak market", True, 0),
        ("Siam Paragon & aquarium", False, 1500),
    ],
    "munnar": [
        ("Tea Museum & plantation walk", False, 150),
        ("Eravikulam National Park", True, 500),
        ("Mattupetty Dam boating", True, 400),
        ("Top Station viewpoint", True, 0),
        ("Spice garden tour", True, 300),
    ],
    "tokyo": [
        ("Senso-ji Temple & Asakusa walk", True, 0),
        ("teamLab Planets immersive art", False, 2400),
        ("Shibuya Crossing & Hachiko Statue", True, 0),
        ("Tokyo Skytree observation deck", False, 1800),
        ("Meiji Shrine & Yoyogi Park", True, 0),
        ("Akihabara Tech & Anime Tour", False, 1200),
    ],
    "dubai": [
        ("Burj Khalifa 124th Floor Deck", False, 3800),
        ("Desert Safari with BBQ & Dunes", True, 2500),
        ("Dubai Mall & Fountain Show", False, 0),
        ("Gold Souk & Abra Creek Ride", True, 200),
        ("Museum of the Future", False, 3200),
        ("Jumeirah Beach Promenade", True, 0),
    ],
    "paris": [
        ("Eiffel Tower Summit Deck", True, 2800),
        ("Louvre Museum Guided Tour", False, 2200),
        ("Seine River Sunset Cruise", True, 1400),
        ("Musée d'Orsay Art Gallery", False, 1600),
        ("Notre-Dame & Latin Quarter Walk", True, 0),
        ("Palace of Versailles Day Trip", True, 2500),
    ],
    "bali": [
        ("Ubud Monkey Forest & Rice Terraces", True, 600),
        ("Tanah Lot Temple Sunset View", True, 400),
        ("Batur Volcano Sunrise Trek", True, 2500),
        ("Nusa Penida Island Day Tour", True, 3000),
        ("Balinese Traditional Spa", False, 1200),
        ("Seminyak Beach & Cafe Hopping", True, 500),
    ],
    "goa": [
        ("Baga & Calangute Beach Watersports", True, 1500),
        ("Old Goa Churches & Basilica of Bom Jesus", False, 0),
        ("Dudhsagar Waterfalls Jeep Safari", True, 2000),
        ("Mandovi River Sunset Cruise", True, 600),
        ("Panjim Fontainhas Heritage Walk", True, 0),
        ("Spice Plantation Tour & Buffet", True, 700),
    ],
}
FOOD_PER_DAY = {
    "singapore": 4500,
    "bangkok": 2500,
    "munnar": 1800,
    "tokyo": 5000,
    "dubai": 4000,
    "paris": 5500,
    "bali": 2200,
    "goa": 1600,
}   # food + local transport
COORDS = {
    "singapore": (1.35, 103.82),
    "bangkok": (13.75, 100.50),
    "munnar": (10.09, 77.06),
    "tokyo": (35.6762, 139.6503),
    "dubai": (25.2048, 55.2708),
    "paris": (48.8566, 2.3522),
    "bali": (-8.3405, 115.0920),
    "goa": (15.2993, 74.1240),
}
RATES_INR = {"INR": 1, "USD": 0.012, "EUR": 0.011, "SGD": 0.016, "THB": 0.40, "GBP": 0.0095}  # offline fallback

def search_flights(origin: str, destination: str, date: str) -> dict:
    base = BASE_FARE.get(destination.lower())
    if base is None:
        return {"results": []}
    return {
        "results": [
            {
                "airline": a,
                "route": f"{origin}-{destination}",
                "date": date,
                "stops": s,
                "price_inr": round(base * m, -2),
            }
            for a, m, s in FLIGHT_TYPES
        ]
    }

def search_hotels(city: str) -> dict:
    return {
        "results": [
            {"name": n, "price_per_night_inr": p, "rating": r, "tier": t}
            for n, p, r, t in HOTELS.get(city.lower(), [])
        ]
    }

def convert_currency(amount: float, from_cur: str, to_cur: str) -> dict:
    f, t = from_cur.upper(), to_cur.upper()
    if f == t:
        return {"amount": amount, "converted": amount, "rate": 1.0, "source": "identity"}
    try:
        url = "https://api.frankfurter.app/latest?" + urllib.parse.urlencode({"amount": amount, "from": f, "to": t})
        with urllib.request.urlopen(url, timeout=6) as r:
            d = json.load(r)
        return {"amount": amount, "converted": d["rates"][t], "rate": d["rates"][t] / amount if amount else 0.0, "source": "Frankfurter"}
    except Exception:
        rate = RATES_INR.get(t, 1.0) / RATES_INR.get(f, 1.0)
        return {"amount": amount, "converted": amount * rate, "rate": rate, "source": "offline fallback rates"}

def get_weather(city: str, start: str, days: int) -> dict:
    lat, lon = COORDS.get(city.lower(), (0, 0))
    try:
        s = date.fromisoformat(start)
        url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode({
            "latitude": lat,
            "longitude": lon,
            "timezone": "auto",
            "start_date": s.isoformat(),
            "end_date": (s + timedelta(days=days - 1)).isoformat(),
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        })
        with urllib.request.urlopen(url, timeout=6) as r:
            d = json.load(r)["daily"]
        return {
            "available": True,
            "days": [
                {
                    "date": d["time"][i],
                    "tmax": d["temperature_2m_max"][i],
                    "tmin": d["temperature_2m_min"][i],
                    "rain_pct": d["precipitation_probability_max"][i] or 0,
                }
                for i in range(len(d["time"]))
            ],
        }
    except Exception:
        return {"available": False, "days": []}  # beyond 16-day forecast window or offline
