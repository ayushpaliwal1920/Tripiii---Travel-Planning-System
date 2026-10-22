# Tripiii Travel Planning System

Tripiii is an AI-assisted travel planner with a browser-based interface. Describe a trip in plain language to get flight information, hotel suggestions, and a day-by-day itinerary in one response.

## Features

- Searches flight information through AviationStack.
- Finds hotel information using Tavily web search.
- Creates a practical itinerary and final trip summary with Groq.
- Coordinates travel-planning steps with a LangGraph workflow.
- Saves workflow checkpoints in PostgreSQL so a conversation can continue with its thread ID.
- Provides a responsive web interface with quick prompts, copy-to-clipboard, and PDF export.

Flight availability and prices depend on the flight provider; a generated plan is a starting point, not a booking or price guarantee.

## How it works

The FastAPI application serves the page and accepts travel requests. LangGraph runs the workflow in sequence:

1. The flight step looks up flight information for the requested route.
2. The hotel step searches the web for suitable stays.
3. The itinerary step uses Groq to combine the trip details into a day-by-day plan.
4. The final step prepares a formatted trip summary.

The frontend sends requests to the API and keeps the returned thread ID in browser local storage for subsequent requests.

## Requirements

- Python 3.12 or later.
- A PostgreSQL database reachable by the application, with SSL connections supported.
- API credentials for Groq, Tavily, and AviationStack.

## Setup

From the project root, create and activate a virtual environment, then install the pinned dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

On macOS or Linux, create and activate the environment with:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create a `.env` file in the project root and set your provider credentials and PostgreSQL connection string:

```dotenv
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
AVIATIONSTACK_API_KEY=your_aviationstack_api_key
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require
```

Replace the example values with your own credentials. Do not commit `.env` or share its contents. The application requires `GROQ_API_KEY` and `DATABASE_URL` to start; Tavily and AviationStack credentials are needed for hotel search and flight lookup, respectively. The backend sets up LangGraph's PostgreSQL checkpoint tables when it starts, so the database user must be permitted to create and use them.

Optionally, set `DEFAULT_ORIGIN_DATA` in `.env` to a default origin used when a request does not specify one:

```dotenv
DEFAULT_ORIGIN_DATA=Dhaka, Bangladesh
```

## Run the application

With the virtual environment active and `.env` configured, start the development server from the project root:

```sh
python -m uvicorn app:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). FastAPI's interactive API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs), and the health endpoint is [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health).

## API

`POST /api/travel` accepts a travel request and an optional thread ID:

```json
{
  "message": "Plan a 7-day trip to Japan from Bangladesh on a budget",
  "thread_id": null
}
```

The response includes `success`, `thread_id`, `answer`, `flight_results`, `hotel_results`, `itinerary`, and `llm_calls`. Send the returned `thread_id` with a later request to continue using the same LangGraph checkpoint thread.

## Project layout

```text
.
├── app.py                 # FastAPI routes and application startup
├── backend.py             # LangGraph travel workflow and PostgreSQL checkpointer
├── tools/
│   ├── flight_tool.py     # AviationStack flight lookup and route parsing
│   └── tavily_tool.py     # Tavily hotel/web search
├── templates/
│   └── index.html         # Browser interface
├── static/
│   ├── script.js          # API calls and frontend interactions
│   └── style.css          # Interface styles
├── requirements.txt       # Pinned Python dependencies
└── test.py                # Interactive manual test script
```

## Manual test script

`test.py` prompts for a travel request and calls the workflow directly:

```sh
python test.py
```

It requires the same `.env` credentials and PostgreSQL access as the web application.
`