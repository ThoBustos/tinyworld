# Contributing to TinyWorld

Thanks for your interest in contributing! This is a learning project and we welcome all contributions.

## Ways to Contribute

- **Bug fixes** - Found something broken? Fix it!
- **Features** - Add new character behaviors, UI improvements, or world features
- **Documentation** - Clarify setup instructions, add code comments
- **Performance** - Optimize the simulation or rendering
- **Testing** - Add tests to ensure stability

## Getting Started

1. **Fork the repo** and create your branch from `main`
2. **Install dependencies** for the parts you're working on (see README)
3. **Make your changes** and test them locally
4. **Follow the style** - match existing code patterns
5. **Commit with clear messages** describing what changed
6. **Push to your fork** and submit a pull request

## Development Setup

```bash
# Backend
cd api
uv sync
uv run uvicorn src.main:app --reload

# Frontend
cd web  
npm install
npm run dev
```

## Code Style

### Python (Backend)
- Use `ruff` for formatting: `uv run ruff format .`
- Type hints where helpful
- Clear variable names

### TypeScript (Frontend)
- Strict mode enabled
- Prefer `const` over `let`
- Use async/await over callbacks

## Pull Request Process

1. **Update the README** if you change setup steps or add features
2. **Test your changes** - ensure both backend and frontend still work
3. **Keep PRs focused** - one feature or fix per PR
4. **Be patient** - reviews may take time

## Questions?

Open an issue for discussion before making large changes.

Let's build something fun together! 🎮