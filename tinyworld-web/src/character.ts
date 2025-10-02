import { Application, AnimatedSprite, Assets, Spritesheet, Texture } from 'pixi.js';

export interface CharacterData {
  name: string;
  sprite: AnimatedSprite;
  spritesheet: Spritesheet;
  animations: Record<string, Texture[]>;
  x: number;
  y: number;
  vx: number;
  vy: number;
  currentDirection: string;
}

export async function createCharacter(
  app: Application, 
  characterName: string = 'socrates',
  startX: number = 400,
  startY: number = 300
): Promise<CharacterData> {
  
  // Load character atlas
  const atlasPath = `/assets/characters/${characterName}/atlas.json`;
  const texturePath = `/assets/characters/${characterName}/atlas.png`;
  
  // Load the texture first
  const texture = await Assets.load(texturePath);
  
  // Load and parse the atlas data
  const atlasData = await fetch(atlasPath).then(res => res.json());
  
  // Create spritesheet
  const spritesheet = new Spritesheet(texture, atlasData);
  await spritesheet.parse();
  
  // Get animation frames - PhiloAgents uses specific frame names
  const animations = {
    'idle_down': [spritesheet.textures[`${characterName}-front`] || spritesheet.textures['sprite1']],
    'idle_up': [spritesheet.textures[`${characterName}-back`] || spritesheet.textures['sprite1']],
    'idle_left': [spritesheet.textures[`${characterName}-left`] || spritesheet.textures['sprite1']],
    'idle_right': [spritesheet.textures[`${characterName}-right`] || spritesheet.textures['sprite1']],
    'walk_down': getWalkFrames(spritesheet, characterName, 'front'),
    'walk_up': getWalkFrames(spritesheet, characterName, 'back'),
    'walk_left': getWalkFrames(spritesheet, characterName, 'left'),
    'walk_right': getWalkFrames(spritesheet, characterName, 'right'),
  };
  
  // Create animated sprite with idle animation
  const animatedSprite = new AnimatedSprite(animations['idle_down']);
  animatedSprite.animationSpeed = 0.15; // Animation speed
  animatedSprite.play();
  
  // Position and scale
  animatedSprite.anchor.set(0.5, 0.8); // Anchor at feet
  animatedSprite.x = startX;
  animatedSprite.y = startY;
  animatedSprite.scale.set(1.5); // Make character bigger
  
  // Return character data with all needed info (scene will handle adding to correct layer)
  return {
    name: characterName,
    sprite: animatedSprite,
    spritesheet,
    animations,
    x: startX,
    y: startY,
    vx: 0,
    vy: 0,
    currentDirection: 'down'
  };
}

// Helper function to get walk animation frames
function getWalkFrames(spritesheet: Spritesheet, characterName: string, direction: string): Texture[] {
  const frames: Texture[] = [];
  
  // PhiloAgents uses format: socrates-front-walk-0000, socrates-front-walk-0001, etc.
  for (let i = 0; i <= 8; i++) {
    const frameName = `${characterName}-${direction}-walk-000${i}`;
    if (spritesheet.textures[frameName]) {
      frames.push(spritesheet.textures[frameName]);
    }
  }
  
  // If no walk frames found, use idle frame
  if (frames.length === 0) {
    const idleFrame = spritesheet.textures[`${characterName}-${direction}`];
    if (idleFrame) {
      frames.push(idleFrame);
    } else {
      // Fallback to any available texture
      const firstTexture = Object.values(spritesheet.textures)[0] as Texture;
      if (firstTexture) {
        frames.push(firstTexture);
      }
    }
  }
  
  return frames;
}

// Simple wander AI
export function updateCharacterAI(character: CharacterData, deltaTime: number) {
  // Random chance to change direction
  if (Math.random() < 0.02) { // 2% chance per frame - less erratic
    const speed =0.5; // pixels per frame - slightly slower
    const angle = Math.random() * Math.PI * 2;
    character.vx = Math.cos(angle) * speed;
    character.vy = Math.sin(angle) * speed;
    
    // Update animation based on direction
    const sprite = character.sprite;
    let newDirection = character.currentDirection;
    
    if (Math.abs(character.vx) > Math.abs(character.vy)) {
      // Moving horizontally
      if (character.vx > 0) {
        newDirection = 'right';
        sprite.textures = character.animations['walk_right'];
      } else {
        newDirection = 'left';
        sprite.textures = character.animations['walk_left'];
      }
    } else {
      // Moving vertically
      if (character.vy > 0) {
        newDirection = 'down';
        sprite.textures = character.animations['walk_down'];
      } else {
        newDirection = 'up';
        sprite.textures = character.animations['walk_up'];
      }
    }
    
    character.currentDirection = newDirection;
    sprite.play();
  }
  
  // Stop moving occasionally
  if (Math.random() < 0.01) { // 1% chance to stop
    character.vx = 0;
    character.vy = 0;
    
    // Set idle animation
    const idleAnim = `idle_${character.currentDirection === 'down' ? 'down' : 
                            character.currentDirection === 'up' ? 'up' : 
                            character.currentDirection === 'left' ? 'left' : 'right'}`;
    character.sprite.textures = character.animations[idleAnim];
    character.sprite.play();
  }
  
  // Update position
  character.x += character.vx * deltaTime;
  character.y += character.vy * deltaTime;
  
  // Apply to sprite
  character.sprite.x = character.x;
  character.sprite.y = character.y;
  
  // Keep in bounds - actual map is 40x40 tiles * 32px = 1280x1280
  const margin = 32; // One tile margin from edge
  const mapWidth = 1280;
  const mapHeight = 1280;
  
  if (character.x < margin || character.x > mapWidth - margin) {
    character.vx *= -1;
    character.x = Math.max(margin, Math.min(character.x, mapWidth - margin));
  }
  if (character.y < margin || character.y > mapHeight - margin) {
    character.vy *= -1;
    character.y = Math.max(margin, Math.min(character.y, mapHeight - margin));
  }
}