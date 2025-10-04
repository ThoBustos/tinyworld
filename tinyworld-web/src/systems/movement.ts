import { CharacterData } from '../character';

export class IntentionalMovementSystem {
  private targetPosition: { x: number; y: number } | null = null;
  private isMoving: boolean = false;
  private moveSpeed: number = 0.8; // pixels per frame - slightly slower than wander
  
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