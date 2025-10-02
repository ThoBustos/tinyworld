# Workflow Trigger Timing Fix
**Date:** 2025-01-31  
**Author:** Thomas & Claude  
**Issue:** ConsciousWorkflow triggering 600+ times per minute instead of once every 30 seconds

## Problem Statement

The `conscious_workflow.py` was being triggered hundreds of times per minute instead of the intended once every 30 seconds, causing:
- Excessive LLM API calls (600+ per minute)
- High costs and rate limiting
- System performance degradation
- Opik trace flooding

## Root Cause Analysis

### Investigation Process
1. Initially suspected WebSocket reconnection loops
2. Checked for multiple workflow instances
3. Discovered timing state management issue

### The Critical Bug

The bug was in `world_simulation.py` - the `last_decision_time` field was not persisting correctly:

```python
# PROBLEM: The workflow returns its own state
new_state = await self.world_state.conscious_workflow.run_cycle(
    self.world_state.character_state
)
# This update would overwrite ALL fields including last_decision_time
self.world_state.character_state.update(new_state)
# Setting this after was useless - it had already been overwritten!
self.world_state.character_state['last_decision_time'] = time.time()
```

Since `last_decision_time` was always 0 after the update, the condition `current_time - 0 > 30` was always true, triggering on every tick (once per second).

## Solution Implemented

### 1. Selective State Update (Lines 109-113)
```python
# Update only the AI-managed fields, preserve timing and physics
ai_fields = ['current_thought', 'recent_thoughts', 'memories', 'tick_count', 'character_id']
for field in ai_fields:
    if field in new_state:
        self.world_state.character_state[field] = new_state[field]
```

### 2. Proper Timing Management (Lines 115-117)
```python
# CRITICAL: Set last_decision_time AFTER selective update
current_time = time.time()
self.world_state.character_state['last_decision_time'] = current_time
```

### 3. Concurrency Protection (Lines 92-94, 99, 129)
```python
# Prevent concurrent executions
if self.decision_in_progress:
    print("⚠️ AI decision already in progress, skipping...")
    return
# ... workflow execution ...
finally:
    self.decision_in_progress = False
```

### 4. Enhanced Debug Logging
- Shows time since last decision
- Displays when next trigger will occur
- Warns about concurrent execution attempts

### 5. Frontend Simplification
- Removed mock message system
- Connected WebSocket handler to display real thoughts from server
- Simplified to only show server-sent messages

## Key Learnings

### 1. State Management in Async Systems
- **Lesson:** When updating state from multiple sources, be explicit about which fields should be updated
- **Best Practice:** Use selective field updates instead of blanket `.update()` calls

### 2. Timing State Must Be Preserved
- **Lesson:** Timing/control state should be managed separately from business logic state
- **Best Practice:** Keep infrastructure state (timing, locks) separate from domain state

### 3. Debug Early and Often
- **Lesson:** Adding detailed logging immediately would have caught this bug faster
- **Best Practice:** Log state before and after critical operations

### 4. Concurrency Protection
- **Lesson:** Async workflows can overlap if not properly guarded
- **Best Practice:** Use flags or locks to prevent concurrent execution of critical sections

## Testing Checklist

✅ **Verify 30-second intervals:**
```bash
# Watch backend logs - should see:
⏰ Triggering AI workflow at X (last was 30.0s ago)
✅ AI decision completed at X
   Previous decision was at Y
   Next trigger in 30 seconds (at ~Z)
```

✅ **Check Opik traces:**
- Should see 2 traces per minute (not 600+)
- Each trace should complete successfully

✅ **Monitor WebSocket messages:**
- Frontend should receive `agent_update` every 30 seconds
- Thought bubbles should display for 15 seconds

✅ **Verify no concurrent executions:**
- Should never see "AI decision already in progress" warning

## Configuration

Current settings in `world_simulation.py`:
- `tick_rate = 1` - Check once per second
- `decision_interval = 30.0` - AI decisions every 30 seconds
- `max_tokens = 50` - Limited thought length for cost control

## Future Improvements

1. **Make interval configurable:** Environment variable for `DECISION_INTERVAL`
2. **Add metrics:** Track decision latency, success rate, token usage
3. **Implement backpressure:** Queue thoughts if LLM is slow
4. **Add health checks:** Ensure workflow is running as expected
5. **Separate concern:** Consider moving timing logic to a dedicated scheduler

## Related Files

- `/tinyworld-backend/src/tinyworld/core/world_simulation.py` - Main timing loop
- `/tinyworld-backend/src/tinyworld/agents/conscious_worlfow.py` - AI workflow
- `/tinyworld-backend/src/tinyworld/main.py` - Backend initialization
- `/tinyworld-web/src/main.ts` - Frontend WebSocket handler
- `/tinyworld-web/src/services/websocket.ts` - WebSocket service

## Conclusion

A simple state management bug caused a 900x increase in LLM API calls. The fix involved:
1. Selective state updates to preserve timing fields
2. Proper order of operations (update domain state, then timing state)
3. Concurrency protection to prevent overlapping executions
4. Enhanced logging for debugging

This incident highlights the importance of careful state management in async systems and the value of comprehensive logging during development.