# Backend Movement Implementation
**Date:** 2025-01-04  
**Feature:** Intentional Movement System - Backend

## Overview
Movement system using conditional edges:
1. Generate message with movement intent
2. Conditional edge: if wants_to_move → determine position, else → skip

## Implementation

### 1. Define Schemas (`conscious_workflow.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional

class MessageWithIntent(BaseModel):
    """Message with movement intent"""
    message: str = Field(description="Philosophical reflection")
    wants_to_move: bool = Field(description="Does the character want to move?")

class TargetPosition(BaseModel):
    """Target position based on visual context"""
    x: float = Field(description="Target X coordinate", ge=0, le=1280)
    y: float = Field(description="Target Y coordinate", ge=0, le=1280)
    reason: str = Field(description="Brief reason for choosing this position")
```

### 2. Extend State (`conscious_workflow.py`)

```python
class SimpleState(TypedDict):
    """State with movement fields"""
    character_id: str
    character_message: str
    tick_count: int
    screenshot_path: Optional[str]
    visual_context: Optional[str]
    current_position: Optional[Dict[str, float]]  # NEW
    wants_to_move: bool  # NEW
    target_position: Optional[Dict[str, float]]  # NEW
```

### 3. Update Message Node (`conscious_workflow.py`)

```python
async def get_message(self, state: SimpleState) -> SimpleState:
    """Get character message with movement intent using structured output"""
    
    visual_context = state.get('visual_context', 'No visual perception available.')
    recent_memories = getattr(self, '_current_recent_messages', [])
    
    # Format memories...
    recent_memories_text = self._format_recent_memories(recent_memories)
    
    # Create LLM with structured output
    message_llm = self.llm.with_structured_output(MessageWithIntent)
    
    # Create prompt
    prompt = self._format_prompt(recent_memories_text, visual_context)
    prompt += """

Generate a philosophical reflection and indicate if you want to move.
Consider movement if you're curious about something visible or want to explore."""
    
    try:
        response = await message_llm.ainvoke(prompt)
        
        state['character_message'] = response.message
        state['wants_to_move'] = response.wants_to_move
        
        logger.info(f"💭 {self.config['name']}: {response.message}")
        if response.wants_to_move:
            logger.info(f"🚶 Character wants to move")
        
    except Exception as e:
        logger.error(f"Error getting message: {e}")
        state['character_message'] = "I find myself unable to express my thoughts clearly."
        state['wants_to_move'] = False
    
    state['tick_count'] = state.get('tick_count', 0) + 1
    return state
```

### 4. Movement Target Node (`conscious_workflow.py`)

```python
async def determine_movement_target(self, state: SimpleState) -> SimpleState:
    """Determine WHERE to move using image and context"""
    
    screenshot_path = state.get('screenshot_path')
    if not screenshot_path or not os.path.exists(screenshot_path):
        logger.warning("No screenshot for movement decision")
        state['target_position'] = None
        return state
    
    if not state.get('current_position'):
        logger.warning("No current position for movement decision")
        state['target_position'] = None
        return state
    
    try:
        # Read and encode image
        with open(screenshot_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
        
        # LLM with structured output for position
        position_llm = self.llm.with_structured_output(TargetPosition)
        
        current_pos = state['current_position']
        
        movement_prompt = f"""Based on the thought and image, where should the character move?

Thought: "{state['character_message']}"
Current position: x={current_pos['x']:.0f}, y={current_pos['y']:.0f}

World info:
- Size: 1280x1280 pixels (40x40 tiles of 32px)
- Origin (0,0) is top-left
- Stay within 100-400 pixels of current position

Look at the image and choose a visible location that aligns with the thought."""
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": movement_prompt},
                {"type": "image_url", "image_url": f"data:image/png;base64,{encoded_image}"}
            ]
        )
        
        target = await position_llm.ainvoke([message])
        
        state['target_position'] = {'x': target.x, 'y': target.y}
        logger.info(f"🎯 Target: ({target.x:.0f}, {target.y:.0f}) - {target.reason}")
        
    except Exception as e:
        logger.error(f"Error determining target: {e}")
        state['target_position'] = None
    
    return state
```

### 5. Conditional Edge Function (`conscious_workflow.py`)

```python
def movement_condition(state: SimpleState) -> str:
    """Conditional edge: check if character wants to move"""
    if state.get('wants_to_move', False):
        return "determine_movement"
    return "save_memory"
```

### 6. Build Graph with Conditional Edge (`conscious_workflow.py`)

```python
def _build_graph(self) -> StateGraph:
    """Build workflow with conditional movement"""
    workflow = StateGraph(SimpleState)
    
    # Add nodes
    workflow.add_node("get_vision", self.get_vision)
    workflow.add_node("get_message", self.get_message)
    workflow.add_node("determine_movement", self.determine_movement_target)
    workflow.add_node("save_memory", self.save_memory)
    
    # Set entry point
    workflow.set_entry_point("get_vision")
    
    # Add edges
    workflow.add_edge("get_vision", "get_message")
    
    # CONDITIONAL EDGE after message
    workflow.add_conditional_edges(
        "get_message",
        movement_condition,  # Function that checks wants_to_move
        {
            "determine_movement": "determine_movement",
            "save_memory": "save_memory"
        }
    )
    
    # Movement determination always goes to save_memory
    workflow.add_edge("determine_movement", "save_memory")
    
    # Save memory goes to END
    workflow.add_edge("save_memory", END)
    
    return workflow.compile()
```

### 7. Update run_cycle (`conscious_workflow.py`)

```python
async def run_cycle(self, current_state: Dict[str, Any] = None, 
                   recent_messages: List[Any] = None, 
                   screenshot_path: str = None,
                   current_position: Dict[str, float] = None) -> Dict:
    """Run cycle with position"""
    if current_state is None:
        current_state = {}
    
    self._current_recent_messages = recent_messages or []
        
    state = SimpleState(
        character_id=self.character_id,
        character_message=current_state.get('character_message', ''),
        tick_count=current_state.get('tick_count', 0),
        screenshot_path=screenshot_path,
        visual_context=None,
        current_position=current_position,
        wants_to_move=False,
        target_position=None
    )
    
    result = await self.graph.ainvoke(
        state,
        config={"callbacks": [self.opik_tracer]}
    )
    
    return result
```

### 8. WebSocket Handler (`main.py`)

```python
if data.get("type") == "screenshot_trigger":
    screenshot_data = data.get("data", {}).get("screenshot_data")
    current_position = data.get("data", {}).get("current_position")
    
    if screenshot_data and world_simulation:
        # Save screenshot...
        
        asyncio.create_task(
            world_simulation._run_ai_decision_with_vision(
                screenshot_path,
                current_position
            )
        )
```

### 9. World Simulation (`world_simulation.py`)

```python
async def _run_ai_decision_with_vision(self, screenshot_path: str, 
                                       current_position: Dict[str, float] = None):
    """Run AI decision with vision and position"""
    
    if self.decision_in_progress:
        print("⚠️ AI decision already in progress, skipping...")
        return
    
    try:
        self.decision_in_progress = True
        
        recent_messages = self.world_state.get_recent_messages_with_timestamps()
        
        # Run workflow
        new_state = await self.world_state.conscious_workflow.run_cycle(
            self.world_state.character_state,
            recent_messages=recent_messages,
            screenshot_path=screenshot_path,
            current_position=current_position
        )
        
        # Update state - only what's returned
        ai_fields = ['character_id', 'character_message', 'tick_count',
                    'wants_to_move', 'target_position']
        
        for field in ai_fields:
            if field in new_state:
                self.world_state.character_state[field] = new_state[field]
        
        # Log outcome
        if new_state.get('wants_to_move') and new_state.get('target_position'):
            target = new_state['target_position']
            print(f"🎯 Movement: to ({target['x']:.0f}, {target['y']:.0f})")
        else:
            print(f"💭 No movement")
        
        # Broadcast
        await self._broadcast_agent_update()
        
    finally:
        self.decision_in_progress = False
        # Cleanup screenshot...
```

### 10. Broadcast (`world_simulation.py`)

```python
async def _broadcast_agent_update(self):
    """Broadcast agent update"""
    state = self.world_state.character_state
    
    message = {
        "type": "agent_update",
        "data": {
            "character_id": "socrates_001",
            "character_name": "Socrates",
            "character_message": state.get('character_message'),
            "timestamp": time.time()
        }
    }
    
    # Only add movement if present
    if state.get('wants_to_move', False) and state.get('target_position'):
        message["data"]["wants_to_move"] = True
        message["data"]["target_position"] = state.get('target_position')
    
    await self.manager.broadcast(message)
```

## Graph Flow

```
get_vision
    ↓
get_message (sets wants_to_move)
    ↓
[Conditional Edge]
    ├─ wants_to_move=True → determine_movement → save_memory → END
    └─ wants_to_move=False → save_memory → END
```

## Key Points

- **Conditional edge** after message generation
- Movement target node **only runs if wants_to_move is True**
- No movement fields sent to frontend if character doesn't want to move
- Clean separation of concerns
- Efficient: image only processed for position when needed