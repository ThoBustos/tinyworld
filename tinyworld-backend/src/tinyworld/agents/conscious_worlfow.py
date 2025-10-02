import asyncio
import time
from typing import Dict, List, Any, TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.documents import Document
from langchain_chroma import Chroma
import opik
from opik.integrations.langchain import OpikTracer
from datetime import datetime

from tinyworld.agents.prompts import CHARACTER_REFLECTION_PROMPT
from tinyworld.agents.personalities import get_socrates_config
from tinyworld.core.chroma_client import TinyWorldVectorStore
from loguru import logger

class SimpleState(TypedDict):
    """Simple state for character message"""
    character_id: str
    character_message: str
    tick_count: int


class ConsciousWorkflow:
    """Simple character message workflow"""
    
    def __init__(self, character_id: str = "socrates_001"):
        self.character_id = character_id
        self.config = get_socrates_config()
        
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.8,
            max_tokens=100
        )
        
        self.graph = self._build_graph()
        
        # Opik tracing
        self.opik_tracer = OpikTracer(
            graph=self.graph.get_graph(xray=True),
            tags=["character_message", "tinyworld"]
        )
        
        # Vector store
        self.vector_store = TinyWorldVectorStore()
    
    def _build_graph(self) -> StateGraph:
        """Build workflow with memory-saving node"""
        workflow = StateGraph(SimpleState)
        
        workflow.add_node("get_message", self.get_message)
        workflow.add_node("save_memory", self.save_memory)
        
        workflow.set_entry_point("get_message")
        workflow.add_edge("get_message", "save_memory")
        workflow.add_edge("save_memory", END)
        
        return workflow.compile()
    
    async def get_message(self, state: SimpleState) -> SimpleState:
        """Get character message using prompt"""
        
        # Use provided recent memories and format them better
        recent_memories = getattr(self, '_current_recent_messages', [])
        
        if recent_memories:
            # Format recent memories with numbers and better structure
            formatted_memories = []
            for i, memory in enumerate(recent_memories[-5:], 1):  # Only show last 5 for clarity
                formatted_memories.append(f"{i}. \"{memory}\"")
            recent_memories_text = "\n".join(formatted_memories)
        else:
            recent_memories_text = "No previous thoughts yet - this is your first reflection."
        
        logger.info(f"💭 Recent memories formatted:\n{recent_memories_text}")
        
        # Create the prompt
        prompt = self._format_prompt(recent_memories_text)
        logger.info(f"\n💭 Full Prompt:\n{prompt}\n")
        
        try:
            # Get message from character
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            character_message = response.content.strip()
            
            state['character_message'] = character_message
            logger.info(f"💭 {self.config['name']}: {character_message}")
            
        except Exception as e:
            logger.error(f"Error getting message: {e}")
            state['character_message'] = "I find myself unable to express my thoughts clearly."
        
        state['tick_count'] = state.get('tick_count', 0) + 1
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
    
    def _format_prompt(self, recent_memories: str) -> str:
        """Format the character prompt"""
        prompt = str(CHARACTER_REFLECTION_PROMPT)
        prompt = prompt.replace('{{character_name}}', self.config['name'])
        prompt = prompt.replace('{{character_personality}}', self.config['personality'])
        prompt = prompt.replace('{{character_mission}}', self.config['mission'])
        prompt = prompt.replace('{{core_traits}}', self.config['core_traits'])
        prompt = prompt.replace('{{speaking_style}}', self.config['speaking_style'])
        prompt = prompt.replace('{{initial_beliefs}}', self.config['initial_beliefs'])
        prompt = prompt.replace('{{recent_memories}}', recent_memories)
        
        return prompt
    
    async def run_cycle(self, current_state: Dict[str, Any] = None, recent_messages: List[str] = None) -> str:
        """Run one cycle and return character message"""
        if current_state is None:
            current_state = {}
        
        # Store recent messages for use in get_message
        self._current_recent_messages = recent_messages or []
            
        state = SimpleState(
            character_id=self.character_id,
            character_message=current_state.get('character_message', ''),
            tick_count=current_state.get('tick_count', 0)
        )
        
        result = await self.graph.ainvoke(
            state,
            config={"callbacks": [self.opik_tracer]}
        )
        
        return result #result['character_message']
    
    def get_created_traces(self):
        return self.opik_tracer.created_traces()
    
    def flush_traces(self):
        self.opik_tracer.flush()