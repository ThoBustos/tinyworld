#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# Setup path and config
sys.path.insert(0, str(Path(__file__).parent / "src"))
from tinyworld.core import config
from tinyworld.agents.conscious_worlfow import ConsciousWorkflow

# Enhanced logging for debugging
from loguru import logger
import json

# Configure detailed logging
logger.add("agent_debug.log", rotation="1 MB", level="DEBUG", format="{time} | {level} | {message}")

async def debug_agent():
    """Debug agent with rich logging"""
    logger.info("🚀 Starting agent debugging session")
    
    workflow = ConsciousWorkflow("debug_character")
    current_state = {}
    
    for cycle in range(1, 4):
        logger.info(f"--- CYCLE {cycle} ---")
        
        # Log input state
        logger.debug(f"Input state: {json.dumps(current_state, indent=2)}")
        
        # Run cycle with timing
        start_time = asyncio.get_event_loop().time()
        result = await workflow.run_cycle(current_state)
        duration = asyncio.get_event_loop().time() - start_time
        
        # Log detailed results
        logger.info(f"✅ Cycle completed in {duration:.2f}s")
        logger.info(f"💭 New thought: {result['current_thought']}")
        logger.debug(f"📝 Recent thoughts: {result['recent_thoughts']}")
        logger.debug(f"🧠 Memories: {result['memories']}")
        logger.info(f"⏰ Tick count: {result['tick_count']}")
        
        print(f"\n🔄 Cycle {cycle}")
        print(f"💭 {result['current_thought']}")
        print(f"📊 Thoughts: {len(result['recent_thoughts'])}, Memories: {len(result['memories'])}")
        
        current_state = result
        await asyncio.sleep(0.5)  # Brief pause
    
    logger.info("🎯 Debug session complete")

if __name__ == "__main__":
    asyncio.run(debug_agent())
