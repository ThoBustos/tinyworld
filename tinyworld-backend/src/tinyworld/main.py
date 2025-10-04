from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import time
import os
import tempfile
import base64
from typing import List
from contextlib import asynccontextmanager

from tinyworld.core import config
from tinyworld.agents.conscious_worlfow import ConsciousWorkflow
from tinyworld.core.world_simulation import WorldState, WorldSimulation
from tinyworld.api.agents_routes import router as agents_router, set_world_state

# Global state for the world simulation
world_state = WorldState()
world_simulation = None

# Simple connection manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global world_simulation
    print("Starting TinyWorld simulation...")
    
    # Initialize character state
    world_state.character_state = {
        'character_id': 'socrates_001',
        'character_name': 'Socrates',
        'character_message': None,
        'last_decision_time': 0,
        'tick_count': 0
    }
    
    # Initialize character workflow
    world_state.conscious_workflow = ConsciousWorkflow()
    world_state.running = True
    
    # Inject world state into agents router
    set_world_state(world_state)
    
    # Create and start world simulation
    world_simulation = WorldSimulation(world_state, manager)
    asyncio.create_task(world_simulation.run_world_loop())
    
    yield
    
    # Shutdown
    print("Stopping TinyWorld simulation...")
    world_state.running = False

app = FastAPI(
    title="TinyWorld API",
    description="A tiny autonomous world simulation backend with AI agents",
    version="0.2.0",
    lifespan=lifespan
)

# Add CORS middleware for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(agents_router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to TinyWorld API",
        "status": "running",
        "agent": "Socrates is thinking..."
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "simulation_running": world_state.running,
        "tick_count": world_state.character_state.get('tick_count', 0)
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    # Send initial welcome with current agent state
    await manager.send_personal_message({
        "type": "welcome",
        "data": {
            "message": "Connected to TinyWorld server",
            "agent_active": True,
            "agent_name": "Socrates",
            "timestamp": time.time()
        }
    }, websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            print(f"📨 Received WebSocket message type: {data.get('type')}")
            
            # Handle screenshot trigger messages
            if data.get("type") == "screenshot_trigger":
                screenshot_data = data.get("data", {}).get("screenshot_data")
                current_position = data.get("data", {}).get("current_position")  # NEW
                
                if screenshot_data and world_simulation:
                    print(f"📸 Received screenshot (size: {len(screenshot_data) // 1024}KB)")
                    if current_position:  # NEW
                        print(f"📍 Current position: x={current_position['x']}, y={current_position['y']}")
                    
                    # Save base64 data to temp file
                    try:
                        # Remove data URL prefix if present
                        if screenshot_data.startswith('data:image'):
                            screenshot_data = screenshot_data.split(',', 1)[1]
                        
                        # Create temp file
                        with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', prefix='tinyworld_screenshot_', delete=False) as tmp_file:
                            # Decode base64 and write to file
                            image_data = base64.b64decode(screenshot_data)
                            tmp_file.write(image_data)
                            screenshot_path = tmp_file.name
                        
                        print(f"💾 Saved to temp file: {screenshot_path}")
                        
                        # Trigger AI decision with vision AND position
                        asyncio.create_task(
                            world_simulation._run_ai_decision_with_vision(
                                screenshot_path,
                                current_position  # NEW - pass position
                            )
                        )
                        
                        # Acknowledge receipt
                        await manager.send_personal_message({
                            "type": "screenshot_received",
                            "data": {
                                "timestamp": time.time(),
                                "temp_path": screenshot_path
                            }
                        }, websocket)
                    except Exception as e:
                        print(f"❌ Error processing screenshot: {e}")
                        await manager.send_personal_message({
                            "type": "error",
                            "data": {
                                "message": "Failed to process screenshot",
                                "error": str(e)
                            }
                        }, websocket)
            else:
                # Echo back with world update (for other message types)
                await manager.send_personal_message({
                    "type": "world_update",
                    "data": {
                        "timestamp": time.time(),
                        "echo": data,
                        "active_connections": len(manager.active_connections)
                    }
                }, websocket)
            
            # If it's a position update, broadcast to all
            if data.get("type") == "character_position":
                await manager.broadcast({
                    "type": "position_update",
                    "data": data.get("data", {})
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client disconnected. Active connections: {len(manager.active_connections)}")
