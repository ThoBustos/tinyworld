export interface AgentUpdateMessage {
  character_id: string;
  character_name: string;
  character_message?: string;
  timestamp: number;
}

export class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectTimeout: number | null = null;
  private onAgentUpdateCallback: ((data: AgentUpdateMessage) => void) | null = null;
  private onConnectedCallback: (() => void) | null = null;
  
  constructor(url: string = 'ws://localhost:8000/ws') {
    this.url = url;
  }
  
  connect(onAgentUpdate: (data: AgentUpdateMessage) => void, onConnected?: () => void): void {
    this.onAgentUpdateCallback = onAgentUpdate;
    this.onConnectedCallback = onConnected || null;
    
    try {
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = () => {
        console.log('🔌 Connected to TinyWorld server');
        if (this.reconnectTimeout) {
          clearTimeout(this.reconnectTimeout);
          this.reconnectTimeout = null;
        }
        // Call the onConnected callback if provided
        if (this.onConnectedCallback) {
          console.log('🎬 Calling onConnected callback...');
          this.onConnectedCallback();
        }
      };
      
      this.ws.onmessage = (event: MessageEvent) => {
        try {
          const message = JSON.parse(event.data);
          
          // Only handle agent_update messages
          if (message.type === 'agent_update' && message.data) {
            this.onAgentUpdateCallback?.(message.data);
          }
        } catch (error) {
          console.error('Failed to parse message:', error);
        }
      };
      
      this.ws.onerror = (error: Event) => {
        console.error('❌ WebSocket error:', error);
      };
      
      this.ws.onclose = () => {
        console.log('🔌 Disconnected from server');
        // Attempt to reconnect after 3 seconds
        this.reconnectTimeout = window.setTimeout(() => {
          console.log('Attempting to reconnect...');
          if (this.onAgentUpdateCallback) {
            this.connect(this.onAgentUpdateCallback, this.onConnectedCallback || undefined);
          }
        }, 3000);
      };
    } catch (error) {
      console.error('Failed to connect:', error);
    }
  }
  
  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
  
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
  
  sendScreenshotData(dataUrl: string): void {
    if (!this.isConnected()) {
      console.warn('Cannot send screenshot - not connected');
      return;
    }
    
    const message = {
      type: 'screenshot_trigger',
      data: {
        screenshot_data: dataUrl,
        timestamp: Date.now()
      }
    };
    
    try {
      this.ws?.send(JSON.stringify(message));
      console.log(`📤 Sent screenshot to server (${Math.round(dataUrl.length / 1024)}KB)`);
    } catch (error) {
      console.error('Failed to send screenshot:', error);
    }
  }
}