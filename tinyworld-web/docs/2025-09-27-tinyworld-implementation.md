# TinyWorld Implementation
*Date: September 27, 2025*

## Overview
Today we built TinyWorld v1 - a complete 2D world with an autonomous character exploring an Ancient Greek town. We integrated PhiloAgents assets, created a camera system, and implemented character animations.

## What We Built

### 1. Asset Integration
- **Tilemap System**: Loaded PhiloAgents' `philoagents-town.json` tilemap
- **Tileset**: Used `tuxmon-sample-32px-extruded.png` (32x32 tiles with 1px extrusion)
- **Character Sprites**: Integrated 13 philosopher character atlases with animations
- **Map Size**: 40x40 tiles (1280x1280 pixels total)

### 2. Character System
- **Sprite Atlas Loading**: Each character has walking animations in 4 directions
- **Animation Naming**: Format is `characterName-direction-walk-0000` through `0008`
- **Idle Sprites**: Single frames like `socrates-front`, `socrates-back`
- **Wander AI**: Characters randomly change direction with smooth animations
- **Boundary Detection**: Characters bounce off map edges

### 3. Camera Following System
- **Smooth Following**: Camera lerps to character position (0.1 smoothing factor)
- **Zoom Level**: Set to 0.7 (30% zoomed out) for better map visibility
- **Edge Handling**: Camera stops at map boundaries to prevent showing void
- **Responsive**: Adjusts to window resize automatically

## Key Learnings

### Asset Organization
```
assets/
├── characters/
│   └── socrates/
│       ├── atlas.json    # Sprite definitions
│       └── atlas.png      # Sprite sheet
├── tilemaps/
│   └── philoagents-town.json
└── tilesets/
    └── tuxmon-sample-32px-extruded.png
```

### Sprite Atlas Structure
The character atlases use specific naming:
- **Walk cycles**: `socrates-front-walk-0000` to `0008`
- **Idle frames**: `socrates-front`, `socrates-back`, `socrates-left`, `socrates-right`
- **Important**: Frame names must match exactly or fallback to first available texture

### Camera Math
```typescript
// Zoom-adjusted viewport calculations
targetX = character.x - (screenWidth / zoom) / 2
maxX = worldWidth - (screenWidth / zoom)
containerX = -cameraX * zoom
```

### Performance Considerations
- **Container Hierarchy**: Map and character in camera container for unified movement
- **Animation Speed**: 0.15 for character animations (good balance)
- **Tick Rate**: 60fps with deltaTime for smooth movement
- **Lerping**: 0.1 smoothing factor prevents jarring camera movements

## Architecture Decisions

### Why PixiJS over Phaser
- Lighter weight for autonomous simulations
- More control over rendering pipeline
- Better for non-game applications

### Why Server-Authoritative Design (Future)
- Single source of truth for world state
- Prevents cheating in multiplayer
- Easier to add complex AI behaviors

### Container Structure
```
app.stage
└── camera.container (scaled by zoom)
    ├── map.container
    │   └── tile sprites
    └── character.sprite
```

## Common Issues & Solutions

### Issue: "No frames found for spritefront"
**Solution**: Check exact frame names in atlas.json, they often differ from expected

### Issue: Character at screen edge instead of center
**Solution**: Ensure camera calculations account for zoom factor

### Issue: Map too zoomed in
**Solution**: Add zoom property to camera (0.7 gives good visibility)

### Issue: Character walks off map
**Solution**: Use actual map dimensions (1280x1280) for boundaries

## Next Steps
1. **Backend Integration**: Connect WebSocket for multiplayer
2. **Multiple Characters**: Add more philosophers with different behaviors
3. **Collision Detection**: Prevent walking through buildings
4. **Interaction System**: Click to talk with characters
5. **Day/Night Cycle**: Visual effects and behavior changes

## Code Organization
```
web/src/
├── main.ts       # Bootstrap and game loop
├── map.ts        # Tilemap loading
├── character.ts  # Character creation and AI
├── camera.ts     # Viewport management
└── scene.ts      # (Currently unused placeholder)
```

## Important Constants
- **Map dimensions**: 1280x1280 pixels
- **Tile size**: 32x32 pixels
- **Camera zoom**: 0.7 (30% zoomed out)
- **Animation speed**: 0.15
- **Camera smoothing**: 0.1
- **Character speed**: 50 pixels/second
- **Wander chance**: 2% per frame

## Tips for Future Development
1. Always check atlas.json for exact sprite names
2. Use container hierarchy for clean transformations
3. Account for zoom in all camera calculations
4. Keep character AI simple - complexity comes from emergence
5. Test edge cases (map boundaries, window resize)