# Agent Display System
*Date: September 27, 2025*

## Overview
This document describes the frontend implementation for displaying Socrates' philosophical thoughts and actions in TinyWorld. The system uses PixiJS for rendering, WebSocket for real-time updates, and custom UI components for speech and thought visualization.

## Architecture

### Component Hierarchy
```
Application (main.ts)
    ├── Scene (scene.ts)
    │   ├── World Container
    │   │   ├── Map Tiles
    │   │   ├── Character Sprite
    │   │   └── AgentDisplay
    │   │       ├── SpeechBubble
    │   │       ├── ThoughtBubble
    │   │       └── ActionIndicator
    │   └── UI Layer
    └── WebSocketService
        └── Agent Message Handler
```

### Data Flow
```
Backend WebSocket → Message Handler → Agent Display → Visual Update
         ↓                  ↓                ↓              ↓
   agent_update      Parse & Route    Update State    Render Bubbles
   position_update   to Components    Sync Position   Animate Actions
```

## Core Components

### 1. AgentDisplay Component (`components/AgentDisplay.ts`)

The main container for all agent UI elements:

```typescript
export class AgentDisplay extends Container {
  public speechBubble: SpeechBubble;
  public thoughtBubble: ThoughtBubble;
  public actionIndicator: ActionIndicator;
  private characterSprite: any;
  
  constructor(characterSprite: any) {
    super();
    
    this.characterSprite = characterSprite;
    
    // Create UI components
    this.speechBubble = new SpeechBubble();
    this.thoughtBubble = new ThoughtBubble();
    this.actionIndicator = new ActionIndicator();
    
    // Position relative to character
    this.speechBubble.y = -60;
    this.thoughtBubble.y = -60;
    this.actionIndicator.y = -30;
  }
}
```

#### Key Methods

**`update(x: number, y: number)`**
- Follows character position
- Called every frame to maintain attachment

**`handleAgentUpdate(data: AgentUpdateMessage)`**
- Processes agent state changes
- Routes to appropriate display component
- Manages bubble visibility

### 2. SpeechBubble Component

Displays spoken philosophical statements:

```typescript
export class SpeechBubble extends Container {
  private background: Graphics;
  private text: Text;
  private fadeTimer: number | null = null;
```

#### Visual Design
- **Background**: White with 95% opacity
- **Border**: 2px dark gray stroke
- **Shape**: Rounded rectangle with speech tail
- **Text**: Black, 14px, centered
- **Max width**: 200px with word wrap
- **Position**: 60px above character

#### Animation
```typescript
show(message: string, duration: number = 3): void {
  // Fade in animation
  this.alpha = 0;
  const fadeIn = () => {
    if (this.alpha < 1) {
      this.alpha += 0.1;
      requestAnimationFrame(fadeIn);
    }
  };
  
  // Auto-hide after duration
  this.fadeTimer = window.setTimeout(() => {
    this.hide();
  }, duration * 1000);
}
```

### 3. ThoughtBubble Component

Displays internal philosophical contemplations:

```typescript
export class ThoughtBubble extends Container {
  private background: Graphics;
  private text: Text;
```

#### Visual Design
- **Background**: Light gray (0xF8F8F8) with 90% opacity
- **Border**: 1px light gray stroke
- **Shape**: Cloud-like ellipse with thought dots
- **Text**: Dark gray, 12px, italic
- **Max width**: 180px
- **Thought dots**: Decreasing size circles leading to character

#### Differentiation from Speech
- Italic font style for thoughts
- Softer colors (gray vs white)
- Cloud shape vs rectangular bubble
- Shorter display duration (2s vs 3s)

### 4. ActionIndicator Component

Shows current action with emoji indicators:

```typescript
export class ActionIndicator extends Container {
  private icon: Text;
```

#### Action Emojis
- 🚶 Walking
- 💬 Speaking
- 🤔 Thinking

#### Animation
```typescript
show(emoji: string, duration: number = 1): void {
  // Floating upward animation
  const float = () => {
    this.y -= 1;        // Move up
    this.alpha -= 0.02; // Fade out
    if (this.alpha > 0) {
      requestAnimationFrame(float);
    }
  };
}
```

## WebSocket Integration

### Enhanced WebSocket Service (`services/websocket.ts`)

```typescript
export class WebSocketService {
  private onAgentUpdateCallback: ((data: AgentUpdateMessage['data']) => void) | null = null;
  
  connect(
    onMessage: (data: WebSocketMessage) => void,
    onAgentUpdate?: (data: AgentUpdateMessage['data']) => void
  ): void {
    this.onAgentUpdateCallback = onAgentUpdate || null;
    
    // Handle agent-specific messages
    if (data.type === 'agent_update' && this.onAgentUpdateCallback) {
      this.onAgentUpdateCallback(data.data);
    }
  }
}
```

### Message Types

```typescript
export interface AgentUpdateMessage {
  type: 'agent_update';
  data: {
    character_id: string;
    character_name: string;
    action: 'idle' | 'walking' | 'speaking' | 'thinking';
    position: [number, number];
    velocity: [number, number];
    thought?: string;      // Current philosophical thought
    speech?: string;       // Spoken utterance
    contemplating?: boolean; // True when thinking
    timestamp: number;
  };
}
```

## Main Application Integration (`main.ts`)

### Setup
```typescript
// Create agent display for Socrates
const agentDisplay = new AgentDisplay(scene.character);
scene.layers.world.addChild(agentDisplay);

// Track server control
let serverControlled = false;
let lastServerUpdate = 0;
```

### WebSocket Handler
```typescript
wsService.connect(
  (message) => {
    // General message handling
    if (message.type === 'welcome') {
      if (message.data.agent_active) {
        serverControlled = true;
        console.log('Socrates is being controlled by the server AI');
      }
    }
  },
  // Agent-specific handler
  (agentData) => {
    if (agentData.character_id === 'socrates_001') {
      // Update position
      const [x, y] = agentData.position;
      scene.character.x = x;
      scene.character.y = y;
      
      // Update display
      agentDisplay.update(x, y);
      agentDisplay.handleAgentUpdate(agentData);
      
      // Console logging for debugging
      if (agentData.thought) {
        console.log(`🏛️ Socrates thinks: "${agentData.thought}"`);
      }
      if (agentData.speech) {
        console.log(`🗣️ Socrates says: "${agentData.speech}"`);
      }
    }
  }
);
```

### Game Loop Integration
```typescript
app.ticker.add((ticker) => {
  // Only update local AI if not server controlled
  if (!serverControlled || (Date.now() - lastServerUpdate > 5000)) {
    updateCharacterAI(scene.character, ticker.deltaTime);
  }
  
  // Always update agent display position
  agentDisplay.update(scene.character.x, scene.character.y);
});
```

## State Synchronization

### Server-Controlled Mode
When `serverControlled = true`:
- Character position comes from server
- Local AI is disabled
- All actions are driven by backend
- Frontend is purely presentational

### Fallback Mode
If no server update for 5 seconds:
- Local AI takes over
- Character moves randomly
- No philosophical thoughts
- Basic wandering behavior

### Position Updates
- **Server rate**: 10Hz for smooth movement
- **Interpolation**: None currently (direct position setting)
- **Future**: Add position interpolation for smoother movement

## Visual Design Specifications

### Color Palette
```typescript
const COLORS = {
  // Speech bubble
  speechBackground: 0xFFFFFF,
  speechBorder: 0x333333,
  speechText: 0x000000,
  
  // Thought bubble
  thoughtBackground: 0xF8F8F8,
  thoughtBorder: 0xCCCCCC,
  thoughtText: 0x666666,
  
  // Transparency
  speechAlpha: 0.95,
  thoughtAlpha: 0.90
};
```

### Typography
```typescript
const STYLES = {
  speech: {
    fontSize: 14,
    fill: 0x000000,
    wordWrap: true,
    wordWrapWidth: 180,
    align: 'center'
  },
  thought: {
    fontSize: 12,
    fill: 0x666666,
    fontStyle: 'italic',
    wordWrap: true,
    wordWrapWidth: 160,
    align: 'center'
  }
};
```

### Positioning
- **Bubble height**: 60px above character center
- **Action indicator**: 30px above character
- **Horizontal**: Centered on character
- **Z-order**: Above character sprite

## Animation System

### Fade Animations
```typescript
// Generic fade in
const fadeIn = (element: Container, step: number = 0.1) => {
  element.alpha = 0;
  element.visible = true;
  
  const animate = () => {
    if (element.alpha < 1) {
      element.alpha += step;
      requestAnimationFrame(animate);
    }
  };
  animate();
};

// Generic fade out
const fadeOut = (element: Container, step: number = 0.1) => {
  const animate = () => {
    if (element.alpha > 0) {
      element.alpha -= step;
      requestAnimationFrame(animate);
    } else {
      element.visible = false;
    }
  };
  animate();
};
```

### Timing
- **Speech duration**: 3 seconds
- **Thought duration**: 2 seconds
- **Action indicator**: 0.5-1 second
- **Fade in speed**: 100ms (0.1 alpha/frame)
- **Fade out speed**: 100ms

## Performance Optimizations

### Container Management
```typescript
// Hide invisible elements
if (!this.visible) return;

// Skip updates when off-screen
if (!isInViewport(this.position)) return;
```

### Memory Management
```typescript
// Clear timers on destruction
destroy() {
  if (this.fadeTimer) {
    clearTimeout(this.fadeTimer);
  }
  super.destroy();
}
```

### Render Optimization
- Use `visible = false` when alpha reaches 0
- Reuse Graphics objects instead of recreating
- Batch text updates
- Limit redraw frequency

## Debug Features

### Console Logging
```typescript
// Formatted console output
console.log(`🏛️ Socrates thinks: "${thought}"`);
console.log(`🗣️ Socrates says: "${speech}"`);
console.log(`🚶 Socrates walks to (${x}, ${y})`);
```

### Debug Overlay (Future)
```typescript
class DebugOverlay extends Container {
  showState(state: AgentState) {
    // Display current action
    // Show position/velocity
    // List recent thoughts
    // Show memory count
  }
}
```

## Testing Strategies

### Component Tests
```typescript
describe('SpeechBubble', () => {
  it('should display message for specified duration', async () => {
    const bubble = new SpeechBubble();
    bubble.show('Test message', 1);
    
    expect(bubble.visible).toBe(true);
    expect(bubble.alpha).toBeGreaterThan(0);
    
    await wait(1100);
    expect(bubble.visible).toBe(false);
  });
});
```

### Integration Tests
```typescript
describe('AgentDisplay', () => {
  it('should show speech bubble for speaking action', () => {
    const display = new AgentDisplay(mockSprite);
    display.handleAgentUpdate({
      action: 'speaking',
      speech: 'Test speech',
      // ... other data
    });
    
    expect(display.speechBubble.visible).toBe(true);
    expect(display.thoughtBubble.visible).toBe(false);
  });
});
```

### Visual Testing Checklist
- [ ] Speech bubbles appear above character
- [ ] Thought bubbles use italic text
- [ ] Action indicators float upward
- [ ] Bubbles don't overlap
- [ ] Text wraps properly
- [ ] Animations are smooth
- [ ] Bubbles follow character movement
- [ ] Multiple bubbles don't conflict

## Configuration Options

### Display Settings
```typescript
interface AgentDisplayOptions {
  bubbleColor?: number;      // Background color
  textColor?: number;        // Text color
  fontSize?: number;         // Base font size
  maxWidth?: number;         // Maximum bubble width
  fadeSpeed?: number;        // Animation speed
  bubbleOffset?: number;     // Height above character
}
```

### Customization Example
```typescript
const customDisplay = new AgentDisplay(sprite, {
  bubbleColor: 0xFFFFE0,  // Light yellow
  textColor: 0x8B4513,     // Brown text
  fontSize: 16,            // Larger text
  maxWidth: 250            // Wider bubbles
});
```

## Troubleshooting

### Common Issues

**Bubbles Not Appearing**
- Check WebSocket connection status
- Verify agent_update messages arriving
- Check AgentDisplay added to scene
- Ensure character sprite exists

**Position Desync**
- Verify serverControlled flag
- Check lastServerUpdate timestamp
- Ensure position updates processed
- Review coordinate system alignment

**Performance Issues**
- Check bubble cleanup (timers cleared)
- Verify off-screen culling
- Monitor animation frame rate
- Review text update frequency

**Visual Glitches**
- Check z-order of display layers
- Verify bubble positioning math
- Review alpha blending settings
- Test different screen sizes

## Future Enhancements

### Planned Features

1. **Advanced Animations**
   - Bubble size elasticity
   - Character emotion indicators
   - Walking animation sync
   - Particle effects for thinking

2. **UI Improvements**
   - Click to expand thoughts
   - History of utterances
   - Thought topic tags
   - Mood-based colors

3. **Multi-Agent Support**
   - Multiple character displays
   - Conversation bubbles
   - Agent proximity detection
   - Dialogue threading

4. **Accessibility**
   - Screen reader support
   - High contrast mode
   - Font size options
   - Colorblind-friendly palette

5. **Mobile Optimization**
   - Touch interactions
   - Responsive bubble sizing
   - Gesture controls
   - Performance modes

## Integration with Other Systems

### Camera System
```typescript
// Bubbles stay at fixed offset from character
// Not affected by camera zoom/pan
agentDisplay.scale = 1 / camera.zoom;
```

### UI Layer
```typescript
// Option to render bubbles in UI layer
// Prevents world scaling effects
uiLayer.addChild(agentDisplay);
```

### Sound System (Future)
```typescript
// Play sound on speech
audioManager.play('socrates_speak.mp3');

// Ambient thinking sounds
audioManager.playLoop('thinking_ambience.mp3');
```

## Performance Metrics

### Target Performance
- **Frame rate**: 60 FPS with bubbles
- **Memory usage**: < 5MB for display system
- **CPU usage**: < 5% for animations
- **Network**: Handle 10 updates/second

### Monitoring
```typescript
// Performance tracking
const metrics = {
  bubbleRenders: 0,
  animationFrames: 0,
  messageProcessed: 0,
  avgRenderTime: 0
};
```

## Deployment Considerations

### Production Build
```typescript
// Minify and bundle
import { AgentDisplay } from './components/AgentDisplay.min.js';

// Remove debug logging
if (process.env.NODE_ENV === 'production') {
  console.log = () => {};
}
```

### Browser Compatibility
- Chrome 90+: Full support
- Firefox 88+: Full support
- Safari 14+: Full support
- Edge 90+: Full support
- Mobile browsers: Touch event handling needed

### Optimization Flags
```typescript
// PixiJS optimization
PIXI.settings.ROUND_PIXELS = true;
PIXI.settings.SCALE_MODE = PIXI.SCALE_MODES.NEAREST;
PIXI.settings.RESOLUTION = window.devicePixelRatio;
```