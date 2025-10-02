# TinyWorld API

FastAPI backend for the TinyWorld simulation.

## Setup from Scratch

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (Python package manager)

### Install uv
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```

### Install Dependencies
```bash
# From the tinyworld-backend directory
cd tinyworld-backend

# Install all dependencies
uv sync

# This creates a virtual environment and installs packages from pyproject.toml
```

### Run Development Server
```bash
# Start the FastAPI server with auto-reload
uv run python -m uvicorn tinyworld.main:app --reload --host 0.0.0.0 --port 8000

# Or run the module directly (if it has a main block)
uv run python -m tinyworld.main
```

### Environment Variables
Copy `.env.example` to `.env` and adjust as needed:
```bash
cp .env.example .env
```

## Project Structure
```
tinyworld-backend/
├── src/
│   └── tinyworld/
│       ├── __init__.py
│       ├── main.py             # FastAPI app entry point
│       ├── agents/             # AI agent implementations
│       │   ├── character_workflow.py
│       │   ├── chat_agent.py
│       │   └── socrates.py
│       ├── api/                # API routes
│       ├── core/               # Core configuration
│       ├── models/             # Data models
│       ├── repositories/       # Data repositories
│       └── services/           # Business logic
├── docs/                       # Documentation
├── pyproject.toml             # Project dependencies
├── uv.lock                    # Lock file
└── .env                       # Environment variables (create from .env.example)
```

## API Endpoints
- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /agent/state` - Get current agent state
- `WebSocket /ws` - WebSocket connection for real-time updates

## Development
```bash
# Run tests
uv run pytest

# Format code
uv run ruff format .

# Lint code  
uv run ruff check .
```