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
  
  constructor(url: string = 'ws://localhost:8000/ws') {
    this.url = url;
  }
  
  connect(onAgentUpdate: (data: AgentUpdateMessage) => void): void {
    this.onAgentUpdateCallback = onAgentUpdate;
    
    try {
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = () => {
        console.log('🔌 Connected to TinyWorld server');
        if (this.reconnectTimeout) {
          clearTimeout(this.reconnectTimeout);
          this.reconnectTimeout = null;
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
            this.connect(this.onAgentUpdateCallback);
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
}