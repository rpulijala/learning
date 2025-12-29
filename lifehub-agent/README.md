# LifeHub Agent

AI assistant with LangGraph orchestration, FastAPI backend, and tool support.

## Features

- **Chat API**: Streaming `/chat` endpoint for conversational AI
- **Weather Tool**: Get weather information for any city (dummy data for now)
- **Task Management**: Add tasks to a local JSON file

## Project Structure

```
lifehub-agent/
├── backend/
│   ├── app/
│   │   └── main.py          # FastAPI app + /chat endpoint
│   ├── agents/
│   │   └── graph.py         # LangGraph agent with tools
│   ├── tools/
│   │   ├── weather.py       # get_weather() tool
│   │   └── tasks.py         # add_task() tool
│   ├── models.py            # OpenAI + Ollama clients
│   └── state/               # Persistence (tasks.json)
└── pyproject.toml           # Dependencies (uv)
```

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- OpenAI API key

### Installation

```bash
# Install dependencies
uv sync

# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
```

## Running the Server

```bash
# Using uv
uv run uvicorn backend.app.main:app --reload --port 8000

# Or directly with Python
uv run python -m backend.app.main
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/
```

### Chat (Streaming)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "What is the weather in Tokyo?"}]}'
```

### Chat (Non-streaming)
```bash
curl -X POST http://localhost:8000/chat/sync \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Add a task: Buy groceries"}]}'
```

## Example Requests

### Get Weather
```bash
curl -X POST http://localhost:8000/chat/sync \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "What is the weather in New York?"}]}'
```

### Add Task
```bash
curl -X POST http://localhost:8000/chat/sync \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Add a task to call mom tomorrow"}]}'
```

### General Chat
```bash
curl -X POST http://localhost:8000/chat/sync \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello, who are you?"}]}'
```

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest
```

## License

MIT
