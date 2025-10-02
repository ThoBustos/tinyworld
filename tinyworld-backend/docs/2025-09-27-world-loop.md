# World Simulation Loop
*Date: September 27, 2025*

## What it is
The heartbeat of TinyWorld - a server-side loop that updates all entities 15-30 times per second.

## Why it matters
- Ensures consistent game state across all clients
- Provides predictable physics and movement
- Enables server-authoritative gameplay

## Implementation Steps
1. Set up asyncio event loop
2. Track delta time between ticks
3. Update all entities each tick
4. Broadcast state to connected clients
5. Sleep to maintain target tick rate

## Code Example
```python
async def world_loop(self):
    while self.running:
        dt = self.calculate_delta_time()
        self.update_entities(dt)
        self.broadcast_state()
        await asyncio.sleep(1.0 / TICK_RATE)
```