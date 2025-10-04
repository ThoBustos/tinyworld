import { Application } from 'pixi.js';
import { buildScene } from './scene';
import { createCamera, updateCamera, setupCameraControls, centerCameraOn } from './camera';
import { updateCharacterAI } from './character';
import { WebSocketService, AgentUpdateMessage } from './services/websocket';
import { AgentDisplay } from './components/AgentDisplay';
import { ScreenshotService } from './services/screenshot';
import { IntentionalMovementSystem } from './systems/movement';

async function bootstrap() {
  // Create PixiJS application with fullscreen settings
  const app = new Application();
  
  await app.init({
    resizeTo: window,        // Fullscreen - auto resize to window
    background: '#3b82f6',   
    antialias: false,        // Pixel-perfect rendering
    roundPixels: true,       // Ensure crisp pixels
    resolution: 1,           // Keep at 1 for consistent rendering
  });
  
  // Remove any existing content and add canvas
  const container = document.getElementById('app');
  if (container) {
    container.innerHTML = '';
    const canvas = app.canvas as HTMLCanvasElement;
    canvas.style.imageRendering = 'pixelated'; // Crisp pixels on all browsers
    canvas.style.imageRendering = 'crisp-edges'; // Fallback
    container.appendChild(canvas);
  }
  
  // Build the complete scene
  const scene = await buildScene(app);
  
  // Create agent display for Socrates
  const agentDisplay = new AgentDisplay(scene.character);
  scene.layers.entities.addChild(agentDisplay);  // Add to same layer as character
  
  // Scale world to fill WIDTH (allows vertical scrolling)
  const worldScale = app.screen.width / scene.worldWidth;
  scene.layers.world.scale.set(worldScale);
  
  // No horizontal centering needed (fills width exactly)
  scene.layers.world.x = 0;
  // Start at top of map
  scene.layers.world.y = 0;
  
  console.log(`World scale: ${worldScale}, Scaled height: ${scene.worldHeight * worldScale}px, Screen height: ${app.screen.height}px`);
  
  // Create camera system
  console.log('Setting up camera...');
  const camera = createCamera(
    scene.layers.world,
    scene.worldWidth,
    scene.worldHeight
  );
  
  // Setup manual camera controls
  const updateManualCamera = setupCameraControls(camera, app);
  
  // Create movement system
  const movementSystem = new IntentionalMovementSystem();
  
  // Connect to WebSocket server
  const wsService = new WebSocketService();
  
  // Initialize screenshot service
  const screenshotService = new ScreenshotService(app);
  
  // Connect with agent update handler and start screenshots on connection
  wsService.connect(
    // Agent update handler
    (agentData: AgentUpdateMessage) => {
      console.log('Agent Update:', agentData);
      
      if (agentData.character_id === 'socrates_001') {
        // Display real speech from server
        if (agentData.character_message) {
          agentDisplay.speechBubble.show(agentData.character_message, 30); // Show for 30 seconds
          console.log(`🗣️ Socrates says: "${agentData.character_message}"`);
        }
        
        // Handle movement intention (NEW)
        if (agentData.wants_to_move && agentData.target_position) {
          console.log(`🚶 Socrates wants to move to (${agentData.target_position.x}, ${agentData.target_position.y})`);
          movementSystem.setTarget(agentData.target_position);
        }
      }
    },
    // On connected callback - start screenshots
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
    
    // Camera following with scale
    const worldScale = app.screen.width / scene.worldWidth;
    const scaledCharY = scene.character.y * worldScale;
    const targetY = app.screen.height / 2 - scaledCharY;
    
    // Clamp Y position so we don't scroll past edges
    const maxY = 0; // Top of map
    const minY = app.screen.height - (scene.worldHeight * worldScale); // Bottom of map
    
    scene.layers.world.y = Math.max(minY, Math.min(maxY, targetY));
  });
  
  // Handle window resize
  window.addEventListener('resize', () => {
    app.resize();
    
    // Reapply world scaling on resize (fill width)
    const worldScale = app.screen.width / scene.worldWidth;
    scene.layers.world.scale.set(worldScale);
  });
  
  console.log('TinyWorld started! 🌍');
  console.log('Socrates has entered the world! 🏛️');
  console.log('Speech and thoughts will appear from websocket messages');
}

// Start the application
bootstrap().catch(console.error);