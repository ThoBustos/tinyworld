# Screenshot Vision Feature

## Overview
Frontend captures screenshots every 30 seconds to trigger the AI vision workflow, allowing Socrates to "see" and respond to the visual world.

## Implementation Details

### Screenshot Capture
- **Technology**: PixiJS `app.renderer.extract.base64()` method
- **Quality**: Full resolution (no compression in V1)
- **Format**: PNG with transparency support
- **Timing**: Every 30 seconds via setInterval

### File Management
- **Location**: OS temp directory (`/tmp` on Unix, `%TEMP%` on Windows)
- **Naming**: `tinyworld_screenshot_[timestamp].png`
- **Cleanup**: Backend deletes after processing (no accumulation)

### WebSocket Communication
- **Message Type**: `screenshot_trigger`
- **Payload**: File path only (not image data)
- **Size**: Minimal - just the path string

### Architecture Flow
```
1. Frontend captures screenshot (30s interval)
2. Save to temporary file
3. Send file path via WebSocket
4. Backend processes with vision AI
5. Backend deletes temp file
6. Frontend receives AI response
```

## Code Structure

### ScreenshotService Class
```typescript
class ScreenshotService {
  - captureScreenshot(): Promise<string>  // Returns file path
  - startCapturing(): void               // Begins 30s interval
  - stopCapturing(): void               // Stops interval
}
```

### Integration Points
- `main.ts`: Initializes and starts the service
- `websocket.ts`: Sends screenshot paths to backend
- `app`: PixiJS application instance for rendering

## Configuration
- **Interval**: 30 seconds (configurable)
- **File Format**: PNG
- **Temp Directory**: System default

## Error Handling
- Failed captures logged but don't stop the interval
- WebSocket disconnection pauses capturing
- Reconnection resumes capturing

## Future Enhancements (V2)
- Cloud storage integration (S3/GCS)
- URL-based transfer instead of file paths
- Compression for bandwidth optimization
- Selective region capture
- Motion detection to trigger captures

## Testing
- Verify temp file creation and deletion
- Check 30-second interval accuracy
- Test WebSocket message delivery
- Validate backend cleanup