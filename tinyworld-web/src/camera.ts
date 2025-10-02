import { Application, Container } from 'pixi.js';
import { CharacterData } from './character';

export interface Camera {
  worldContainer: Container;
  worldWidth: number;
  worldHeight: number;
  x: number;
  y: number;
  smoothing: number;
  isManualControl: boolean;
}

export function createCamera(
  worldContainer: Container,
  worldWidth: number,
  worldHeight: number
): Camera {
  return {
    worldContainer,
    worldWidth,
    worldHeight,
    x: 0,
    y: 0,
    smoothing: 0.08,
    isManualControl: false
  };
}

export function updateCamera(
  camera: Camera,
  character: CharacterData | null,
  app: Application
) {
  if (!character) return;
  
  const screenWidth = app.screen.width;
  const screenHeight = app.screen.height;
  
  if (!camera.isManualControl) {
    // Center character on screen with slight offset for visual center
    const targetX = character.x - screenWidth / 2;
    const targetY = (character.y - 20) - screenHeight / 2;
    
    // Clamp to world boundaries
    const maxX = Math.max(0, camera.worldWidth - screenWidth);
    const maxY = Math.max(0, camera.worldHeight - screenHeight);
    
    const clampedX = Math.max(0, Math.min(targetX, maxX));
    const clampedY = Math.max(0, Math.min(targetY, maxY));
    
    // Smooth camera movement
    camera.x += (clampedX - camera.x) * camera.smoothing;
    camera.y += (clampedY - camera.y) * camera.smoothing;
  }
  
  // Apply camera position to world container
  camera.worldContainer.x = Math.round(-camera.x);
  camera.worldContainer.y = Math.round(-camera.y);
}

export function setupCameraControls(camera: Camera, app: Application) {
  const keys: Record<string, boolean> = {};
  const manualSpeed = 15;
  
  window.addEventListener('keydown', (e) => {
    keys[e.key] = true;
  });
  
  window.addEventListener('keyup', (e) => {
    keys[e.key] = false;
  });
  
  return function updateManualCamera() {
    if (keys['Shift']) {
      camera.isManualControl = true;
      
      const screenWidth = app.screen.width;
      const screenHeight = app.screen.height;
      
      if (keys['ArrowLeft']) camera.x -= manualSpeed;
      if (keys['ArrowRight']) camera.x += manualSpeed;
      if (keys['ArrowUp']) camera.y -= manualSpeed;
      if (keys['ArrowDown']) camera.y += manualSpeed;
      
      // Clamp to boundaries
      const maxX = Math.max(0, camera.worldWidth - screenWidth);
      const maxY = Math.max(0, camera.worldHeight - screenHeight);
      
      camera.x = Math.max(0, Math.min(camera.x, maxX));
      camera.y = Math.max(0, Math.min(camera.y, maxY));
      
      // Apply directly in manual mode
      camera.worldContainer.x = Math.round(-camera.x);
      camera.worldContainer.y = Math.round(-camera.y);
    } else {
      camera.isManualControl = false;
    }
  };
}

export function centerCameraOn(camera: Camera, x: number, y: number, app: Application) {
  const screenWidth = app.screen.width;
  const screenHeight = app.screen.height;
  
  const targetX = x - screenWidth / 2;
  const targetY = y - screenHeight / 2;
  
  const maxX = Math.max(0, camera.worldWidth - screenWidth);
  const maxY = Math.max(0, camera.worldHeight - screenHeight);
  
  camera.x = Math.max(0, Math.min(targetX, maxX));
  camera.y = Math.max(0, Math.min(targetY, maxY));
  
  camera.worldContainer.x = Math.round(-camera.x);
  camera.worldContainer.y = Math.round(-camera.y);
}