# Entity Model Design
*Date: September 27, 2025*

## What it is
The core data structure representing anything that exists in the world - characters, objects, items.

## Key Properties
- **id**: Unique identifier (UUID or incremental)
- **position**: (x, y) coordinates in 2D space
- **velocity**: (vx, vy) movement vector
- **type**: Entity category (npc, player, object)

## Why these matter
- Position determines rendering location
- Velocity enables smooth movement
- ID tracks entities across network
- Type drives behavior and appearance

## Pydantic Model
```python
class Entity(BaseModel):
    id: str
    position: tuple[float, float]
    velocity: tuple[float, float] = (0, 0)
    type: str = "npc"
```