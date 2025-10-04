import asyncio
import time
import math
import os
from typing import Dict, Optional, List
from collections import deque
from datetime import datetime

from tinyworld.agents.conscious_worlfow import ConsciousWorkflow


class WorldState:
    def __init__(self):
        self.running = False
        self.tick_rate = 1  # Check once per second (simplified)
        self.decision_interval = 30.0  # AI decisions every 30 seconds
        self.conscious_workflow: Optional[ConsciousWorkflow] = None
        self.last_tick_time = time.time()
        self.recent_messages: deque = deque(maxlen=10)  # Rolling window of 10 latest messages

    def add_message(self, message: str, timestamp: float = None):
        """Add a message to the rolling window"""
        if timestamp is None:
            timestamp = time.time()
        
        self.recent_messages.append({
            'message': message,
            'timestamp': timestamp
        })

    def get_recent_messages_list(self) -> List[str]:
        """Get recent messages as a simple list of strings"""
        return [msg['message'] for msg in self.recent_messages]
    
    def get_recent_messages_with_timestamps(self) -> List[Dict[str, any]]:
        """Get recent messages with their timestamps"""
        return list(self.recent_messages)


class WorldSimulation:
    def __init__(self, world_state: WorldState, connection_manager):
        self.world_state = world_state
        self.manager = connection_manager
        self.decision_in_progress = False  # Prevent concurrent AI decisions
        
    async def run_world_loop(self):
        """Main world simulation loop - Now waits for frontend triggers"""
        print("🧠 Starting vision-triggered world loop - waiting for screenshots from frontend")
        print("📷 Screenshots should arrive every 30 seconds from the frontend")
        while self.world_state.running:
            # Just keep the loop alive, actual triggers come from screenshots
            await asyncio.sleep(1.0)
    
    # COMMENTED OUT: Physics simulation not needed for stationary thinking agent
    # async def _update_physics(self, dt: float):
    #     """Update character physics"""
    #     if self.world_state.character_state['current_action'] == 'walking':
    #         vx, vy = self.world_state.character_state['velocity']
    #         x, y = self.world_state.character_state['position']
    #         
    #         # Update position
    #         new_x = x + vx * dt
    #         new_y = y + vy * dt
    #         
    #         self.world_state.character_state['position'] = (new_x, new_y)
    #         
    #         # Check if reached target
    #         target = self.world_state.character_state.get('action_target', {}).get('target')
    #         if target:
    #             dist = math.sqrt((new_x - target[0])**2 + (new_y - target[1])**2)
    #             if dist < 10:  # Close enough to target
    #                 self.world_state.character_state['velocity'] = (0, 0)
    #                 self.world_state.character_state['current_action'] = 'idle'
    # 
    # async def _check_action_duration(self, current_time: float):
    #     """Check if current action should expire"""
    #     action_start = self.world_state.character_state.get('action_start_time', 0)
    #     action_duration = self.world_state.character_state.get('action_duration', 0)
    #     if action_start > 0 and current_time - action_start > action_duration:
    #         self.world_state.character_state['current_action'] = 'idle'
    #         self.world_state.character_state['velocity'] = (0, 0)
    
    async def _run_ai_decision(self):
        """Run the AI character decision workflow"""
        # Prevent concurrent executions
        if self.decision_in_progress:
            print("⚠️ AI decision already in progress, skipping...")
            return
            
        if self.world_state.conscious_workflow:
            print("🔄 Running conscious workflow...")
            try:
                self.decision_in_progress = True
                
                
                # Initialize or increment execution counter
                execution_count = self.world_state.character_state.get('execution_count', 0) + 1
                self.world_state.character_state['execution_count'] = execution_count
                
                # Pass recent messages with timestamps to the workflow
                recent_messages_with_timestamps = self.world_state.get_recent_messages_with_timestamps()
                
                # Run the character decision workflow with recent messages
                new_state = await self.world_state.conscious_workflow.run_cycle(
                    self.world_state.character_state,
                    recent_messages=recent_messages_with_timestamps
                )
                
                # Update AI-managed fields including movement decisions
                ai_fields = ['character_id', 'character_message', 'tick_count',
                            'wants_to_move', 'target_position']  # NEW fields
                for field in ai_fields:
                    if field in new_state:
                        self.world_state.character_state[field] = new_state[field]
                
                # Log movement decision if present
                if new_state.get('wants_to_move') and new_state.get('target_position'):
                    target = new_state['target_position']
                    print(f"🎯 Movement decided: to ({target['x']:.0f}, {target['y']:.0f})")
                else:
                    print(f"💭 No movement this cycle")
                
                # Add the new message to rolling window
                if 'character_message' in new_state:
                    current_time = time.time()
                    self.world_state.add_message(new_state['character_message'], current_time)
                    print(f"💬 Added message to rolling window (now has {len(self.world_state.recent_messages)} messages)")
                
                # CRITICAL: Set last_decision_time AFTER update to avoid overwrite
                current_time = time.time()
                self.world_state.character_state['last_decision_time'] = current_time
                
                print(f"✅ AI decision completed at {current_time:.2f} (Execution #{execution_count})")
                print(f"   Next trigger in 30 seconds (at ~{(current_time + 30):.2f})")
                
                # Broadcast the decision to all connected clients
                await self._broadcast_agent_update()
                
            except Exception as e:
                print(f"Error in character workflow: {e}")
            finally:
                self.decision_in_progress = False
        else:
            print("❌ No conscious_workflow found - workflow not initialized!")
    
    async def _broadcast_agent_update(self):
        """Broadcast agent decisions, thoughts and movement intentions"""
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
        
        # Only add movement fields if character wants to move
        if state.get('wants_to_move', False) and state.get('target_position'):
            message["data"]["wants_to_move"] = True
            message["data"]["target_position"] = state.get('target_position')
            print(f"📡 Broadcasting movement intent to frontend")
        
        await self.manager.broadcast(message)

    async def _run_ai_decision_with_vision(self, screenshot_path: str, 
                                           current_position: Dict[str, float] = None):
        """Run the AI character decision workflow triggered by screenshot"""
        # Prevent concurrent executions
        if self.decision_in_progress:
            print("⚠️ AI decision already in progress, skipping...")
            return
            
        if self.world_state.conscious_workflow:
            print(f"🔄 Running conscious workflow with vision from: {screenshot_path}")
            if current_position:
                print(f"📍 Character at position: x={current_position['x']:.0f}, y={current_position['y']:.0f}")
            
            try:
                self.decision_in_progress = True
                
                # Check if screenshot file exists
                if not os.path.exists(screenshot_path):
                    print(f"❌ Screenshot file not found: {screenshot_path}")
                    return
                
                # Initialize or increment execution counter
                execution_count = self.world_state.character_state.get('execution_count', 0) + 1
                self.world_state.character_state['execution_count'] = execution_count
                
                # Pass recent messages with timestamps to the workflow
                recent_messages_with_timestamps = self.world_state.get_recent_messages_with_timestamps()
                
                # Run the character decision workflow with screenshot AND position
                new_state = await self.world_state.conscious_workflow.run_cycle(
                    self.world_state.character_state,
                    recent_messages=recent_messages_with_timestamps,
                    screenshot_path=screenshot_path,
                    current_position=current_position  # NEW - pass position
                )
                
                # Update AI-managed fields including movement decisions
                ai_fields = ['character_id', 'character_message', 'tick_count',
                            'wants_to_move', 'target_position']  # NEW fields
                for field in ai_fields:
                    if field in new_state:
                        self.world_state.character_state[field] = new_state[field]
                
                # Log movement decision if present
                if new_state.get('wants_to_move') and new_state.get('target_position'):
                    target = new_state['target_position']
                    print(f"🎯 Movement decided: to ({target['x']:.0f}, {target['y']:.0f})")
                else:
                    print(f"💭 No movement this cycle")
                
                # Add the new message to rolling window
                if 'character_message' in new_state:
                    current_time = time.time()
                    self.world_state.add_message(new_state['character_message'], current_time)
                    print(f"💬 Added message to rolling window (now has {len(self.world_state.recent_messages)} messages)")
                
                # CRITICAL: Set last_decision_time AFTER update to avoid overwrite
                current_time = time.time()
                self.world_state.character_state['last_decision_time'] = current_time
                
                print(f"✅ AI decision completed at {current_time:.2f} (Execution #{execution_count})")
                print(f"   Next trigger expected from frontend screenshot")
                
                # Broadcast the decision to all connected clients
                await self._broadcast_agent_update()
                
            except Exception as e:
                print(f"Error in character workflow: {e}")
            finally:
                self.decision_in_progress = False
                # CRITICAL: Delete screenshot file after processing
                if os.path.exists(screenshot_path):
                    try:
                        os.remove(screenshot_path)
                        print(f"🗑️ Deleted screenshot: {screenshot_path}")
                    except Exception as e:
                        print(f"⚠️ Failed to delete screenshot: {e}")
        else:
            print("❌ No conscious_workflow found - workflow not initialized!")
    
    # COMMENTED OUT: Position updates not needed for stationary thinking agent
    # async def _broadcast_position_update(self):
    #     """Broadcast character position"""
    #     await self.manager.broadcast({
    #         "type": "position_update",
    #         "data": {
    #             "character_id": "socrates_001",
    #             "position": self.world_state.character_state.get('position'),
    #             "velocity": self.world_state.character_state.get('velocity'),
    #             "action": self.world_state.character_state.get('current_action')
    #         }
    #     })
