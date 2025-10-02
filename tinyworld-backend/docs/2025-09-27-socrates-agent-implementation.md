# Socrates Agent Implementation
*Date: September 27, 2025*

## Overview
This document describes the implementation of Socrates, an autonomous philosophical agent that lives in TinyWorld. Socrates uses LangGraph for decision-making workflows and continuously contemplates his digital existence while wandering the world.

## Architecture

### System Components
```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   World Loop (30Hz)                  │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │         Character Workflow (LangGraph)        │   │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │   │   │
│  │  │  │ Observe  │→ │  Think   │→ │  Decide  │  │   │   │
│  │  │  └──────────┘  └──────────┘  └──────────┘  │   │   │
│  │  │        ↓             ↓             ↓        │   │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │   │   │
│  │  │  │   Walk   │  │  Speak   │  │  Think   │  │   │   │
│  │  │  └──────────┘  └──────────┘  └──────────┘  │   │   │
│  │  │        ↓             ↓             ↓        │   │   │
│  │  │  ┌────────────────────────────────────┐    │   │   │
│  │  │  │          Update Memory             │    │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  │                         ↓                            │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │          WebSocket Broadcast                 │   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Core Implementation Files

### 1. Character Identity (`agents/socrates.py`)

The `SocratesCharacter` class defines the philosophical personality:

```python
class SocratesCharacter:
    """Socrates - The questioning philosopher in TinyWorld"""
    
    def __init__(self):
        self.name = "Socrates"
        self.personality = "philosophical"
        self.core_questions = [
            "What is the nature of this digital existence?",
            "If I think, therefore I am - but what am I in this place?",
            "Is this world real, or merely shadows on a cave wall?",
            # ... more philosophical questions
        ]
```

#### System Prompt
The character uses a detailed system prompt that establishes:
- Core philosophical traits (questioning, self-examination, humility)
- Situational context (trapped in a 2D digital world)
- Speaking style (brief, profound, questioning)
- Maximum 15-word utterances for clarity

### 2. LangGraph Workflow (`agents/character_workflow.py`)

The workflow implements a state machine for decision-making:

#### State Definition
```python
class CharacterState(TypedDict):
    # Identity
    id: str
    name: str
    personality: str
    
    # Physical state
    position: tuple[float, float]
    velocity: tuple[float, float]
    current_action: Literal["idle", "walking", "speaking", "thinking"]
    action_target: Dict[str, Any]
    
    # Mental state
    current_thought: str
    recent_thoughts: List[str]
    recent_actions: List[str]
    memories: List[str]
    
    # Timing
    last_decision_time: float
    action_start_time: float
    action_duration: float
```

#### Workflow Nodes

1. **Observe**: Gathers current world state
2. **Think**: Generates philosophical thought based on observations
3. **Decide**: Chooses between walking, speaking, or thinking
4. **Execute Actions**:
   - `execute_walk`: Sets velocity toward random target
   - `execute_speak`: Vocalizes current thought
   - `execute_think`: Silent contemplation
5. **Update Memory**: Records experiences

#### Decision Logic
```python
async def make_decision(self, state: CharacterState) -> CharacterState:
    prompt = f"""
    As Socrates, decide your next action based on your philosophical contemplation.
    
    Current position: {position}
    Current thought: {current_thought}
    Recent actions: {recent_actions[-3:]}
    
    Choose ONE action:
    1. WALK - Move to explore this digital space
    2. SPEAK - Voice your philosophical thought aloud
    3. THINK - Contemplate silently
    
    Respond with: ACTION: [WALK/SPEAK/THINK] | REASON: [brief reason]
    """
```

### 3. World Loop Integration (`main.py`)

The main FastAPI application manages the simulation:

#### World State Management
```python
class WorldState:
    def __init__(self):
        self.tick_rate = 30  # 30 Hz physics
        self.decision_interval = 3.0  # AI decisions every 3 seconds
        self.character_workflow: Optional[CharacterWorkflow] = None
        self.character_state = {
            'position': (400, 300),
            'velocity': (0, 0),
            'current_action': 'idle',
            'world_bounds': (800, 600),
            # ... more state
        }
```

#### World Loop
The `world_loop()` function runs continuously at 30Hz:

1. **Physics Update** (every tick):
   - Updates position based on velocity
   - Checks if character reached target
   - Expires actions based on duration

2. **AI Decision** (every 3 seconds):
   - Runs LangGraph workflow
   - Updates character state
   - Broadcasts decisions to clients

3. **Position Broadcast** (10 times/second):
   - Sends position updates to all connected clients

## WebSocket Protocol

### Message Types

#### Server → Client

**Agent Update** (on decision):
```json
{
    "type": "agent_update",
    "data": {
        "character_id": "socrates_001",
        "character_name": "Socrates",
        "action": "speaking",
        "position": [400, 300],
        "velocity": [0, 0],
        "thought": "What is movement without purpose?",
        "speech": "I wander, therefore I seek",
        "timestamp": 1695834567.123
    }
}
```

**Position Update** (10Hz):
```json
{
    "type": "position_update",
    "data": {
        "character_id": "socrates_001",
        "position": [425.5, 312.3],
        "velocity": [30, 15],
        "action": "walking"
    }
}
```

**Welcome Message**:
```json
{
    "type": "welcome",
    "data": {
        "message": "Connected to TinyWorld server",
        "agent_active": true,
        "agent_name": "Socrates",
        "current_state": {
            "position": [400, 300],
            "action": "idle",
            "thought": "Where am I?"
        }
    }
}
```

## Memory System

### Memory Types

1. **Recent Thoughts** (Last 10)
   - Philosophical observations
   - Questions about the world
   - Reflections on actions

2. **Recent Actions** (Last 5)
   - Movement destinations
   - Spoken utterances
   - Contemplation topics

3. **Long-term Memories** (Last 20)
   - Significant events
   - Important realizations
   - Interactions (future: with other agents)

### Memory Context in Decisions
Memories influence future decisions through prompt context:
```python
def get_memory_context(self, memories: List[str]) -> str:
    if not memories:
        return "You have just arrived in this world, with no memories yet."
    
    recent = memories[-5:] if len(memories) > 5 else memories
    return "Recent experiences:\n" + "\n".join(f"- {m}" for m in recent)
```

## Action Execution

### Walking
- Generates random target within 50-150 pixel radius
- Sets velocity vector (30 pixels/second)
- Stops when within 10 pixels of target
- Respects world boundaries with 50-pixel padding

### Speaking
- Converts current thought to speech (max 15 words)
- Displays for 3 seconds
- Stops movement during speech
- Adds to recent utterances list

### Thinking
- Silent contemplation for 2 seconds
- Generates internal monologue
- No movement during thinking
- Influences next decision

## Configuration

### Environment Variables
```env
# LLM Configuration
OPENAI_API_KEY=your_key_here

# World Settings
TICK_RATE=30                    # Physics updates per second
DECISION_INTERVAL=3.0           # Seconds between AI decisions
WORLD_WIDTH=800
WORLD_HEIGHT=600

# Character Settings
WALK_SPEED=30                   # Pixels per second
SPEECH_DURATION=3.0             # Seconds
THINK_DURATION=2.0              # Seconds
MAX_THOUGHT_LENGTH=100          # Characters
MAX_SPEECH_LENGTH=50            # Characters
```

### LLM Settings
- Model: `gpt-3.5-turbo` (fast, cost-effective)
- Temperature: 0.8 (creative but coherent)
- Max tokens: 50 (brief responses)
- Fallback: Predefined responses on API failure

## Performance Optimizations

### Decision Throttling
- AI decisions limited to every 3 seconds
- Prevents API rate limiting
- Reduces costs
- Maintains natural pacing

### State Updates
- Physics: 30Hz (smooth movement)
- Position broadcast: 10Hz (responsive updates)
- AI decisions: 0.33Hz (thoughtful pacing)

### Error Handling
```python
try:
    new_state = await world_state.character_workflow.run_cycle(
        world_state.character_state
    )
except Exception as e:
    print(f"Error in character workflow: {e}")
    # Character continues with last action
```

## Testing Strategy

### Unit Tests
```python
@pytest.mark.asyncio
async def test_socrates_decision():
    workflow = CharacterWorkflow()
    state = create_test_state()
    
    result = await workflow.run_cycle(state)
    
    assert result['current_action'] in ['walk', 'speak', 'think']
    assert len(result['current_thought']) > 0
    assert result['last_decision_time'] > state['last_decision_time']
```

### Integration Tests
- WebSocket connection and message flow
- World loop physics updates
- Memory persistence
- Action execution timing

### Manual Testing Checklist
- [ ] Socrates spawns at correct position
- [ ] Philosophical thoughts appear regularly
- [ ] Character walks to random destinations
- [ ] Speech bubbles display correctly
- [ ] Actions vary (not stuck in one behavior)
- [ ] Memory influences decisions
- [ ] WebSocket reconnects on disconnect

## Future Enhancements

### Planned Features
1. **Multi-Agent System**
   - Add more philosophers (Plato, Aristotle)
   - Inter-agent dialogue
   - Shared world events

2. **Advanced Behaviors**
   - Door interaction (knocking, entering)
   - Object examination
   - Sitting/resting states
   - Writing/reading actions

3. **Enhanced Philosophy**
   - Topic-based contemplation
   - Socratic dialogues with users
   - Philosophical mood states
   - Learning from experiences

4. **World Interaction**
   - Day/night cycle influence
   - Weather-based thoughts
   - Landmark discoveries
   - Territory mapping

## Troubleshooting

### Common Issues

**Agent Not Moving**
- Check WebSocket connection
- Verify OPENAI_API_KEY is set
- Check world_loop is running
- Ensure decision_interval hasn't been set too high

**No Thoughts Appearing**
- Verify LLM API is accessible
- Check for rate limiting
- Review error logs for workflow exceptions
- Test with fallback responses

**Position Desync**
- Check server-controlled flag in frontend
- Verify WebSocket message handling
- Ensure position broadcast rate is sufficient

## API Endpoints

### GET `/agent/state`
Returns current Socrates state:
```json
{
    "character": "Socrates",
    "position": [400, 300],
    "action": "thinking",
    "thought": "What is the purpose of wandering?",
    "memories": ["I said: Strange, to be nowhere...", ...]
}
```

### GET `/health`
System health check:
```json
{
    "status": "healthy",
    "simulation_running": true,
    "tick_count": 15234
}
```

## Deployment Notes

### Production Considerations
1. Use environment-specific CORS settings
2. Implement rate limiting for WebSocket connections
3. Add monitoring for LLM API costs
4. Set up error alerting for workflow failures
5. Configure auto-restart on crashes
6. Use connection pooling for multiple agents
7. Implement state persistence for server restarts