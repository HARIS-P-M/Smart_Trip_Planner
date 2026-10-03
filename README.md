# 🌍 Smart Trip Planner — Autonomous Multi-Agent Travel Engine

An intelligent, multi-agent travel planning platform that generates budget-checked, day-by-day itineraries tailored to weather forecasts, visa rules, live events, and real-time currency conversions.

Built with **FastAPI**, **LangGraph**, **Model Context Protocol (MCP)**, **Open-Meteo**, and **Frankfurter API**.

---

## 🌟 Key Features

- 🧠 **Multi-Agent LangGraph Pipeline**: Coordinated execution between **Planner**, **Itinerary**, **Weather**, **Budget**, and **Summary** agents.
- 🔁 **Automatic Budget Re-Planning**: Intelligent loop that automatically re-evaluates and optimizes flight/hotel tiers up to 2 times if total expenses exceed the target budget.
- 🌧️ **Dynamic Weather Adaptation**: Queries live Open-Meteo 16-day forecasts and dynamically swaps outdoor activities for indoor alternatives when rain probability exceeds 60%.
- 💱 **Multi-Currency Budgeting**: Converts costs in real-time between **INR**, **USD**, **EUR**, **SGD**, **THB**, and **GBP** using the Frankfurter API (with offline fallbacks).
- 📜 **RAG Knowledge Retrieval**: Keyword RAG system for official visa rules, travel insurance guidelines, and city guides.
- 📰 **Live Advisories**: Fetches real-time festivals, closures, and advisories using Tavily Web Search.
- 🏨 **Alternative Cheaper Hotel Suggestions**: Automatically surfaces lower-cost accommodation options to help users save money.

---

## 🗺️ Supported Destinations

| Destination | Country | Flag | Type |
| :--- | :--- | :---: | :--- |
| **Singapore** | Singapore | 🇸🇬 | International |
| **Bangkok** | Thailand | 🇹🇭 | International |
| **Tokyo** | Japan | 🇯🇵 | International |
| **Dubai** | UAE | 🇦🇪 | International |
| **Paris** | France | 🇫🇷 | International |
| **Bali** | Indonesia | 🇮🇩 | International |
| **Munnar** | India | 🇮🇳 | Domestic |
| **Goa** | India | 🇮🇳 | Domestic |

---

## 🏗️ Multi-Agent Architecture

```
                 +-----------------------+
                 |     User Request      |
                 +-----------+-----------+
                             |
                             v
                 +-----------------------+
                 |     Planner Node      | <---+
                 +-----------+-----------+     |
                             |                 | (Re-plan if over budget,
                             v                 |  max 2 replan attempts)
                 +-----------------------+     |
                 |    Itinerary Node     |     |
                 |  (RAG + Tavily Live)  |     |
                 +-----------+-----------+     |
                             |                 |
                             v                 |
                 +-----------------------+     |
                 |     Weather Node      |     |
                 | (Open-Meteo Forecast) |     |
                 +-----------+-----------+     |
                             |                 |
                             v                 |
                 +-----------------------+     |
                 |      Budget Node      | ----+
                 |   (MCP Tools & FX)    |
                 +-----------+-----------+
                             |
                   (Within Budget / Max Replans)
                             |
                             v
                 +-----------------------+
                 |     Summary Node      |
                 +-----------+-----------+
                             |
                             v
                 +-----------------------+
                 | Final Plan Response   |
                 +-----------------------+
```

---

## 🛠️ Model Context Protocol (MCP) Tools

The backend runs a dedicated MCP server ([mcp_server.py](file:///d:/Agentic%20Ai/backend/mcp_server.py)) over stdio exposing the following tools:

- `search_flights(origin, destination, date)`: Searches mock flight availability and prices across airlines.
- `search_hotels(city)`: Searches hotels categorized by tier (budget, mid, luxury) with star ratings.
- `convert_currency(amount, from_cur, to_cur)`: Real-time currency exchange rates via Frankfurter API.
- `get_weather(city, start, days)`: Fetches daily weather metrics (min/max temp & rain probability) via Open-Meteo API.

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables (Optional)
Copy `.env.example` to `.env` if you wish to enable live event searches via Tavily:
```bash
cp .env.example .env
```
Inside `.env`:
```env
TAVILY_API_KEY=your_tavily_api_key_here
```

### 3. Start Server
Navigate to the `backend` directory and run Uvicorn:
```bash
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 4. Access the Application
Open your browser and visit:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 📁 Repository Structure

```
├── backend/
│   ├── main.py          # FastAPI application & static file router
│   ├── graph.py         # LangGraph state machine & multi-agent nodes
│   ├── mcp_server.py    # FastMCP server definition
│   ├── tools.py         # Travel data providers & external API integrations
│   ├── rag.py           # Knowledge base retrieval engine
│   └── kb.md            # Visa, destination, and travel insurance knowledge base
├── frontend/
│   └── index.html       # Glassmorphism dark mode web interface
├── requirements.txt     # Python dependencies
└── README.md            # Documentation
```

---

## 🛡️ Disclaimers & Safety

1. **Indicative Pricing**: All flight and hotel rates are simulated or estimated; users should confirm final prices on official booking portals prior to travel.
2. **Visa Policies**: Visa rules and entry requirements change frequently. Users are advised to double-check official embassy portals cited in the guidelines.
