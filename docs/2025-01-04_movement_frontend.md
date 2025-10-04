# Frontend Movement Implementation
**Date:** 2025-01-04  
**Feature:** Intentional Movement System - Frontend

## Overview
Handle intentional movement from backend while maintaining random wander as default.

## Implementation

### 1. Add Movement Manager (`tinyworld-web/src/systems/movement.ts`)

```typescript
export class IntentionalMovementSystem {
  private targetPosition: { x: number; y: number } | null = null;
  private isMoving: boolean = false;
  private moveSpeed: number = 0.8; // pixels per frame - smooth movement
  
  /**
   * Set movement target from backend
   */
  setTarget(target: { x: number; y: number }) {
    this.targetPosition = target;
    this.isMoving = true;
    console.log(`🎯 Movement target set: (${target.x}, ${target.y})`);
  }
  
  /**
   * Update character position toward target
   */
  update(character: CharacterData, deltaTime: number): boolean {
    if (!this.isMoving || !this.targetPosition) {
      return false; // Not moving intentionally
    }
    
    // Calculate direction to target
    const dx = this.targetPosition.x - character.x;
    const dy = this.targetPosition.y - character.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    
    // Check if reached target (within 5 pixels)
    if (distance < 5) {
      character.x = this.targetPosition.x;
      character.y = this.targetPosition.y;
      character.vx = 0;
      character.vy = 0;
      
      // Clear target
      this.targetPosition = null;
      this.isMoving = false;
      
      console.log('✅ Reached target position');
      
      // Set idle animation
      this.setIdleAnimation(character);
      return false;
    }
    
    // Normalize direction and apply speed
    const speed = this.moveSpeed * deltaTime;
    character.vx = (dx / distance) * speed;
    character.vy = (dy / distance) * speed;
    
    // Update position
    character.x += character.vx;
    character.y += character.vy;
    
    // Update animation based on movement direction
    this.updateAnimation(character);
    
    // Apply to sprite
    character.sprite.x = character.x;
    character.sprite.y = character.y;
    
    return true; // Still moving
  }
  
  /**
   * Update animation based on movement direction
   */
  private updateAnimation(character: CharacterData) {
    const sprite = character.sprite;
    let newDirection = character.currentDirection;
    
    if (Math.abs(character.vx) > Math.abs(character.vy)) {
      // Moving horizontally
      if (character.vx > 0) {
        newDirection = 'right';
      } else {
        newDirection = 'left';
      }
    } else {
      // Moving vertically
      if (character.vy > 0) {
        newDirection = 'down';
      } else {
        newDirection = 'up';
      }
    }
    
    // Update animation if direction changed
    if (newDirection !== character.currentDirection) {
      character.currentDirection = newDirection;
      const walkAnim = `walk_${newDirection}`;
      sprite.textures = character.animations[walkAnim];
      sprite.play();
    }
    
    // Ensure animation is playing
    if (!sprite.playing) {
      sprite.play();
    }
  }
  
  /**
   * Set idle animation
   */
  private setIdleAnimation(character: CharacterData) {
    const idleAnim = `idle_${character.currentDirection}`;
    character.sprite.textures = character.animations[idleAnim];
    character.sprite.play();
  }
  
  /**
   * Check if currently moving
   */
  isMovingIntentionally(): boolean {
    return this.isMoving;
  }
}
```

### 2. Update WebSocket Service (`tinyworld-web/src/services/websocket.ts`)

```typescript
export interface AgentUpdateMessage {
  character_id: string;
  character_name: string;
  character_message?: string;
  timestamp: number;
  wants_to_move?: boolean;  // NEW
  target_position?: { x: number; y: number };  // NEW
}

export class WebSocketService {
  // ... existing code ...
  
  /**
   * Send screenshot with current position
   */
  sendScreenshotData(dataUrl: string, currentPosition: { x: number; y: number }): void {
    if (!this.isConnected()) {
      console.warn('Cannot send screenshot - not connected');
      return;
    }
    
    const message = {
      type: 'screenshot_trigger',
      data: {
        screenshot_data: dataUrl,
        current_position: currentPosition,  // NEW
        timestamp: Date.now()
      }
    };
    
    try {
      this.ws?.send(JSON.stringify(message));
      console.log(`📤 Sent screenshot with position (${currentPosition.x}, ${currentPosition.y})`);
    } catch (error) {
      console.error('Failed to send screenshot:', error);
    }
  }
}
```

### 3. Update Main Loop (`tinyworld-web/src/main.ts`)

```typescript
import { IntentionalMovementSystem } from './systems/movement';

async function bootstrap() {
  // ... existing setup ...
  
  // Create movement system
  const movementSystem = new IntentionalMovementSystem();
  
  // Connect to WebSocket server
  const wsService = new WebSocketService();
  
  // Initialize screenshot service
  const screenshotService = new ScreenshotService(app);
  
  // Connect with agent update handler
  wsService.connect(
    // Agent update handler
    (agentData: AgentUpdateMessage) => {
      console.log('Agent Update:', agentData);
      
      if (agentData.character_id === 'socrates_001') {
        // Display message
        if (agentData.character_message) {
          agentDisplay.speechBubble.show(agentData.character_message, 30);
          console.log(`🗣️ Socrates says: "${agentData.character_message}"`);
        }
        
        // Handle movement intention (NEW)
        if (agentData.wants_to_move && agentData.target_position) {
          console.log(`🚶 Socrates wants to move to (${agentData.target_position.x}, ${agentData.target_position.y})`);
          movementSystem.setTarget(agentData.target_position);
        }
      }
    },
    // On connected callback
    () => {
      console.log('✅ WebSocket connected, starting screenshot capture...');
      screenshotService.startCapturing(30, (dataUrl) => {
        // Send screenshot with current character position
        const currentPosition = {
          x: scene.character.x,
          y: scene.character.y
        };
        console.log(`📸 Sending screenshot from position (${currentPosition.x.toFixed(0)}, ${currentPosition.y.toFixed(0)})`);
        wsService.sendScreenshotData(dataUrl, currentPosition);
      });
    }
  );
  
  // Main game loop - runs at 60fps
  app.ticker.add((ticker) => {
    // Try intentional movement first
    const isMovingIntentionally = movementSystem.update(scene.character, ticker.deltaTime);
    
    // If not moving intentionally, use random wander
    if (!isMovingIntentionally) {
      updateCharacterAI(scene.character, ticker.deltaTime);
    }
    
    // Always update agent display position
    agentDisplay.update(scene.character.x, scene.character.y);
    
    // Camera following (existing code)
    const worldScale = app.screen.width / scene.worldWidth;
    const scaledCharY = scene.character.y * worldScale;
    const targetY = app.screen.height / 2 - scaledCharY;
    
    const maxY = 0;
    const minY = app.screen.height - (scene.worldHeight * worldScale);
    
    scene.layers.world.y = Math.max(minY, Math.min(maxY, targetY));
  });
  
  // ... rest of existing code ...
}
```

### 4. Optional: Visual Feedback (`tinyworld-web/src/components/MovementIndicator.ts`)

```typescript
import { Graphics, Container } from 'pixi.js';

export class MovementIndicator extends Container {
  private targetMarker: Graphics;
  private pathLine: Graphics;
  
  constructor() {
    super();
    
    // Create target marker (small circle)
    this.targetMarker = new Graphics();
    this.targetMarker.beginFill(0x00ff00, 0.5);
    this.targetMarker.drawCircle(0, 0, 5);
    this.targetMarker.endFill();
    this.targetMarker.visible = false;
    
    // Create path line
    this.pathLine = new Graphics();
    this.pathLine.visible = false;
    
    this.addChild(this.pathLine);
    this.addChild(this.targetMarker);
  }
  
  /**
   * Show movement target and path
   */
  showTarget(from: { x: number; y: number }, to: { x: number; y: number }) {
    // Position marker
    this.targetMarker.x = to.x;
    this.targetMarker.y = to.y;
    this.targetMarker.visible = true;
    
    // Draw path line
    this.pathLine.clear();
    this.pathLine.lineStyle(2, 0x00ff00, 0.3);
    this.pathLine.moveTo(from.x, from.y);
    this.pathLine.lineTo(to.x, to.y);
    this.pathLine.visible = true;
  }
  
  /**
   * Hide indicators
   */
  hide() {
    this.targetMarker.visible = false;
    this.pathLine.visible = false;
  }
}
```

## Data Flow

### Frontend → Backend
```typescript
{
  type: 'screenshot_trigger',
  data: {
    screenshot_data: string,  // base64 image
    current_position: {        // NEW
      x: number,
      y: number
    },
    timestamp: number
  }
}
```

### Backend → Frontend
```typescript
{
  type: 'agent_update',
  data: {
    character_id: string,
    character_name: string,
    character_message: string,
    timestamp: number,
    wants_to_move?: boolean,     // Only if movement
    target_position?: {           // Only if movement
      x: number,
      y: number
    }
  }
}
```

## Movement Behavior

1. **Default**: Random wander (existing `updateCharacterAI`)
2. **When backend sends movement**: 
   - Stop random wander
   - Move smoothly to target
   - Resume random wander when reached

## Benefits

- Clean separation: intentional vs random movement
- Smooth transitions between movement modes
- No movement when character is contemplating
- Visual feedback optional but helpful
- Maintains existing wander behavior