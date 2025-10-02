import { Application } from 'pixi.js';
import { buildScene } from './scene';
import { createCamera, updateCamera, setupCameraControls, centerCameraOn } from './camera';
import { updateCharacterAI } from './character';
import { WebSocketService, AgentUpdateMessage } from './services/websocket';
import { AgentDisplay } from './components/AgentDisplay';

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
  
  // Connect to WebSocket server
  const wsService = new WebSocketService();
  
  // Connect with agent update handler - use websocket messages for speech/thought
  wsService.connect((agentData: AgentUpdateMessage) => {
    console.log('Agent Update:', agentData);
    
    if (agentData.character_id === 'socrates_001') {
      // Display real speech from server
      if (agentData.character_message) {
        agentDisplay.speechBubble.show(agentData.character_message, 30); // Show for 10 seconds
        console.log(`🗣️ Socrates says: "${agentData.character_message}"`);
      }
      // Display real thoughts from server
      // if (agentData.thought) {
      //   agentDisplay.speechBubble.show(agentData.thought, 30); // Show for 10 seconds
      //   console.log(`💭 Socrates thinks: "${agentData.thought}"`);
      // }
    }
  });
  
  // Main game loop - runs at 60fps
  app.ticker.add((ticker) => {
    // Update character AI
    updateCharacterAI(scene.character, ticker.deltaTime);
    
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