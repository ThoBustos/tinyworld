import asyncio
import time
import math
from typing import Dict, Optional

from tinyworld.agents.conscious_worlfow import ConsciousWorkflow


class WorldState:
    def __init__(self):
        self.running = False
        self.tick_rate = 1  # Check once per second (simplified)
        self.decision_interval = 30.0  # AI decisions every 30 seconds
        self.conscious_workflow: Optional[ConsciousWorkflow] = None
        self.last_tick_time = time.time()


class WorldSimulation:
    def __init__(self, world_state: WorldState, connection_manager):
        self.world_state = world_state
        self.manager = connection_manager
        self.decision_in_progress = False  # Prevent concurrent AI decisions
        
    async def run_world_loop(self):
        """Main world simulation loop - Simplified to only run AI decisions"""
        print("🧠 Starting simplified world loop - AI decisions every 30 seconds")
        while self.world_state.running:
            current_time = time.time()
            dt = current_time - self.world_state.last_tick_time
            self.world_state.last_tick_time = current_time
            
            # COMMENTED OUT: Physics updates not needed for pure AI thinking
            # await self._update_physics(dt)
            
            # COMMENTED OUT: Action duration checks not needed
            # await self._check_action_duration(current_time)
            
            # Run AI decision at 30-second intervals
            time_since_last = current_time - self.world_state.character_state['last_decision_time']
            if time_since_last > self.world_state.decision_interval:
                print(f"⏰ Triggering AI workflow at {current_time:.2f} (last was {time_since_last:.1f}s ago)")
                await self._run_ai_decision()
            
            # COMMENTED OUT: Position broadcasts not needed for stationary thinking agent
            # if int(current_time * 10) != int((current_time - dt) * 10):
            #     await self._broadcast_position_update()
            
            # Sleep for 1 second (simplified from 30 ticks/sec)
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
                
                # Debug: Check state before update
                old_last_decision = self.world_state.character_state.get('last_decision_time', 0)
                
                # Run the character decision workflow
                new_state = await self.world_state.conscious_workflow.run_cycle(
                    self.world_state.character_state
                )
                
                # Update only the AI-managed fields, preserve timing and physics
                ai_fields = ['character_id', 'character_message', 'tick_count']
                for field in ai_fields:
                    if field in new_state:
                        self.world_state.character_state[field] = new_state[field]
                
                # CRITICAL: Set last_decision_time AFTER update to avoid overwrite
                current_time = time.time()
                self.world_state.character_state['last_decision_time'] = current_time
                
                print(f"✅ AI decision completed at {current_time:.2f}")
                print(f"   Previous decision was at {old_last_decision:.2f}")
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
        """Broadcast agent decisions and thoughts"""
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
        
        # Remove the undefined 'action' variable references or define it properly
        # if action == 'speak':
        #     message["data"]["speech"] = state.get('action_target', {}).get('content', '')
        
        # if action == 'think':
        #     message["data"]["contemplating"] = True
        
        await self.manager.broadcast(message)

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
