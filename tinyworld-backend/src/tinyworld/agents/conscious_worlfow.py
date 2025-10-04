import asyncio
import time
import base64
import os
from typing import Dict, List, Any, TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.documents import Document
from langchain_chroma import Chroma
import opik
from opik.integrations.langchain import OpikTracer
from datetime import datetime
from pydantic import BaseModel, Field

from tinyworld.agents.prompts import CHARACTER_REFLECTION_PROMPT
from tinyworld.agents.personalities import get_socrates_config
from tinyworld.core.chroma_client import TinyWorldVectorStore
from loguru import logger

# Movement schemas for structured output
class MessageWithIntent(BaseModel):
    """Message with movement intent"""
    message: str = Field(description="Philosophical reflection")
    wants_to_move: bool = Field(description="Does the character want to move?")

class TargetPosition(BaseModel):
    """Target position based on visual context"""
    x: float = Field(description="Target X coordinate", ge=0, le=1280)
    y: float = Field(description="Target Y coordinate", ge=0, le=1280)
    reason: str = Field(description="Brief reason for choosing this position")

class SimpleState(TypedDict):
    """Simple state for character message with vision and movement"""
    character_id: str
    character_message: str
    tick_count: int
    screenshot_path: Optional[str]
    visual_context: Optional[str]
    current_position: Optional[Dict[str, float]]  # NEW: {"x": 640, "y": 320}
    wants_to_move: bool  # NEW
    target_position: Optional[Dict[str, float]]  # NEW: {"x": 640, "y": 320}


class ConsciousWorkflow:
    """Simple character message workflow"""
    
    def __init__(self, character_id: str = "socrates_001"):
        self.character_id = character_id
        self.config = get_socrates_config()
        
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.8,
            max_tokens=300
        )
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )

        self.graph = self._build_graph()
        
        # Opik tracing
        self.opik_tracer = OpikTracer(
            graph=self.graph.get_graph(xray=True),
            tags=["character_message", "tinyworld"]
        )
        
        # Vector store
        self.vector_store = TinyWorldVectorStore()
    
    def movement_condition(self, state: SimpleState) -> str:
        """Conditional edge: check if character wants to move"""
        if state.get('wants_to_move', False):
            return "determine_movement"
        return "save_memory"
    
    def _build_graph(self) -> StateGraph:
        """Build workflow with conditional movement"""
        workflow = StateGraph(SimpleState)
        
        # Add nodes
        workflow.add_node("get_vision", self.get_vision)
        workflow.add_node("get_message", self.get_message)
        workflow.add_node("determine_movement", self.determine_movement_target)
        workflow.add_node("save_memory", self.save_memory)
        
        # Set entry point
        workflow.set_entry_point("get_vision")
        
        # Add edges
        workflow.add_edge("get_vision", "get_message")
        
        # CONDITIONAL EDGE after message
        workflow.add_conditional_edges(
            "get_message",
            self.movement_condition,  # Function that checks wants_to_move
            {
                "determine_movement": "determine_movement",
                "save_memory": "save_memory"
            }
        )
        
        # Movement determination always goes to save_memory
        workflow.add_edge("determine_movement", "save_memory")
        
        # Save memory goes to END
        workflow.add_edge("save_memory", END)
        
        return workflow.compile()

    async def get_vision(self, state: SimpleState) -> SimpleState:
        """Process screenshot with vision model to extract visual context"""
        screenshot_path = state.get('screenshot_path')
        
        if not screenshot_path or not os.path.exists(screenshot_path):
            logger.info("👁️ No screenshot available, proceeding without vision")
            state['visual_context'] = "No visual input available - relying on inner contemplation."
            return state
        
        try:
            logger.info(f"👁️ Processing screenshot: {screenshot_path}")
            
            # Read and encode the image
            with open(screenshot_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            
            # Create vision prompt
            vision_prompt = """You are observing a scene from a tiny pixelated world. 
            Describe what you see in this image. Focus on:
            1. The overall environment and setting
            2. Any characters or entities visible
            3. Notable objects or landmarks
            4. The mood or atmosphere of the scene
            5. Any movement or action happening
            
            Be concise but descriptive, as if you're a philosopher observing the world."""
            
            # Process with Gemini vision
            message = HumanMessage(
                content=[
                    {"type": "text", "text": vision_prompt},
                    {"type": "image_url", "image_url": f"data:image/png;base64,{encoded_image}"}
                ]
            )
            
            response = await self.llm.ainvoke([message])
            visual_context = response.content.strip()
            
            state['visual_context'] = visual_context
            logger.info(f"🌆 Visual context: {visual_context[:100]}...")
            
        except Exception as e:
            logger.error(f"Error processing vision: {e}")
            state['visual_context'] = "My vision is clouded at the moment."
        
        return state
    
    async def get_message(self, state: SimpleState) -> SimpleState:
        """Get character message with movement intent using structured output"""
        
        # Get visual context from vision processing
        visual_context = state.get('visual_context', 'No visual perception available.')
        
        # Use provided recent memories and format them better with timestamps
        recent_memories = getattr(self, '_current_recent_messages', [])
        
        if recent_memories:
            # Format recent memories with timestamps and better structure
            formatted_memories = []
            for i, memory_data in enumerate(recent_memories[-10:], 1):  # Only show last 10 for clarity
                if isinstance(memory_data, dict) and 'message' in memory_data and 'timestamp' in memory_data:
                    # Format timestamp to readable format
                    timestamp = datetime.fromtimestamp(memory_data['timestamp']).strftime("%H:%M:%S")
                    formatted_memories.append(f"{i}. [{timestamp}] \"{memory_data['message']}\"")
                else:
                    # Fallback for old format (just strings)
                    formatted_memories.append(f"{i}. \"{memory_data}\"")
            recent_memories_text = "\n".join(formatted_memories)
        else:
            recent_memories_text = "No previous thoughts yet - this is your first reflection."
        
        logger.info(f"💭 Recent memories formatted:\n{recent_memories_text}")
        
        # Create LLM with structured output for message + intent
        message_llm = self.llm.with_structured_output(MessageWithIntent)
        
        # Create the prompt with visual context
        prompt = self._format_prompt(recent_memories_text, visual_context)
        prompt += """

Based on your observations and thoughts, determine:
Whether you want to move to explore or investigate something

Consider movement if you're curious about something you see, 
want to explore, or seek a different perspective."""
        
        logger.info(f"\n💭 Full Prompt:\n{prompt}\n")
        
        try:
            # Get structured response
            response = await message_llm.ainvoke(prompt)
            
            state['character_message'] = response.message
            state['wants_to_move'] = response.wants_to_move
            
            logger.info(f"💭 {self.config['name']}: {response.message}")
            logger.info(f"🚶 Wants to move: {response.wants_to_move}")
            
        except Exception as e:
            logger.error(f"Error getting message: {e}")
            state['character_message'] = "I find myself unable to express my thoughts clearly."
            state['wants_to_move'] = False
        
        state['tick_count'] = state.get('tick_count', 0) + 1
        return state
    
    async def determine_movement_target(self, state: SimpleState) -> SimpleState:
        """Determine WHERE to move using image and context"""
        
        # Only run if movement is wanted
        if not state.get('wants_to_move'):
            state['target_position'] = None
            return state
        
        screenshot_path = state.get('screenshot_path')
        if not screenshot_path or not os.path.exists(screenshot_path):
            logger.warning("No screenshot for movement decision")
            state['target_position'] = None
            return state
        
        if not state.get('current_position'):
            logger.warning("No current position for movement decision")
            state['target_position'] = None
            return state
        
        try:
            # Read and encode the image
            with open(screenshot_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            
            # Create LLM with structured output for position
            position_llm = self.llm.with_structured_output(TargetPosition)
            
            current_pos = state['current_position']
            
            # Movement prompt with image
            movement_prompt = f"""Based on the thought and image, where should the character move?

Thought: "{state['character_message']}"
Current position: x={current_pos['x']:.0f}, y={current_pos['y']:.0f}

World info:
- Size: 1280x1280 pixels (40x40 tiles of 32px)
- Origin (0,0) is top-left
- Stay within 100-400 pixels of current position

Look at the image and choose a visible location that aligns with the thought."""
            
            # Create message with image
            message = HumanMessage(
                content=[
                    {"type": "text", "text": movement_prompt},
                    {"type": "image_url", "image_url": f"data:image/png;base64,{encoded_image}"}
                ]
            )
            
            # Get target position
            target = await position_llm.ainvoke([message])
            
            state['target_position'] = {
                'x': target.x,
                'y': target.y
            }
            
            logger.info(f"🎯 Target determined: ({target.x:.0f}, {target.y:.0f}) - {target.reason}")
            
        except Exception as e:
            logger.error(f"Error determining movement target: {e}")
            state['target_position'] = None
        
        return state
    
    async def save_memory(self, state: SimpleState) -> SimpleState:
        """Save the character message in memory using single shared collection"""
        try:
            # Prepare metadata with character info and classic metadata
            metadata = {
                "character": self.config['name'],
                "character_id": state['character_id'],
                "tick_count": state['tick_count'],
                "message_type": "character_reflection",
                "personality": self.config['personality'],
            }
            
            # Use the existing add_memory method - it handles collection creation automatically
            # This will create/use collection: tinyworld_characters_memory
            doc_id = self.vector_store.add_memory(
                character_id="characters",
                content=state['character_message'],
                collection_name="tinyworld-characters-memory",
                memory_type="memory", 
                metadata=metadata,
                importance=5.0
            )
            
            logger.info(f"💾 Saved memory for {self.config['name']}: {state['character_message'][:50]}...")
            logger.debug(f"Memory saved with ID: {doc_id}")
            
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
        
        return state
    
    def _format_prompt(self, recent_memories: str, visual_context: str = '') -> str:
        """Format the character prompt with vision context"""
        prompt = str(CHARACTER_REFLECTION_PROMPT)
        prompt = prompt.replace('{{character_name}}', self.config['name'])
        prompt = prompt.replace('{{character_personality}}', self.config['personality'])
        prompt = prompt.replace('{{character_mission}}', self.config['mission'])
        prompt = prompt.replace('{{core_traits}}', self.config['core_traits'])
        prompt = prompt.replace('{{speaking_style}}', self.config['speaking_style'])
        prompt = prompt.replace('{{initial_beliefs}}', self.config['initial_beliefs'])
        prompt = prompt.replace('{{recent_memories}}', recent_memories)
        
        # Add visual context to the prompt
        if visual_context and visual_context != 'No visual perception available.':
            prompt += f"\n\n**What I observe in my surroundings:**\n{visual_context}\n\nReflect on both your inner thoughts and what you perceive visually."
        
        return prompt
    
    async def run_cycle(self, current_state: Dict[str, Any] = None, 
                       recent_messages: List[Any] = None, 
                       screenshot_path: str = None,
                       current_position: Dict[str, float] = None) -> Dict:
        """Run cycle with position and return full state including movement"""
        if current_state is None:
            current_state = {}
        
        # Store recent messages for use in get_message
        self._current_recent_messages = recent_messages or []
            
        state = SimpleState(
            character_id=self.character_id,
            character_message=current_state.get('character_message', ''),
            tick_count=current_state.get('tick_count', 0),
            screenshot_path=screenshot_path,
            visual_context=None,
            current_position=current_position,  # NEW
            wants_to_move=False,  # NEW
            target_position=None  # NEW
        )
        
        result = await self.graph.ainvoke(
            state,
            config={"callbacks": [self.opik_tracer]}
        )
        
        return result  # Returns full state including movement decision
    
    def get_created_traces(self):
        return self.opik_tracer.created_traces()
    
    def flush_traces(self):
        self.opik_tracer.flush()