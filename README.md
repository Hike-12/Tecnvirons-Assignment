# Technivirons AI Backend

A production-quality asynchronous Python backend for a realtime AI conversational session.

## Tech Stack

- **Python 3.10+**
- **FastAPI**: High-performance web framework.
- **WebSockets**: For realtime bidirectional communication.
- **Supabase (Postgres)**: For persistence of sessions and events.
- **Groq API**: For LLM interaction with streaming and tool calling (using Llama 3).

## Setup Instructions

### 1. Environment Setup

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

- `SUPABASE_URL`: Your Supabase project URL.
- `SUPABASE_KEY`: Your Supabase service_role or anon key (service_role preferred for backend).
- `GROQ_API_KEY`: Your Groq API key.

### 3. Database Schema

Run the SQL commands found in `schema.sql` in your Supabase SQL Editor to create the necessary tables (`sessions`, `session_events`).

## Running the Server

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

The server will start at `http://localhost:8000`.

## Testing

1. Open your browser and navigate to `http://localhost:8000`.
2. Click "Connect" to establish a WebSocket connection.
3. Type a message and hit Send.
4. To test tool calling, ask: "Can you fetch the profile for user 123?"

## Design Decisions

- **Async Architecture**: Used `asyncio` throughout to handle multiple WebSocket connections concurrently without blocking.
- **Streaming**: LLM responses are streamed token-by-token to the client for low latency.
- **Tool Calling**: Implemented a loop in the WebSocket handler to support tool execution. The LLM can pause generation, request a tool, and the backend executes it and feeds the result back.
- **Persistence**: All events (messages, tool calls) are logged to Supabase asynchronously.
- **Background Tasks**: Session summarization happens in the background after the WebSocket disconnects, ensuring the user experience isn't impacted by cleanup tasks.
- **Separation of Concerns**: Logic is split into `routers` (transport), `services` (business logic), and `database` (persistence).
"# Hike-12" 
