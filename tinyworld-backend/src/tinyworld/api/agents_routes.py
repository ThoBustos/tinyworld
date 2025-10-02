from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import time
import json

from tinyworld.agents.conscious_worlfow import ConsciousWorkflow

router = APIRouter(prefix="/agents")

# This will be injected from main.py
_world_state = None

def set_world_state(world_state):
    """Inject world state dependency"""
    global _world_state
    _world_state = world_state

@router.get("/state")
async def get_agent_state():
    """Get the current state of the Socrates agent"""
    if not _world_state:
        raise HTTPException(status_code=503, detail="World state not available")
    
    return {
        "character": "Socrates",
        "position": _world_state.character_state.get('position'),
        "action": _world_state.character_state.get('current_action'),
        "thought": _world_state.character_state.get('current_thought'),
        "memories": _world_state.character_state.get('memories', [])
    }

@router.get("/health")
async def agent_health():
    """Check agent health status"""
    if not _world_state:
        raise HTTPException(status_code=503, detail="World state not available")
    
    return {
        "status": "healthy" if _world_state.character_workflow else "no_workflow",
        "workflow_type": "ConsciousWorkflow",
        "character_id": getattr(_world_state.character_workflow, 'character_id', 'unknown')
    }

@router.post("/reset")
async def reset_agent():
    """Reset the agent state"""
    if not _world_state:
        raise HTTPException(status_code=503, detail="World state not available")
    
    # Reset character state
    _world_state.character_state.update({
        'current_thought': '',
        'recent_thoughts': [],
        'memories': [],
        'tick_count': 0,
        'current_action': 'idle'
    })
    
    return {"message": "Agent reset successfully"}
