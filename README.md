# TinyWorld 🌍

An autonomous world simulation where entities make their own decisions and interact with their environment.

## Next Steps for v1

1. Create world simulation loop (tick at 15-30 Hz)
2. Add basic Entity class (position, velocity, id)
3. Implement simple wander AI (random direction changes)
4. Set up WebSocket for state broadcasting
5. Create REST endpoint for spawning entities
6. Build PixiJS canvas and connection to WebSocket
7. Render entities as simple circles
8. Add click interaction (push/influence entities)
9. Implement smooth interpolation between server updates
10. Add basic action system (move, idle, interact)

## Tech Stack

**Backend:** FastAPI (Python) with WebSockets  
**Frontend:** PixiJS with TypeScript  
**Dev:** uv (Python), Vite (Web), Docker Compose  

## Quick Start

```bash
# Backend
cd api && uv sync && uv run uvicorn src.main:app --reload

# Frontend  
cd web && yarn install && yarn dev

# Or both
make dev
```

## Contributing

See [CONTRIBUTING.md](https://docs.github.com/en/pull-requests/
collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/
creating-a-pull-request-from-a-fork) for guidelines.

## Issues & Support

- **Bug Reports:** [Open an issue](https://github.com/ThoBustos/tinyworld/issues/new)
- **Feature Requests:** [Request a feature](https://github.com/ThoBustos/tinyworld/issues/new)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**MIT License Summary:** You can freely use, modify, and distribute this software with proper attribution.
