# Autonomous Character Decision System
*Date: September 27, 2025*

## Overview
A real-time AI-driven character system where NPCs autonomously make decisions between walking, speaking, and knocking on doors. Uses LangGraph for decision orchestration and Opik for behavior monitoring.

## Architecture Flow
```
Character State → LangGraph Decision Node → Action Selection → World Update → Frontend Render
     ↑                                                                              ↓
     └──────────────────── Memory & Reflection Update ←───────────────────────────┘
```

---

## Backend Implementation

### 1. Core Dependencies
```python
# pyproject.toml additions
dependencies = [
    "langchain>=0.3.0",
    "langgraph>=0.2.0",
    "opik>=0.2.0",
    "anthropic>=0.30.0",  # or openai>=1.40.0
]
```

### 2. Character Agent Structure

#### State Definition
```python
from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, END

class CharacterState(TypedDict):
    # Core Identity
    id: str
    name: str
    personality: str  # "curious", "shy", "bold"
    
    # Physical State
    position: tuple[float, float]
    current_action: Literal["idle", "walking", "speaking", "knocking"]
    action_target: dict  # {type: "position"|"door"|"speech", data: ...}
    
    # Memory System
    short_term_memory: List[str]  # Last 10 observations/actions
    long_term_memory: List[str]   # Important events
    recent_utterances: List[str]  # Last 5 things said
    
    # Environment Context
    nearby_entities: List[dict]   # Other characters, doors, objects
    visible_doors: List[dict]     # Doors within interaction range
    last_decision_time: float     # Timestamp of last AI decision
```

#### LangGraph Decision Graph
```python
from langgraph.graph import StateGraph
from langchain_anthropic import ChatAnthropic

class CharacterAgent:
    def __init__(self, character_id: str):
        self.llm = ChatAnthropic(model="claude-3-haiku")
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(CharacterState)
        
        # Nodes
        workflow.add_node("observe", self.observe_environment)
        workflow.add_node("decide", self.make_decision)
        workflow.add_node("walk", self.execute_walk)
        workflow.add_node("speak", self.execute_speak)
        workflow.add_node("knock", self.execute_knock)
        workflow.add_node("update_memory", self.update_memory)
        
        # Edges
        workflow.set_entry_point("observe")
        workflow.add_edge("observe", "decide")
        
        # Conditional routing based on decision
        workflow.add_conditional_edges(
            "decide",
            self.route_action,
            {
                "walk": "walk",
                "speak": "speak",
                "knock": "knock"
            }
        )
        
        # All actions lead to memory update
        workflow.add_edge("walk", "update_memory")
        workflow.add_edge("speak", "update_memory")
        workflow.add_edge("knock", "update_memory")
        workflow.add_edge("update_memory", END)
        
        return workflow.compile()
```

#### Decision Logic
```python
async def make_decision(self, state: CharacterState) -> CharacterState:
    prompt = f"""
    You are {state['name']}, a {state['personality']} character.
    
    Current situation:
    - Position: {state['position']}
    - Nearby: {[e['type'] for e in state['nearby_entities']]}
    - Doors available: {len(state['visible_doors'])}
    - Recent memories: {state['short_term_memory'][-3:]}
    - Last things you said: {state['recent_utterances'][-2:]}
    
    Choose ONE action:
    1. WALK - Move to explore the world
    2. SPEAK - Say something based on your thoughts
    3. KNOCK - Knock on a nearby door
    
    Consider:
    - Don't repeat the same action too often
    - Your personality ({state['personality']}) should influence choices
    - React to your environment and memories
    
    Respond with: ACTION: [WALK/SPEAK/KNOCK] | REASON: [brief explanation]
    """
    
    response = await self.llm.ainvoke(prompt)
    action = self._parse_action(response.content)
    
    state['current_action'] = action.lower()
    return state
```

### 3. Opik Monitoring Integration

```python
from opik import track, flush
from opik.integrations.langchain import OpikTracer

class MonitoredCharacterAgent(CharacterAgent):
    def __init__(self, character_id: str):
        super().__init__(character_id)
        self.tracer = OpikTracer(
            project_name="tinyworld_characters",
            tags=["character_ai", character_id]
        )
    
    @track(name="character_decision_cycle")
    async def run_decision_cycle(self, state: CharacterState) -> CharacterState:
        # Track entire decision cycle
        with self.tracer.trace() as trace:
            trace.set_metadata({
                "character_id": state['id'],
                "personality": state['personality'],
                "position": state['position']
            })
            
            result = await self.graph.ainvoke(state)
            
            trace.log_metrics({
                "decision_latency": time.time() - state['last_decision_time'],
                "memory_size": len(state['short_term_memory']),
                "action_taken": result['current_action']
            })
            
            return result
```

### 4. World Loop Integration

```python
class WorldSimulation:
    def __init__(self):
        self.characters = {}
        self.character_agents = {}
        self.decision_interval = 3.0  # Seconds between decisions
        
    async def world_loop(self):
        while self.running:
            dt = self.calculate_delta_time()
            
            # Physics update (every tick)
            self.update_positions(dt)
            
            # AI decisions (throttled)
            await self.process_ai_decisions()
            
            # Broadcast state
            await self.broadcast_state()
            
            await asyncio.sleep(1.0 / TICK_RATE)
    
    async def process_ai_decisions(self):
        current_time = time.time()
        tasks = []
        
        for char_id, character in self.characters.items():
            if current_time - character['last_decision_time'] > self.decision_interval:
                agent = self.character_agents[char_id]
                tasks.append(self.run_character_decision(agent, character))
        
        # Run all decisions in parallel
        if tasks:
            await asyncio.gather(*tasks)
    
    async def run_character_decision(self, agent, character):
        try:
            updated_state = await agent.run_decision_cycle(character)
            self.apply_character_action(updated_state)
        except Exception as e:
            # Fallback to wander on error
            character['current_action'] = 'walk'
            character['velocity'] = self.random_velocity()
```

### 5. Action Executors

```python
class ActionExecutors:
    @staticmethod
    async def execute_walk(state: CharacterState) -> CharacterState:
        # Generate target position
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(50, 150)
        
        target = (
            state['position'][0] + distance * math.cos(angle),
            state['position'][1] + distance * math.sin(angle)
        )
        
        state['action_target'] = {
            'type': 'position',
            'data': target,
            'duration': 3.0  # Takes 3 seconds to walk
        }
        
        state['short_term_memory'].append(f"Decided to walk to {target}")
        return state
    
    @staticmethod
    async def execute_speak(state: CharacterState) -> CharacterState:
        # Generate contextual speech
        prompt = f"""
        As {state['name']} ({state['personality']}), say something short (max 15 words).
        Recent context: {state['short_term_memory'][-2:]}
        Don't repeat: {state['recent_utterances'][-1:]}
        """
        
        speech = await generate_speech(prompt)
        
        state['action_target'] = {
            'type': 'speech',
            'data': speech,
            'duration': 2.0  # Display for 2 seconds
        }
        
        state['recent_utterances'].append(speech)
        state['short_term_memory'].append(f"Said: {speech}")
        
        return state
    
    @staticmethod
    async def execute_knock(state: CharacterState) -> CharacterState:
        if not state['visible_doors']:
            # Fallback to walk if no doors
            return await ActionExecutors.execute_walk(state)
        
        door = random.choice(state['visible_doors'])
        
        state['action_target'] = {
            'type': 'door',
            'data': door['id'],
            'duration': 1.5  # Knock animation duration
        }
        
        state['short_term_memory'].append(f"Knocked on door at {door['position']}")
        return state
```

---

## Frontend Implementation

### 1. WebSocket Connection

```typescript
// websocket.ts
class CharacterSystemClient {
    private ws: WebSocket;
    private characters: Map<string, Character>;
    
    connect() {
        this.ws = new WebSocket('ws://localhost:8000/ws');
        
        this.ws.onmessage = (event) => {
            const update = JSON.parse(event.data);
            
            switch(update.type) {
                case 'character_decision':
                    this.handleDecision(update.data);
                    break;
                case 'character_action':
                    this.handleAction(update.data);
                    break;
                case 'world_state':
                    this.updateWorldState(update.data);
                    break;
            }
        };
    }
    
    handleDecision(data: DecisionData) {
        const character = this.characters.get(data.characterId);
        if (character) {
            // Show decision indicator
            character.showThinkingBubble(data.action);
            
            // Log to debug panel
            DebugPanel.log(`${character.name} decided to ${data.action}: ${data.reason}`);
        }
    }
}
```

### 2. Character Visualization

```typescript
// character.ts
import * as PIXI from 'pixi.js';

class Character {
    private sprite: PIXI.Sprite;
    private speechBubble: SpeechBubble;
    private actionIndicator: ActionIndicator;
    private debugInfo: DebugOverlay;
    
    constructor(id: string, position: [number, number]) {
        this.sprite = PIXI.Sprite.from('character.png');
        this.speechBubble = new SpeechBubble();
        this.actionIndicator = new ActionIndicator();
        this.debugInfo = new DebugOverlay();
    }
    
    updateAction(action: CharacterAction) {
        switch(action.type) {
            case 'walking':
                this.animateWalk(action.target);
                this.actionIndicator.show('🚶', action.duration);
                break;
                
            case 'speaking':
                this.speechBubble.show(action.data, action.duration);
                this.actionIndicator.show('💬', action.duration);
                break;
                
            case 'knocking':
                this.animateKnock();
                this.actionIndicator.show('👊', action.duration);
                break;
        }
    }
    
    animateWalk(target: [number, number]) {
        // Smooth movement interpolation
        const duration = 3000; // 3 seconds
        const startPos = this.sprite.position.clone();
        
        const animate = (progress: number) => {
            this.sprite.x = startPos.x + (target[0] - startPos.x) * progress;
            this.sprite.y = startPos.y + (target[1] - startPos.y) * progress;
            
            // Bob animation while walking
            this.sprite.y += Math.sin(progress * Math.PI * 8) * 2;
        };
        
        this.runAnimation(animate, duration);
    }
}
```

### 3. Speech Bubble System

```typescript
class SpeechBubble extends PIXI.Container {
    private background: PIXI.Graphics;
    private text: PIXI.Text;
    private fadeTimer: number;
    
    show(message: string, duration: number) {
        // Create bubble background
        this.background.clear();
        this.background.beginFill(0xFFFFFF, 0.95);
        this.background.drawRoundedRect(0, 0, 200, 50, 10);
        this.background.endFill();
        
        // Add text
        this.text.text = message;
        this.text.style = {
            fontSize: 14,
            fill: 0x000000,
            wordWrap: true,
            wordWrapWidth: 180
        };
        
        // Position above character
        this.position.set(-100, -80);
        
        // Fade in
        this.alpha = 0;
        gsap.to(this, { alpha: 1, duration: 0.3 });
        
        // Auto-hide after duration
        clearTimeout(this.fadeTimer);
        this.fadeTimer = setTimeout(() => {
            gsap.to(this, { 
                alpha: 0, 
                duration: 0.3,
                onComplete: () => this.visible = false
            });
        }, duration * 1000);
    }
}
```

### 4. Debug Monitoring Panel

```typescript
class DebugPanel {
    private decisions: DecisionLog[] = [];
    private metricsChart: Chart;
    
    constructor() {
        this.createPanel();
        this.connectToOpik();
    }
    
    createPanel() {
        const panel = document.createElement('div');
        panel.className = 'debug-panel';
        panel.innerHTML = `
            <h3>AI Decision Monitor</h3>
            <div class="metrics">
                <div>Decisions/min: <span id="decision-rate">0</span></div>
                <div>Avg Latency: <span id="avg-latency">0ms</span></div>
                <div>Active Characters: <span id="active-chars">0</span></div>
            </div>
            <div class="decision-log" id="decision-log"></div>
            <canvas id="action-distribution"></canvas>
        `;
        document.body.appendChild(panel);
    }
    
    logDecision(decision: DecisionData) {
        this.decisions.push(decision);
        
        // Update UI
        const logElement = document.getElementById('decision-log');
        const entry = document.createElement('div');
        entry.className = `decision-entry ${decision.action}`;
        entry.innerHTML = `
            <span class="time">${new Date().toLocaleTimeString()}</span>
            <span class="char">${decision.characterName}</span>
            <span class="action">${decision.action}</span>
            <span class="reason">${decision.reason}</span>
        `;
        logElement.insertBefore(entry, logElement.firstChild);
        
        // Update metrics
        this.updateMetrics();
        this.updateActionChart();
    }
}
```

---

## Data Flow & Messages

### WebSocket Message Protocol

```typescript
// Server -> Client Messages
interface CharacterDecisionMessage {
    type: 'character_decision';
    data: {
        characterId: string;
        characterName: string;
        action: 'walk' | 'speak' | 'knock';
        reason: string;
        timestamp: number;
        metrics: {
            latency: number;
            memoryUsed: number;
            tokensUsed: number;
        };
    };
}

interface CharacterActionMessage {
    type: 'character_action';
    data: {
        characterId: string;
        action: {
            type: 'walking' | 'speaking' | 'knocking';
            target?: [number, number];
            data?: string;
            duration: number;
        };
        position: [number, number];
    };
}

interface WorldStateMessage {
    type: 'world_state';
    data: {
        characters: CharacterState[];
        doors: DoorState[];
        timestamp: number;
    };
}

// Client -> Server Messages
interface ClientCommand {
    type: 'spawn_character' | 'remove_character' | 'set_personality';
    data: any;
}
```

### State Synchronization

```python
# Backend WebSocket Handler
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def broadcast_decision(self, character_id: str, decision: dict):
        message = {
            "type": "character_decision",
            "data": {
                "characterId": character_id,
                "characterName": decision["name"],
                "action": decision["action"],
                "reason": decision["reason"],
                "timestamp": time.time(),
                "metrics": {
                    "latency": decision["latency"],
                    "memoryUsed": len(decision["memory"]),
                    "tokensUsed": decision["tokens"]
                }
            }
        }
        
        for connection in self.active_connections:
            await connection.send_json(message)
    
    async def sync_world_state(self):
        # Send compressed world state every 100ms
        state = self.world.get_state()
        message = {
            "type": "world_state",
            "data": {
                "characters": [self.serialize_character(c) for c in state.characters],
                "doors": state.doors,
                "timestamp": time.time()
            }
        }
        
        for connection in self.active_connections:
            await connection.send_json(message)
```

---

## Performance Considerations

### Backend Optimizations

1. **Decision Batching**
```python
# Process multiple characters in one LLM call
async def batch_decisions(characters: List[CharacterState]) -> List[str]:
    prompt = self.create_batch_prompt(characters)
    response = await self.llm.ainvoke(prompt)
    return self.parse_batch_response(response)
```

2. **Caching**
```python
# Cache similar situations
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_decision(situation_hash: str) -> str:
    # Return cached decision for similar situations
    pass
```

3. **Rate Limiting**
```python
class RateLimiter:
    def __init__(self, max_decisions_per_minute: int = 20):
        self.limit = max_decisions_per_minute
        self.decisions = deque()
    
    async def should_make_decision(self) -> bool:
        now = time.time()
        # Remove old decisions
        while self.decisions and self.decisions[0] < now - 60:
            self.decisions.popleft()
        
        if len(self.decisions) < self.limit:
            self.decisions.append(now)
            return True
        return False
```

### Frontend Optimizations

1. **Object Pooling**
```typescript
class SpeechBubblePool {
    private pool: SpeechBubble[] = [];
    
    get(): SpeechBubble {
        return this.pool.pop() || new SpeechBubble();
    }
    
    release(bubble: SpeechBubble) {
        bubble.reset();
        this.pool.push(bubble);
    }
}
```

2. **Throttled Updates**
```typescript
// Only update visible characters
class ViewportCuller {
    updateVisibleCharacters(characters: Character[], camera: Camera) {
        characters.forEach(char => {
            const inView = camera.isInView(char.position);
            char.visible = inView;
            
            if (inView) {
                char.update();
            }
        });
    }
}
```

---

## Configuration & Environment Variables

```python
# .env
ANTHROPIC_API_KEY=your_key_here
OPIK_API_KEY=your_opik_key
OPIK_WORKSPACE=tinyworld

# Decision System Config
DECISION_INTERVAL=3.0  # Seconds between decisions
MAX_CHARACTERS=10      # Max AI-controlled characters
LLM_MODEL=claude-3-haiku-20240307
MAX_TOKENS_PER_DECISION=150
ENABLE_DEBUG_UI=true
```

---

## Testing Strategy

### Backend Tests
```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_character_decision_cycle():
    agent = CharacterAgent("test_char")
    state = create_test_state()
    
    # Mock LLM response
    agent.llm.ainvoke = AsyncMock(return_value="ACTION: WALK | REASON: Exploring")
    
    result = await agent.graph.ainvoke(state)
    
    assert result['current_action'] == 'walk'
    assert len(result['short_term_memory']) > len(state['short_term_memory'])
```

### Frontend Tests
```typescript
describe('Character Decision System', () => {
    it('should display speech bubble on speak action', () => {
        const character = new Character('test', [0, 0]);
        const action = {
            type: 'speaking',
            data: 'Hello world!',
            duration: 2
        };
        
        character.updateAction(action);
        
        expect(character.speechBubble.visible).toBe(true);
        expect(character.speechBubble.text).toBe('Hello world!');
    });
});
```

---

## Deployment Checklist

- [ ] Configure rate limits for LLM calls
- [ ] Set up Opik project and API keys
- [ ] Implement graceful fallbacks for LLM failures
- [ ] Add cost monitoring alerts
- [ ] Configure WebSocket reconnection logic
- [ ] Set up debug UI toggle
- [ ] Implement character limit controls
- [ ] Add performance monitoring
- [ ] Create admin controls for personality adjustment
- [ ] Document API endpoints for character management