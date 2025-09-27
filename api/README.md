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
# From the api directory
cd api

# Install all dependencies
uv sync

# This creates a virtual environment and installs packages from pyproject.toml
```

### Run Development Server
```bash
# Start the FastAPI server with auto-reload
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or use the shorthand (once main.py exists)
uv run python -m src.main
```

### Environment Variables
Copy `.env.example` to `.env` and adjust as needed:
```bash
cp .env.example .env
```

## Project Structure
```
api/
├── src/
│   ├── main.py         # FastAPI app entry point
│   ├── world.py        # World simulation logic
│   ├── models.py       # Pydantic models
│   └── ai.py          # Character AI behaviors
├── pyproject.toml      # Project dependencies
└── .env               # Environment variables (create from .env.example)
```

## API Endpoints (planned)
- `GET /health` - Health check
- `POST /action` - Send actions to the world
- `WS /ws` - WebSocket for real-time updates

## Development
```bash
# Run tests
uv run pytest

# Format code
uv run ruff format .

# Lint code  
uv run ruff check .
```