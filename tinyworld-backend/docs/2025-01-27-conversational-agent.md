# Conversational Agent Feature
*Date: January 27, 2025*

## Feature Overview
Implementation of a continuous conversational agent with persistent memory using LangGraph and MongoDB.

## Architecture Components

### 1. Core Models
- **Conversation**: Manages conversation sessions with unique IDs
- **Message**: Individual messages with role and content
- **CharacterProfile**: Defines character personality and behavior
- **ConversationState**: Maintains current state and memory

### 2. LangGraph Workflow
Three-node workflow for conversation processing:
1. **Input Processing Node**: Parse and contextualize user input
2. **Response Generation Node**: Generate AI response with character personality
3. **Memory Update Node**: Persist conversation and update context

### 3. Service Layer
Business logic for conversation management:
- Session initialization and management
- Message processing with context
- History retrieval and management
- Memory persistence

### 4. Repository Pattern
MongoDB-based persistence:
- LangGraph checkpoint storage for state management
- Message history collection
- Character memory indexing
- Efficient retrieval with pagination

### 5. API Endpoints
RESTful and WebSocket interfaces:
- `POST /chat/start`: Initialize new conversation
- `POST /chat/message`: Send and receive messages
- `GET /chat/history/{session_id}`: Retrieve conversation history
- `POST /chat/reset`: Clear conversation memory
- `WS /chat/stream`: Real-time streaming responses

## Technical Stack
- **LangGraph**: Workflow orchestration
- **MongoDB**: State and memory persistence
- **OpenAI API**: Language model integration
- **FastAPI**: Web framework
- **Opik**: Observability and monitoring

## Character Configuration
```json
{
  "name": "Sage",
  "personality": "Wise and thoughtful, builds relationships over time",
  "system_prompt": "You are Sage, a wise mentor who remembers past conversations...",
  "memory_config": {
    "type": "continuous",
    "context_window": 20,
    "summary_threshold": 100
  }
}
```

## Development Phases

### Phase 1: Basic Conversation (Current)
- Single character implementation
- Simple memory management
- Basic API endpoints

### Phase 2: Enhanced Memory
- Conversation summarization
- Long-term memory indexing
- Context retrieval optimization

### Phase 3: Multi-Character
- Multiple character profiles
- Character switching
- Personality persistence

### Phase 4: World Integration
- Integration with TinyWorld simulation
- Character-to-character conversations
- Environmental context awareness

## Usage Example
```python
# Start conversation
response = await client.post("/chat/start", json={
    "character_id": "sage",
    "user_id": "user123"
})
session_id = response.json()["session_id"]

# Send message
response = await client.post("/chat/message", json={
    "session_id": session_id,
    "message": "Hello, Sage. Tell me about yourself."
})
print(response.json()["response"])
```

## Environment Variables
```bash
OPENAI_API_KEY=sk-...
MONGODB_URI=mongodb://localhost:27017/tinyworld
OPIK_API_KEY=...
```

## Testing Strategy
1. Unit tests for workflow nodes
2. Integration tests for conversation flow
3. Load tests for concurrent conversations
4. Memory persistence validation

## Monitoring
- Opik traces for LangGraph workflows
- Response time metrics
- Token usage tracking
- Error rate monitoring