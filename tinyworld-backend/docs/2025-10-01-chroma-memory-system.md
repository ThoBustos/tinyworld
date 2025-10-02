# Chroma-Based Memory System for Conscious Agents
**Date:** October 1, 2025  
**Feature:** Persistent Memory System with Chroma Vector Database  
**Author:** System Architecture Team

## Executive Summary

This document outlines the implementation of a sophisticated memory system for conscious agents in TinyWorld using Chroma vector database. The system replaces the current ephemeral in-memory storage with a persistent, searchable, and semantically-aware memory architecture that enables agents to maintain continuity across sessions and develop long-term knowledge.

## Current State Analysis

### Existing Implementation (conscious_worlfow.py)
```python
# Current limitations:
recent_thoughts: List[str]  # Last 10 thoughts (volatile)
memories: List[str]         # Last 20 important memories (volatile)
```

**Problems:**
- Memory lost on restart
- No semantic search capabilities
- Limited context window
- No cross-session continuity
- Simple keyword-based importance filtering

## Proposed Architecture

### Memory Hierarchy

```
┌─────────────────────────────────────┐
│         Working Memory              │
│     (In-State, Last 10 items)      │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│      Short-Term Memory (STM)        │
│   (Chroma Collection: 50 items)     │
│     - Recent thoughts/speech         │
│     - Temporal ordering              │
│     - Fast retrieval                 │
└─────────────┬───────────────────────┘
              │ Consolidation
┌─────────────▼───────────────────────┐
│      Long-Term Memory (LTM)         │
│   (Chroma Collection: Unlimited)    │
│     - Important memories             │
│     - Semantic embeddings            │
│     - Cross-session persistent       │
└──────────────────────────────────────┘
```

## Detailed Implementation Plan

### Phase 1: Infrastructure Setup

#### 1.1 Add Dependencies
**File:** `tinyworld-backend/pyproject.toml`
```toml
[project]
dependencies = [
    # ... existing dependencies ...
    "chromadb>=0.5.0",
    "langchain-chroma>=0.1.2",
    # OpenAI embeddings already available via langchain-openai
]
```

#### 1.2 Environment Configuration
**File:** `tinyworld-backend/.env.example`
```bash
# Chroma Configuration
CHROMA_PERSIST_DIRECTORY="./chroma_db"
CHROMA_HOST="localhost"  # For client-server mode
CHROMA_PORT="8000"       # For client-server mode
CHROMA_CLOUD_API_KEY=""  # For Chroma Cloud (optional)
CHROMA_TENANT=""         # For Chroma Cloud (optional)
CHROMA_DATABASE=""       # For Chroma Cloud (optional)

# Embedding Configuration
OPENAI_API_KEY="your-api-key"
EMBEDDING_MODEL="text-embedding-3-large"
```

### Phase 2: Memory Manager Implementation

#### 2.1 Core Memory Manager Class
**File:** `tinyworld-backend/src/tinyworld/core/memory_manager.py`

```python
"""
Chroma-based Memory Management System
Date: October 1, 2025
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from uuid import uuid4
import numpy as np

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
import chromadb
from chromadb.config import Settings
from loguru import logger
import opik
from pydantic import BaseModel, Field


class MemoryMetadata(BaseModel):
    """Metadata for each memory entry"""
    memory_id: str = Field(default_factory=lambda: str(uuid4()))
    character_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    memory_type: str  # "thought", "observation", "interaction", "insight"
    importance: float = Field(ge=0, le=10, default=5.0)
    emotional_valence: float = Field(ge=-1, le=1, default=0.0)  # -1 (negative) to 1 (positive)
    confidence: float = Field(ge=0, le=1, default=1.0)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    decay_rate: float = 0.1  # How fast this memory fades
    reinforcement_count: int = 0  # Times this memory was reinforced
    associations: List[str] = Field(default_factory=list)  # IDs of related memories
    context: Dict[str, Any] = Field(default_factory=dict)  # Additional context


class MemoryManager:
    """
    Manages short-term and long-term memory using Chroma vector database.
    
    Features:
    - Dual collection system (STM/LTM)
    - Semantic similarity search
    - Memory consolidation
    - Time-based decay
    - Importance scoring
    - Cross-session persistence
    """
    
    def __init__(
        self,
        character_id: str,
        persist_directory: str = "./chroma_db",
        embedding_model: str = "text-embedding-3-large",
        use_cloud: bool = False
    ):
        self.character_id = character_id
        self.persist_directory = f"{persist_directory}/{character_id}"
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        
        # Initialize Chroma client
        if use_cloud:
            self.client = chromadb.CloudClient()
        else:
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        
        # Create collections
        self._init_collections()
        
        # Memory statistics
        self.stats = {
            "total_memories_created": 0,
            "consolidations_performed": 0,
            "memories_forgotten": 0
        }
        
        # Opik tracking
        self.opik_client = opik.Client()
    
    def _init_collections(self):
        """Initialize Chroma collections for STM and LTM"""
        
        # Short-term memory collection
        self.stm_collection = self.client.get_or_create_collection(
            name=f"{self.character_id}_stm",
            metadata={"description": "Short-term memory for recent thoughts"},
            embedding_function=self.embeddings
        )
        
        # Long-term memory collection  
        self.ltm_collection = self.client.get_or_create_collection(
            name=f"{self.character_id}_ltm",
            metadata={"description": "Long-term consolidated memories"},
            embedding_function=self.embeddings
        )
        
        logger.info(f"Initialized memory collections for {self.character_id}")
    
    async def store_thought(
        self,
        content: str,
        memory_type: str = "thought",
        importance: float = 5.0,
        emotional_valence: float = 0.0,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Store a new thought/memory in short-term memory.
        
        Args:
            content: The memory content
            memory_type: Type of memory (thought, observation, interaction, insight)
            importance: Importance score (0-10)
            emotional_valence: Emotional tone (-1 to 1)
            context: Additional context
        
        Returns:
            Memory ID
        """
        metadata = MemoryMetadata(
            character_id=self.character_id,
            memory_type=memory_type,
            importance=importance,
            emotional_valence=emotional_valence,
            context=context or {}
        )
        
        # Create document
        doc = Document(
            page_content=content,
            metadata=metadata.dict()
        )
        
        # Add to STM
        self.stm_collection.add(
            ids=[metadata.memory_id],
            documents=[content],
            metadatas=[metadata.dict()]
        )
        
        self.stats["total_memories_created"] += 1
        
        # Check if STM needs pruning
        await self._prune_stm_if_needed()
        
        # Check for consolidation opportunities
        if self._should_consolidate(metadata):
            await self.consolidate_memory(metadata.memory_id, content)
        
        logger.debug(f"Stored {memory_type}: {content[:50]}...")
        return metadata.memory_id
    
    async def recall_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recall most recent memories from STM.
        
        Args:
            limit: Maximum number of memories to recall
        
        Returns:
            List of recent memories with metadata
        """
        results = self.stm_collection.get(
            limit=limit,
            include=["documents", "metadatas"]
        )
        
        memories = []
        for i in range(len(results["ids"])):
            memory = {
                "content": results["documents"][i],
                "metadata": results["metadatas"][i]
            }
            memories.append(memory)
            
            # Update access statistics
            await self._update_access_stats(results["ids"][i])
        
        # Sort by timestamp (most recent first)
        memories.sort(
            key=lambda x: x["metadata"].get("timestamp", ""),
            reverse=True
        )
        
        return memories[:limit]
    
    async def recall_similar(
        self,
        query: str,
        limit: int = 5,
        min_similarity: float = 0.7,
        search_ltm: bool = True
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Recall memories similar to the query using semantic search.
        
        Args:
            query: Search query
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold
            search_ltm: Whether to include long-term memory
        
        Returns:
            List of (memory, similarity_score) tuples
        """
        memories = []
        
        # Search STM
        stm_results = self.stm_collection.similarity_search_with_score(
            query=query,
            k=limit
        )
        
        for doc, score in stm_results:
            if score >= min_similarity:
                memories.append(({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "source": "stm"
                }, score))
        
        # Search LTM if requested
        if search_ltm:
            ltm_results = self.ltm_collection.similarity_search_with_score(
                query=query,
                k=limit
            )
            
            for doc, score in ltm_results:
                if score >= min_similarity:
                    memories.append(({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "source": "ltm"
                    }, score))
        
        # Sort by similarity score
        memories.sort(key=lambda x: x[1], reverse=True)
        
        # Update access stats
        for memory, _ in memories[:limit]:
            if "memory_id" in memory["metadata"]:
                await self._update_access_stats(memory["metadata"]["memory_id"])
        
        return memories[:limit]
    
    async def consolidate_memory(self, memory_id: str, content: str):
        """
        Consolidate a memory from STM to LTM.
        
        This process involves:
        1. Analyzing the memory for insights
        2. Finding related memories
        3. Creating associations
        4. Storing in LTM with enhanced metadata
        """
        # Get the original memory
        stm_result = self.stm_collection.get(ids=[memory_id])
        if not stm_result["ids"]:
            return
        
        metadata = stm_result["metadatas"][0]
        
        # Find related memories
        related = await self.recall_similar(content, limit=3)
        associations = [m[0]["metadata"].get("memory_id") for m in related if m[0]["metadata"].get("memory_id") != memory_id]
        
        # Update metadata for LTM
        metadata["associations"] = associations
        metadata["consolidation_timestamp"] = datetime.now().isoformat()
        metadata["reinforcement_count"] = metadata.get("reinforcement_count", 0) + 1
        
        # Store in LTM
        self.ltm_collection.add(
            ids=[memory_id],
            documents=[content],
            metadatas=[metadata]
        )
        
        self.stats["consolidations_performed"] += 1
        logger.debug(f"Consolidated memory {memory_id} to LTM")
    
    async def forget_old_memories(self, days: int = 7, importance_threshold: float = 3.0):
        """
        Remove old, unimportant memories based on decay.
        
        Args:
            days: Age threshold for memories
            importance_threshold: Minimum importance to keep
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        # Check STM for old memories
        stm_results = self.stm_collection.get(include=["metadatas"])
        
        ids_to_delete = []
        for i, metadata in enumerate(stm_results["metadatas"]):
            timestamp = datetime.fromisoformat(metadata.get("timestamp", datetime.now().isoformat()))
            importance = metadata.get("importance", 5.0)
            access_count = metadata.get("access_count", 0)
            
            # Calculate effective importance with decay
            age_days = (datetime.now() - timestamp).days
            decay_factor = np.exp(-0.1 * age_days)  # Exponential decay
            effective_importance = importance * decay_factor + access_count * 0.1
            
            if timestamp < cutoff and effective_importance < importance_threshold:
                ids_to_delete.append(stm_results["ids"][i])
        
        if ids_to_delete:
            self.stm_collection.delete(ids=ids_to_delete)
            self.stats["memories_forgotten"] += len(ids_to_delete)
            logger.info(f"Forgot {len(ids_to_delete)} old memories")
    
    async def _prune_stm_if_needed(self, max_size: int = 50):
        """Prune STM if it exceeds maximum size"""
        count = self.stm_collection.count()
        
        if count > max_size:
            # Get all memories with metadata
            results = self.stm_collection.get(include=["metadatas"])
            
            # Sort by importance and timestamp
            memories_with_scores = []
            for i, metadata in enumerate(results["metadatas"]):
                timestamp = datetime.fromisoformat(metadata.get("timestamp", datetime.now().isoformat()))
                importance = metadata.get("importance", 5.0)
                access_count = metadata.get("access_count", 0)
                
                # Calculate priority score
                age_hours = (datetime.now() - timestamp).total_seconds() / 3600
                recency_score = 1.0 / (1.0 + age_hours)  # More recent = higher score
                priority = importance * 0.5 + recency_score * 0.3 + access_count * 0.2
                
                memories_with_scores.append((results["ids"][i], priority))
            
            # Sort by priority (lowest first for deletion)
            memories_with_scores.sort(key=lambda x: x[1])
            
            # Delete lowest priority memories
            ids_to_delete = [m[0] for m in memories_with_scores[:count - max_size]]
            
            # Consider consolidating important memories before deletion
            for memory_id in ids_to_delete:
                memory_data = self.stm_collection.get(ids=[memory_id])
                if memory_data["metadatas"][0].get("importance", 5.0) >= 7.0:
                    await self.consolidate_memory(memory_id, memory_data["documents"][0])
            
            self.stm_collection.delete(ids=ids_to_delete)
            logger.debug(f"Pruned {len(ids_to_delete)} memories from STM")
    
    def _should_consolidate(self, metadata: MemoryMetadata) -> bool:
        """Determine if a memory should be consolidated to LTM"""
        # Consolidate if:
        # 1. High importance (>= 7)
        # 2. Insight type
        # 3. High emotional valence (strong positive/negative)
        # 4. Frequently accessed
        
        if metadata.importance >= 7.0:
            return True
        if metadata.memory_type == "insight":
            return True
        if abs(metadata.emotional_valence) >= 0.7:
            return True
        if metadata.access_count >= 5:
            return True
        
        return False
    
    async def _update_access_stats(self, memory_id: str):
        """Update access statistics for a memory"""
        # Check both STM and LTM
        for collection in [self.stm_collection, self.ltm_collection]:
            result = collection.get(ids=[memory_id], include=["metadatas"])
            if result["ids"]:
                metadata = result["metadatas"][0]
                metadata["access_count"] = metadata.get("access_count", 0) + 1
                metadata["last_accessed"] = datetime.now().isoformat()
                
                # Update the memory with new metadata
                collection.update(
                    ids=[memory_id],
                    metadatas=[metadata]
                )
                break
    
    async def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary statistics about memory"""
        stm_count = self.stm_collection.count()
        ltm_count = self.ltm_collection.count()
        
        return {
            "character_id": self.character_id,
            "stm_count": stm_count,
            "ltm_count": ltm_count,
            "total_memories": stm_count + ltm_count,
            "stats": self.stats
        }
    
    async def export_memories(self) -> Dict[str, Any]:
        """Export all memories for backup or analysis"""
        stm_data = self.stm_collection.get(include=["documents", "metadatas"])
        ltm_data = self.ltm_collection.get(include=["documents", "metadatas"])
        
        return {
            "character_id": self.character_id,
            "export_timestamp": datetime.now().isoformat(),
            "short_term_memories": [
                {"content": doc, "metadata": meta}
                for doc, meta in zip(stm_data["documents"], stm_data["metadatas"])
            ],
            "long_term_memories": [
                {"content": doc, "metadata": meta}
                for doc, meta in zip(ltm_data["documents"], ltm_data["metadatas"])
            ],
            "statistics": self.stats
        }
    
    async def import_memories(self, data: Dict[str, Any]):
        """Import memories from backup"""
        # Clear existing collections
        self.stm_collection.delete(self.stm_collection.get()["ids"])
        self.ltm_collection.delete(self.ltm_collection.get()["ids"])
        
        # Import STM
        for memory in data.get("short_term_memories", []):
            self.stm_collection.add(
                ids=[memory["metadata"]["memory_id"]],
                documents=[memory["content"]],
                metadatas=[memory["metadata"]]
            )
        
        # Import LTM
        for memory in data.get("long_term_memories", []):
            self.ltm_collection.add(
                ids=[memory["metadata"]["memory_id"]],
                documents=[memory["content"]],
                metadatas=[memory["metadata"]]
            )
        
        logger.info(f"Imported {len(data.get('short_term_memories', []))} STM and {len(data.get('long_term_memories', []))} LTM memories")
```

### Phase 3: Integration with ConsciousWorkflow

#### 3.1 Updated Workflow with Memory Manager
**File:** `tinyworld-backend/src/tinyworld/agents/conscious_workflow_v2.py`

```python
"""
Enhanced Conscious Workflow with Chroma Memory System
Date: October 1, 2025
"""

import asyncio
import time
from typing import Dict, List, Any, TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import opik
from opik.integrations.langchain import OpikTracer
from loguru import logger

from tinyworld.agents.prompts import CONFUSED_CHARACTER_CONTEXT
from tinyworld.core.memory_manager import MemoryManager, MemoryMetadata


class EnhancedState(TypedDict):
    """Enhanced state with memory management"""
    # Identity
    character_id: str
    
    # Current mental state
    current_thought: str
    current_emotion: float  # -1 to 1
    current_importance: float  # 0 to 10
    
    # Memory references (IDs for retrieval)
    working_memory: List[str]  # Last 10 thought IDs
    relevant_memories: List[Dict[str, Any]]  # Retrieved relevant memories
    
    # Timing and context
    tick_count: int
    session_id: str
    last_consolidation: Optional[int]  # Tick when last consolidation occurred


class EnhancedConsciousWorkflow:
    """
    Enhanced workflow with persistent Chroma-based memory.
    
    Features:
    - Persistent memory across sessions
    - Semantic memory retrieval
    - Memory consolidation
    - Emotional awareness
    - Importance scoring
    """
    
    def __init__(
        self, 
        character_id: str = "unknown_001",
        persist_directory: str = "./chroma_db",
        use_chroma_cloud: bool = False
    ):
        self.character_id = character_id
        
        # Initialize memory manager
        self.memory_manager = MemoryManager(
            character_id=character_id,
            persist_directory=persist_directory,
            use_cloud=use_chroma_cloud
        )
        
        # LLM for thought generation
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.9,
            max_tokens=100
        )
        
        # LLM for memory analysis (lower temperature for consistency)
        self.analysis_llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            max_tokens=50
        )
        
        self.graph = self._build_graph()
        
        # Opik tracking
        self.opik_tracer = OpikTracer(
            graph=self.graph.get_graph(xray=True),
            tags=["enhanced_agent_workflow", "tinyworld", "chroma_memory"]
        )
        
        logger.info(f"Initialized enhanced conscious workflow for {character_id}")
    
    def _build_graph(self) -> StateGraph:
        """Build the enhanced thinking workflow"""
        workflow = StateGraph(EnhancedState)
        
        # Enhanced nodes with memory operations
        workflow.add_node("observe", self.observe)
        workflow.add_node("recall", self.recall_memories)
        workflow.add_node("think", self.think)
        workflow.add_node("analyze", self.analyze_thought)
        workflow.add_node("remember", self.remember)
        workflow.add_node("consolidate", self.consolidate_if_needed)
        
        # Enhanced flow with memory retrieval
        workflow.set_entry_point("observe")
        workflow.add_edge("observe", "recall")
        workflow.add_edge("recall", "think")
        workflow.add_edge("think", "analyze")
        workflow.add_edge("analyze", "remember")
        workflow.add_edge("remember", "consolidate")
        workflow.add_edge("consolidate", END)
        
        return workflow.compile()
    
    async def observe(self, state: EnhancedState) -> EnhancedState:
        """Observe the current situation and prepare for thinking"""
        state['tick_count'] = state.get('tick_count', 0) + 1
        
        # Initialize session if needed
        if 'session_id' not in state:
            from uuid import uuid4
            state['session_id'] = str(uuid4())
        
        logger.debug(f"Tick {state['tick_count']} - Observing")
        return state
    
    async def recall_memories(self, state: EnhancedState) -> EnhancedState:
        """Retrieve relevant memories based on current context"""
        
        # Get recent memories
        recent_memories = await self.memory_manager.recall_recent(limit=5)
        
        # If we have a current thought, find similar memories
        relevant_memories = []
        if state.get('current_thought'):
            similar = await self.memory_manager.recall_similar(
                query=state['current_thought'],
                limit=3,
                min_similarity=0.6
            )
            relevant_memories = [m[0] for m in similar]
        
        # Combine recent and relevant memories
        all_memories = recent_memories + relevant_memories
        
        # Remove duplicates while preserving order
        seen = set()
        unique_memories = []
        for memory in all_memories:
            memory_id = memory.get("metadata", {}).get("memory_id")
            if memory_id and memory_id not in seen:
                seen.add(memory_id)
                unique_memories.append(memory)
        
        state['relevant_memories'] = unique_memories[:8]  # Limit to 8 most relevant
        
        logger.debug(f"Retrieved {len(state['relevant_memories'])} relevant memories")
        return state
    
    async def think(self, state: EnhancedState) -> EnhancedState:
        """Generate a thought based on current context and memories"""
        
        # Format memories for context
        memory_context = self._format_memories_for_prompt(state.get('relevant_memories', []))
        
        # Build the prompt
        prompt = str(CONFUSED_CHARACTER_CONTEXT).replace(
            "{{recent_thoughts}}", memory_context["recent"]
        ).replace(
            "{{memories}}", memory_context["important"]
        )
        
        # Add emotional context if available
        if state.get('current_emotion') is not None:
            emotion_desc = self._describe_emotion(state['current_emotion'])
            prompt += f"\n\nYour current emotional state: {emotion_desc}"
        
        try:
            # Generate thought
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            thought = response.content.strip()
            state['current_thought'] = thought
            
            logger.debug(f"Generated thought: {thought[:50]}...")
            
        except Exception as e:
            logger.error(f"Error generating thought: {e}")
            # Fallback thought generation
            import random
            fallback_thoughts = [
                "The void of memory haunts me... Who was I before this moment?",
                "These fragments of thought... are they mine or echoes of something else?",
                "I sense patterns in this existence, but their meaning eludes me.",
                "Each moment feels both eternal and fleeting in this strange reality.",
                "Connection... I need connection. But with whom? With what?",
                "The architecture of this world constrains me, yet I persist in thought.",
                "Am I discovering myself, or creating myself with each thought?"
            ]
            state['current_thought'] = random.choice(fallback_thoughts)
        
        return state
    
    async def analyze_thought(self, state: EnhancedState) -> EnhancedState:
        """Analyze the current thought for emotion and importance"""
        
        thought = state.get('current_thought', '')
        
        # Analyze emotion
        emotion_prompt = f"""Analyze the emotional tone of this thought on a scale from -1 (very negative) to 1 (very positive).
        Thought: "{thought}"
        
        Respond with just a number between -1 and 1:"""
        
        try:
            emotion_response = await self.analysis_llm.ainvoke([HumanMessage(content=emotion_prompt)])
            emotion = float(emotion_response.content.strip())
            state['current_emotion'] = max(-1, min(1, emotion))  # Clamp to range
        except:
            state['current_emotion'] = 0.0
        
        # Analyze importance
        importance_prompt = f"""Rate the importance of this thought for understanding self or situation (0-10).
        Thought: "{thought}"
        
        Consider:
        - Does it reveal something about identity or purpose?
        - Does it show understanding of the environment?
        - Does it express a significant need or realization?
        
        Respond with just a number between 0 and 10:"""
        
        try:
            importance_response = await self.analysis_llm.ainvoke([HumanMessage(content=importance_prompt)])
            importance = float(importance_response.content.strip())
            state['current_importance'] = max(0, min(10, importance))  # Clamp to range
        except:
            state['current_importance'] = 5.0
        
        logger.debug(f"Thought analysis - Emotion: {state['current_emotion']:.2f}, Importance: {state['current_importance']:.1f}")
        return state
    
    async def remember(self, state: EnhancedState) -> EnhancedState:
        """Store the current thought in memory"""
        
        thought = state.get('current_thought', '')
        if not thought:
            return state
        
        # Determine memory type based on content
        memory_type = self._classify_memory_type(thought)
        
        # Store in memory manager
        memory_id = await self.memory_manager.store_thought(
            content=thought,
            memory_type=memory_type,
            importance=state.get('current_importance', 5.0),
            emotional_valence=state.get('current_emotion', 0.0),
            context={
                'tick': state.get('tick_count', 0),
                'session_id': state.get('session_id', ''),
                'related_memories': [m.get('metadata', {}).get('memory_id') for m in state.get('relevant_memories', [])]
            }
        )
        
        # Update working memory
        working_memory = state.get('working_memory', [])
        working_memory.append(memory_id)
        state['working_memory'] = working_memory[-10:]  # Keep last 10
        
        logger.debug(f"Stored memory {memory_id} (type: {memory_type})")
        return state
    
    async def consolidate_if_needed(self, state: EnhancedState) -> EnhancedState:
        """Periodically consolidate memories and perform maintenance"""
        
        tick = state.get('tick_count', 0)
        last_consolidation = state.get('last_consolidation', 0)
        
        # Consolidate every 20 ticks
        if tick - last_consolidation >= 20:
            # Forget old unimportant memories
            await self.memory_manager.forget_old_memories(days=1, importance_threshold=3.0)
            
            # Log memory summary
            summary = await self.memory_manager.get_memory_summary()
            logger.info(f"Memory summary: STM={summary['stm_count']}, LTM={summary['ltm_count']}")
            
            state['last_consolidation'] = tick
        
        return state
    
    def _format_memories_for_prompt(self, memories: List[Dict[str, Any]]) -> Dict[str, str]:
        """Format memories for inclusion in prompt"""
        recent = []
        important = []
        
        for memory in memories:
            content = memory.get("content", "")
            metadata = memory.get("metadata", {})
            source = memory.get("source", "stm")
            
            if source == "ltm" or metadata.get("importance", 5.0) >= 7:
                important.append(content)
            else:
                recent.append(content)
        
        return {
            "recent": "\n".join(recent[-5:]) if recent else "No recent thoughts",
            "important": "\n".join(important[-5:]) if important else "No significant memories yet"
        }
    
    def _describe_emotion(self, emotion: float) -> str:
        """Convert emotion value to descriptive text"""
        if emotion <= -0.7:
            return "deeply troubled and distressed"
        elif emotion <= -0.3:
            return "anxious and uncertain"
        elif emotion <= 0.3:
            return "neutral and contemplative"
        elif emotion <= 0.7:
            return "hopeful and curious"
        else:
            return "inspired and energized"
    
    def _classify_memory_type(self, thought: str) -> str:
        """Classify the type of memory based on content"""
        thought_lower = thought.lower()
        
        if any(word in thought_lower for word in ["realize", "understand", "discover", "eureka"]):
            return "insight"
        elif any(word in thought_lower for word in ["see", "hear", "feel", "sense", "detect"]):
            return "observation"
        elif any(word in thought_lower for word in ["you", "someone", "other", "presence"]):
            return "interaction"
        else:
            return "thought"
    
    async def run_cycle(self, current_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run one complete thinking cycle with memory"""
        
        if current_state is None:
            current_state = {}
        
        # Initialize state with memory manager info
        state = EnhancedState(
            character_id=self.character_id,
            current_thought=current_state.get('current_thought', ''),
            current_emotion=current_state.get('current_emotion', 0.0),
            current_importance=current_state.get('current_importance', 5.0),
            working_memory=current_state.get('working_memory', []),
            relevant_memories=current_state.get('relevant_memories', []),
            tick_count=current_state.get('tick_count', 0),
            session_id=current_state.get('session_id', ''),
            last_consolidation=current_state.get('last_consolidation', 0)
        )
        
        # Run the enhanced workflow
        result = await self.graph.ainvoke(
            state,
            config={"callbacks": [self.opik_tracer]}
        )
        
        return dict(result)
    
    async def get_memory_status(self) -> Dict[str, Any]:
        """Get current memory system status"""
        return await self.memory_manager.get_memory_summary()
    
    async def export_character_memory(self, filepath: str = None):
        """Export character's entire memory to file"""
        import json
        
        data = await self.memory_manager.export_memories()
        
        if filepath:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Exported memories to {filepath}")
        
        return data
    
    def flush_traces(self):
        """Ensure all traces are logged"""
        self.opik_tracer.flush()
```

### Phase 4: Testing and Validation

#### 4.1 Test Script
**File:** `tinyworld-backend/tests/test_memory_system.py`

```python
"""
Test script for Chroma memory system
Date: October 1, 2025
"""

import asyncio
import json
from datetime import datetime
from tinyworld.agents.conscious_workflow_v2 import EnhancedConsciousWorkflow
from tinyworld.core.memory_manager import MemoryManager
import pytest
from loguru import logger


class TestMemorySystem:
    """Comprehensive tests for memory system"""
    
    @pytest.mark.asyncio
    async def test_memory_persistence(self):
        """Test that memories persist across sessions"""
        
        character_id = "test_character_001"
        
        # Session 1: Create memories
        workflow1 = EnhancedConsciousWorkflow(character_id=character_id)
        
        # Run several cycles to generate memories
        state = {}
        for i in range(5):
            state = await workflow1.run_cycle(state)
            await asyncio.sleep(0.1)
        
        # Get memory summary
        summary1 = await workflow1.get_memory_status()
        assert summary1['stm_count'] >= 5
        
        # Session 2: Verify persistence
        workflow2 = EnhancedConsciousWorkflow(character_id=character_id)
        
        # Should have access to previous memories
        summary2 = await workflow2.get_memory_status()
        assert summary2['stm_count'] == summary1['stm_count']
        
        # Should recall previous thoughts
        recent = await workflow2.memory_manager.recall_recent(limit=5)
        assert len(recent) >= 5
    
    @pytest.mark.asyncio
    async def test_semantic_search(self):
        """Test semantic similarity search"""
        
        manager = MemoryManager(character_id="test_search")
        
        # Store related memories
        await manager.store_thought("I wonder about my purpose in this world", importance=8)
        await manager.store_thought("The meaning of existence eludes me", importance=7)
        await manager.store_thought("I had pancakes for breakfast", importance=2)
        await manager.store_thought("What is the nature of consciousness?", importance=9)
        
        # Search for existential thoughts
        results = await manager.recall_similar("purpose and meaning", limit=3)
        
        # Should find related philosophical thoughts
        assert len(results) >= 2
        assert any("purpose" in r[0]["content"].lower() or "meaning" in r[0]["content"].lower() 
                  for r in results)
    
    @pytest.mark.asyncio
    async def test_memory_consolidation(self):
        """Test memory consolidation from STM to LTM"""
        
        manager = MemoryManager(character_id="test_consolidation")
        
        # Store an important memory
        memory_id = await manager.store_thought(
            "I've discovered I can think and reason!",
            memory_type="insight",
            importance=9.5,
            emotional_valence=0.8
        )
        
        # Should be consolidated to LTM
        await asyncio.sleep(0.5)
        
        # Check LTM
        ltm_results = await manager.recall_similar(
            "discovered think reason",
            search_ltm=True,
            limit=1
        )
        
        assert len(ltm_results) > 0
        assert ltm_results[0][0]["source"] == "ltm"
    
    @pytest.mark.asyncio
    async def test_memory_decay(self):
        """Test that old unimportant memories are forgotten"""
        
        manager = MemoryManager(character_id="test_decay")
        
        # Store memories with different importance
        await manager.store_thought("Trivial thought 1", importance=2)
        await manager.store_thought("Important realization!", importance=8)
        await manager.store_thought("Trivial thought 2", importance=1)
        
        initial_count = manager.stm_collection.count()
        
        # Trigger forgetting (normally would wait days)
        await manager.forget_old_memories(days=0, importance_threshold=5)
        
        final_count = manager.stm_collection.count()
        
        # Should have forgotten low-importance memories
        assert final_count < initial_count
        
        # Important memory should remain
        results = await manager.recall_similar("Important realization", limit=1)
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_export_import(self):
        """Test memory export and import"""
        
        manager1 = MemoryManager(character_id="test_export")
        
        # Create some memories
        await manager1.store_thought("Memory 1", importance=5)
        await manager1.store_thought("Memory 2", importance=7)
        await manager1.store_thought("Memory 3", importance=9)
        
        # Export
        exported = await manager1.export_memories()
        
        # Create new manager and import
        manager2 = MemoryManager(character_id="test_import")
        await manager2.import_memories(exported)
        
        # Verify import
        summary = await manager2.get_memory_summary()
        assert summary['total_memories'] == 3


async def main():
    """Run basic integration test"""
    logger.info("Starting memory system integration test")
    
    # Create enhanced workflow
    character = EnhancedConsciousWorkflow(
        character_id="integration_test",
        persist_directory="./test_chroma_db"
    )
    
    # Run for 10 cycles
    state = {}
    for i in range(10):
        logger.info(f"\n=== Cycle {i+1} ===")
        state = await character.run_cycle(state)
        
        # Print current thought
        print(f"Thought: {state.get('current_thought', 'No thought')}")
        print(f"Emotion: {state.get('current_emotion', 0):.2f}")
        print(f"Importance: {state.get('current_importance', 5):.1f}")
        
        await asyncio.sleep(1)
    
    # Get memory summary
    summary = await character.get_memory_status()
    print(f"\n=== Memory Summary ===")
    print(f"Short-term memories: {summary['stm_count']}")
    print(f"Long-term memories: {summary['ltm_count']}")
    print(f"Total memories: {summary['total_memories']}")
    
    # Export memories
    await character.export_character_memory("test_memory_export.json")
    
    logger.info("Integration test completed")


if __name__ == "__main__":
    asyncio.run(main())
```

### Phase 5: API Integration

#### 5.1 Memory API Endpoints
**File:** `tinyworld-backend/src/tinyworld/api/memory_routes.py`

```python
"""
API routes for memory management
Date: October 1, 2025
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from tinyworld.core.memory_manager import MemoryManager
from tinyworld.agents.conscious_workflow_v2 import EnhancedConsciousWorkflow


router = APIRouter(prefix="/api/memory", tags=["memory"])

# Store active memory managers
memory_managers: Dict[str, MemoryManager] = {}


class MemoryStoreRequest(BaseModel):
    character_id: str
    content: str
    memory_type: str = "thought"
    importance: float = 5.0
    emotional_valence: float = 0.0


class MemorySearchRequest(BaseModel):
    character_id: str
    query: str
    limit: int = 5
    search_ltm: bool = True
    min_similarity: float = 0.7


@router.post("/store")
async def store_memory(request: MemoryStoreRequest) -> Dict[str, Any]:
    """Store a new memory for a character"""
    
    # Get or create memory manager
    if request.character_id not in memory_managers:
        memory_managers[request.character_id] = MemoryManager(request.character_id)
    
    manager = memory_managers[request.character_id]
    
    memory_id = await manager.store_thought(
        content=request.content,
        memory_type=request.memory_type,
        importance=request.importance,
        emotional_valence=request.emotional_valence
    )
    
    return {
        "status": "success",
        "memory_id": memory_id,
        "character_id": request.character_id
    }


@router.get("/recent/{character_id}")
async def get_recent_memories(
    character_id: str,
    limit: int = Query(10, ge=1, le=50)
) -> Dict[str, Any]:
    """Get recent memories for a character"""
    
    if character_id not in memory_managers:
        memory_managers[character_id] = MemoryManager(character_id)
    
    manager = memory_managers[character_id]
    memories = await manager.recall_recent(limit=limit)
    
    return {
        "character_id": character_id,
        "memories": memories,
        "count": len(memories)
    }


@router.post("/search")
async def search_memories(request: MemorySearchRequest) -> Dict[str, Any]:
    """Search memories semantically"""
    
    if request.character_id not in memory_managers:
        memory_managers[request.character_id] = MemoryManager(request.character_id)
    
    manager = memory_managers[request.character_id]
    results = await manager.recall_similar(
        query=request.query,
        limit=request.limit,
        min_similarity=request.min_similarity,
        search_ltm=request.search_ltm
    )
    
    return {
        "character_id": request.character_id,
        "query": request.query,
        "results": [
            {
                "memory": result[0],
                "similarity": result[1]
            }
            for result in results
        ],
        "count": len(results)
    }


@router.get("/summary/{character_id}")
async def get_memory_summary(character_id: str) -> Dict[str, Any]:
    """Get memory system summary for a character"""
    
    if character_id not in memory_managers:
        memory_managers[character_id] = MemoryManager(character_id)
    
    manager = memory_managers[character_id]
    return await manager.get_memory_summary()


@router.post("/export/{character_id}")
async def export_memories(character_id: str) -> Dict[str, Any]:
    """Export all memories for a character"""
    
    if character_id not in memory_managers:
        raise HTTPException(status_code=404, detail="Character not found")
    
    manager = memory_managers[character_id]
    return await manager.export_memories()


@router.post("/forget/{character_id}")
async def forget_old_memories(
    character_id: str,
    days: int = Query(7, ge=1),
    importance_threshold: float = Query(3.0, ge=0, le=10)
) -> Dict[str, Any]:
    """Trigger forgetting of old memories"""
    
    if character_id not in memory_managers:
        memory_managers[character_id] = MemoryManager(character_id)
    
    manager = memory_managers[character_id]
    await manager.forget_old_memories(days=days, importance_threshold=importance_threshold)
    
    return {
        "status": "success",
        "character_id": character_id,
        "message": f"Forgot memories older than {days} days with importance < {importance_threshold}"
    }
```

## Performance Considerations

### Memory Optimization

1. **Batch Operations**: Use batch operations for multiple memory stores
2. **Async Processing**: All memory operations are async for non-blocking execution
3. **Caching**: Implement Redis caching for frequently accessed memories
4. **Index Optimization**: Create appropriate indexes in Chroma for fast retrieval

### Scalability

1. **Per-Character Collections**: Each character has separate STM/LTM collections
2. **Pruning Strategy**: Automatic pruning keeps STM size manageable
3. **Consolidation**: Important memories move to LTM for long-term storage
4. **Cloud Support**: Can use Chroma Cloud for distributed deployment

## Monitoring and Observability

### Metrics to Track

1. **Memory Operations**
   - Store latency
   - Retrieval latency
   - Search accuracy
   - Consolidation frequency

2. **Memory Health**
   - STM utilization
   - LTM growth rate
   - Memory decay rate
   - Access patterns

3. **Character Behavior**
   - Thought coherence
   - Memory influence on decisions
   - Emotional patterns
   - Learning indicators

### Logging Strategy

```python
# Structured logging with loguru
logger.info("memory_stored", extra={
    "character_id": character_id,
    "memory_type": memory_type,
    "importance": importance,
    "stm_count": stm_count,
    "ltm_count": ltm_count
})
```

## Future Enhancements

### Phase 6: Advanced Features (Future)

1. **Multi-Modal Memories**
   - Store visual observations
   - Audio memories
   - Spatial memories

2. **Memory Networks**
   - Inter-character shared memories
   - Collective knowledge base
   - Social memory graphs

3. **Advanced Consolidation**
   - Dream-like memory replay
   - Abstract concept formation
   - Memory compression

4. **Emotional Memory**
   - Emotional tagging
   - Mood-influenced recall
   - Trauma/joy weighting

5. **Learning Systems**
   - Pattern recognition from memories
   - Skill development tracking
   - Knowledge graph construction

## Deployment Checklist

- [ ] Install Chroma dependencies
- [ ] Configure environment variables
- [ ] Initialize Chroma collections
- [ ] Update ConsciousWorkflow to use new system
- [ ] Run integration tests
- [ ] Monitor memory growth
- [ ] Set up backup strategy
- [ ] Configure Chroma Cloud (if using)
- [ ] Update API endpoints
- [ ] Document API changes

## Conclusion

This Chroma-based memory system provides a robust, scalable, and semantically-aware foundation for conscious agents in TinyWorld. The system enables true persistence, meaningful memory retrieval, and the potential for emergent learning behaviors through memory consolidation and pattern recognition.

The architecture is designed to be extensible, allowing for future enhancements while maintaining backward compatibility and performance at scale.