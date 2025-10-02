# Sprites and Assets
*Date: September 27, 2025*

## Graphics vs Sprites
- **Graphics**: Vector shapes drawn with code (good for prototypes)
- **Sprites**: Images loaded from files (better quality)

## Creating a Simple House with Graphics
```typescript
const house = new Graphics()
    .rect(0, 0, 80, 60)
    .fill(0x8b5a2b)  // Brown walls
    .moveTo(-10, 0)
    .lineTo(40, -30)
    .lineTo(90, 0)
    .fill(0x6b3f18); // Darker roof
```

## Loading Image Assets
```typescript
import { Assets, Sprite } from 'pixi.js';

const texture = await Assets.load('assets/house.png');
const house = new Sprite({ texture });
house.anchor.set(0.5); // Center anchor point
```

## Positioning Tips
- Use `app.screen.width/height` for responsive positioning
- Set anchor points for easier rotation/scaling
- Position relative to screen size for different devices