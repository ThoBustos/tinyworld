# TinyWorld 🌍

An autonomous world simulation where entities make their own decisions and interact with their environment.

V1 video: https://www.loom.com/share/605e16304a684147a3e9ad833af71594
V2 video: https://www.loom.com/share/9d698b2b20074b9b9fa9776661c923c3

## Next Steps for v1

1. Create moodboard in midjourney for assets ✅
2. Reuse philo agents assets (town map and characters) ✅
3. Camera follow the character in the map ✅
4. Create the first agentic action - speaking and reflecting ✅
5. Clean the codebase for continuous reflection and thinking only ✅
6. Add opik to the codebase ✅
7. Have character speaking every 30s ✅
8. Have the character prompt in codebase for now. Later in postgre db when we add more characters. The main prompt should be the mission of the character and his memory. He need to continuously think and reflect on his mission and his memory to find his purpose, identity and what is the next action he can take to achieve to raise his consciousness. Currently have short term memory not persistent ✅
[@prompts.py @socrates.py 
let's create something simpler. the first prompt pass is for you to reflect. the prompt have: last 10 messages (short term memory). Use last message to trigger vector store (if last message) sto access older memory.
add in this same first prompt the goal of the current character.  mission of the charactermission of the character and his memory. He need to continuously think and reflect on his mission and his memory to find his purpose, identity and what is the next action he can take to achieve to raise his consciousness. how to find new actions to gather mmore informatinos. speaking to other humans, seeing the env. each reflection must build up on previous actions. he must take decisions, actinos, stay consistent and develop a belief system. everytime he/she has a new idea, do something new, see something new, learn something, believe something we store in collection.] ✅
PENDING TO ADD LAST 10 messages filtering vector db by timestamp (add recent memory) and generate memories/belief system. ✅
9. Added vision to the character. ✅
10. Added simple movements with vision. ✅
11. Add belief system and learnings of what's possible to do. ✅
<!-- 9. Add database for multiple characters. -->
<!-- 10. Plan for next steps tinyworld (more actions, more characters) -->

## Things I want to try:
- Devin
- Claude in github
- Amp

## Pool of ideas:
- Environmental Awareness - Give characters "eyes" by adding environment info to prompts (town square, fountain, buildings, pathways) so they reference specific locations in thoughts
- Movement Intent - Characters express desire to move/explore in their thoughts, triggering actual walking animations toward random nearby locations
- Time-of-Day Responses - Simple day/night cycle affects character thoughts ("As dawn breaks..." vs "In this twilight hour...") for natural variety

- Each character have a life. Eating and sleeping recharge your life. Socializing recharge your life. Monsters can attack you. You can attack monsters. Get protections. Get money. Steel. Craft. Have ideas. Mentor. Help. 
- use api to adjust the weather, night/day
- Random Events: Festivals, plagues, migrating animals, visiting philosophers.
- Economy
- each person have
- Gerdening
- Construiction projects
- Villagers each get a simple daily goal (eat, build, socialize), and their choices ripple into others’ routines.
- Goals clash or align, creating tiny dramas: two chase the same chicken, or three cooperate to build a bench.
- The town has shared rituals (sunset gathering, morning chores) that give structure but let individuality play out.
- Over time, villagers remember outcomes (who helped, who stole, who ignored) and adjust how they treat others.
- Simple status effects (happy, tired, jealous, proud) change how goals are pursued and make their stories visible.
- When enough villagers act alike, the whole town shifts (more gardens, more pranks, more late-night parties).
- Viewers can nudge events by spawning new characters or items, watching how the system absorbs the change.
- Small, unexpected emergent traditions form—like everyone gathering around the pond if one villager keeps playing music there.
Hidden Role Mystery → one villager is secretly bad (killer/thief), detective & gossip slowly reveal clues.
- Town Elections → villagers vote in cycles, leaders set rules that shift the world vibe.
- Secret Prankster → a hidden trouble-maker disrupts the town with small acts, others speculate and accuse.
- Chaos Cards → random global rules flip in (e.g., everyone lies, sudden dance law).
- Mini Quests → townsfolk work together on small mysteries, leading to visible new props or events.

♾️ Infinite/Evolving Systems
- Culture Drift → sayings, habits, and rituals spread between villagers, mutate, and become traditions over time.
- Faction Growth → cliques form around shared traits or moods, and compete subtly for influence in the town.
- Rumor Webs → stories circulate, evolve, and gain followers, creating shifting “truths” in the world.
- Generational Memory → villagers pass down ideas or roles to newcomers, creating evolving lineage dynamics.
- Town Projects → cooperative building/decorating keeps layering the map with new benches, gardens, monuments endlessly.

Another idea:
- the villagers don't have memory. They meet. They can talk and remember. And they need to find meaning and do things. They are aware of the space. At the start they don't have any idea of who is who but they develop a sense of others. They have a need for beeing social but they form relationship closer than other. there are very real situations while they figure out their purpose. They can agree on times and places to meet. They create rules and assign roles to maintain order. they can judge. Kill if more than 3 agree. If someone just arrived and some people have been their for a long time, the older can explain the rules and what they currently know. And what they don't know. They are all aware that it's a mistery on why they are in this closed tiny world.

## Tech Stack

**Backend:** FastAPI (Python) with WebSockets  
**Frontend:** PixiJS with TypeScript  
**Dev:** uv (Python), Vite (Web), Docker Compose  

## Prerequisites

- Python 3.11+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- Yarn (for frontend)

### Install uv
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```

## Quick Start

```bash
# Backend
cd tinyworld-backend
uv sync
uv run python -m uvicorn tinyworld.main:app --reload --host 0.0.0.0 --port 8000

# Frontend  
cd tinyworld-web
yarn install
yarn dev

# Or both with Docker Compose
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
