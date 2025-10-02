import { Container, Graphics, Text, TextStyle } from 'pixi.js';

export interface AgentDisplayOptions {
  bubbleColor?: number;
  textColor?: number;
  fontSize?: number;
  maxWidth?: number;
}

export class SpeechBubble extends Container {
  private background: Graphics;
  private text: Text;
  private fadeTimer: number | null = null;
  
  constructor(options: AgentDisplayOptions = {}) {
    super();
    
    const { maxWidth = 220 } = options;
    
    this.background = new Graphics();
    this.addChild(this.background);
    
    const style = new TextStyle({
      fontSize: 14,
      fill: 0x333333,
      fontFamily: 'Arial, sans-serif',
      wordWrap: true,
      wordWrapWidth: maxWidth - 24,
      align: 'center',
      lineHeight: 18,
    });
    
    this.text = new Text({ text: '', style });
    this.text.anchor.set(0.5);
    this.addChild(this.text);
    
    this.visible = false;
  }
  
  show(message: string, duration: number = 5): void {
    if (this.fadeTimer) {
      clearTimeout(this.fadeTimer);
    }
    
    this.text.text = message;
    
    // Clean bubble design
    const padding = 16;
    const width = Math.max(this.text.width + padding * 2, 80);
    const height = this.text.height + padding * 2;
    
    this.background.clear();
    
    // Clean white bubble with subtle border
    this.background.fill(0xFFFFFF);
    this.background.setStrokeStyle({ width: 2, color: 0xDDDDDD });
    
    // Center the bubble above the character
    const bubbleY = -height - 15;
    this.background.roundRect(-width / 2, bubbleY, width, height, 12);
    
    // Clean centered pointer triangle
    const pointerSize = 8;
    this.background.moveTo(-pointerSize, bubbleY + height);
    this.background.lineTo(0, bubbleY + height + pointerSize);
    this.background.lineTo(pointerSize, bubbleY + height);
    this.background.closePath();
    this.background.fill();
    
    // Center text both horizontally and vertically within bubble
    this.text.x = 0;
    this.text.y = bubbleY + height / 2;
    
    this.visible = true;
    this.alpha = 1;
    
    this.fadeTimer = window.setTimeout(() => this.hide(), duration * 1000);
  }
  
  hide(): void {
    this.visible = false;
  }
}

export class ActionIndicator extends Container {
  private icon: Text;
  private fadeTimer: number | null = null;
  
  constructor() {
    super();
    
    const style = new TextStyle({
      fontSize: 24,
      fill: 0xFFFFFF
    });
    
    this.icon = new Text({ text: '', style });
    this.icon.anchor.set(0.5);
    this.addChild(this.icon);
    
    this.visible = false;
  }
  
  show(emoji: string, duration: number = 1): void {
    if (this.fadeTimer) {
      clearTimeout(this.fadeTimer);
    }
    
    this.icon.text = emoji;
    this.visible = true;
    this.alpha = 1;
    
    // Floating animation
    this.y = 0;
    const float = () => {
      this.y -= 1;
      this.alpha -= 0.02;
      if (this.alpha > 0) {
        requestAnimationFrame(float);
      } else {
        this.visible = false;
        this.y = 0;
      }
    };
    
    this.fadeTimer = window.setTimeout(() => {
      float();
    }, duration * 1000);
  }
}

export class AgentDisplay extends Container {
  public speechBubble: SpeechBubble;
  private characterSprite: any;
  
  constructor(characterSprite: any) {
    super();
    
    this.characterSprite = characterSprite;
    this.speechBubble = new SpeechBubble();
    
    this.speechBubble.y = -80;
    
    this.addChild(this.speechBubble);
  }
  
  update(x: number, y: number): void {
    this.x = x;
    this.y = y;
  }
  
  handleAgentUpdate(data: any): void {
    const { speech, character_message } = data;
    
    // Show any message in the speech bubble
    const message = speech || character_message;
    if (message) {
      this.speechBubble.show(message, 5);
    }
  }
}