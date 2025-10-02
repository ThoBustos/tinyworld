# Vision-Triggered Workflow

## Overview
The AI consciousness workflow is now triggered by frontend screenshots instead of backend timers, enabling Socrates to perceive and respond to visual stimuli in his world.

## Architecture Change

### Previous Architecture
- Backend timer triggered workflow every 30 seconds
- No visual input to the AI
- Purely time-based decision making

### New Architecture  
- Frontend sends screenshots every 30 seconds
- Screenshots trigger the workflow
- Visual perception influences AI responses

## Implementation Details

### WebSocket Handler
- **Message Type**: `screenshot_trigger`
- **Payload**: Local file path to screenshot
- **Action**: Triggers `_run_ai_decision_with_vision()`

### Vision Processing Flow
```python
1. Receive screenshot path from WebSocket
2. Read image file from disk
3. Convert to base64 for Gemini API
4. Process with get_vision() node
5. Extract visual context
6. Pass to get_message() for response
7. Save to vector memory
8. DELETE screenshot file
9. Broadcast response
```

### ConsciousWorkflow Changes

#### New State Fields
```python
class SimpleState(TypedDict):
    character_id: str
    character_message: str
    tick_count: int
    screenshot_path: Optional[str]  # NEW
    visual_context: Optional[str]   # NEW
```

#### Workflow Graph
```
get_vision → get_message → save_memory → END
```

#### get_vision Node
- Reads screenshot from file path
- Sends to Gemini Vision API
- Extracts: scene description, visible objects, character positions
- Returns visual_context string

### Gemini Vision Integration
```python
# Using multimodal input
message = HumanMessage(
    content=[
        {"type": "text", "text": "Describe what you see"},
        {"type": "image_url", "image_url": f"data:image/png;base64,{encoded_image}"}
    ]
)
```

### File Cleanup Strategy
```python
async def _run_ai_decision_with_vision(self, screenshot_path: str):
    try:
        # Process workflow with vision
        result = await workflow.run_cycle(screenshot_path)
    finally:
        # ALWAYS delete the screenshot
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
```

## Error Handling
- Missing screenshot file: Log error, continue without vision
- Vision API failure: Fallback to text-only response
- File deletion failure: Log warning, continue
- Concurrent requests: Queue or reject duplicates

## Performance Considerations
- Image processing adds ~1-2s latency
- File I/O overhead minimal for temp files
- Gemini vision API rate limits apply
- Memory usage spike during processing

## Configuration
```python
VISION_ENABLED = True
SCREENSHOT_TIMEOUT = 5.0  # seconds to wait for file
CLEANUP_ON_ERROR = True
```

## Testing Strategy
1. Verify screenshot file reception
2. Test vision API integration
3. Validate file cleanup
4. Check error scenarios
5. Monitor memory usage

## Future Enhancements
- Cloud storage URLs instead of local files
- Batch processing of multiple views
- Visual memory persistence
- Scene change detection
- Object tracking across frames

## Monitoring
- Log all screenshot receipts
- Track vision API latency
- Monitor file cleanup success
- Alert on accumulation of temp files