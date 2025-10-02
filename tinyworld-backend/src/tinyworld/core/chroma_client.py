import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from loguru import logger


class TinyWorldVectorStore:
    """
    Singleton vector store manager for TinyWorld using Chroma.
    Reads its own environment variables and manages the database.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Read environment variables with defaults
        self.persist_directory = Path(os.getenv('CHROMA_PERSIST_DIRECTORY', './data/chroma_db'))
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-large')
        self.collection_prefix = os.getenv('CHROMA_COLLECTION_PREFIX', 'tinyworld')
        
        # Create directory if it doesn't exist
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(model=self.embedding_model)
        
        # Initialize Chroma client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Cache for vector stores
        self._stores = {}
        
        logger.info(f"Initialized TinyWorld vector store at {self.persist_directory}")
        self._initialized = True
    
    def get_collection_name(self, character_id: str, memory_type: str = "general") -> str:
        """Generate standardized collection name"""
        return f"{self.collection_prefix}_{character_id}_{memory_type}"
    
    def get_vector_store(self, collection_name: str = None) -> Chroma:
        """Get or create the single shared vector store"""
        collection_name = "tinyworld-characters-memory"  # Hardcoded single collection
        
        # Return cached store if exists
        if collection_name in self._stores:
            return self._stores[collection_name]
        
        # Ensure collection exists in the persistent client
        try:
            collection = self.client.get_collection(collection_name)
            logger.info(f"Connected to existing collection: {collection_name}")
        except Exception:
            # Collection doesn't exist, create it
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # Default embedding space
            )
            logger.info(f"Created new collection: {collection_name}")
        
        # Create Langchain Chroma wrapper using our existing persistent client
        vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            client=self.client,  # Use existing persistent client
        )
        
        # Cache it
        self._stores[collection_name] = vector_store
        
        return vector_store
    
    def add_memory(
        self,
        character_id: str,
        content: str,
        collection_name: str,  # Move this before default parameters
        memory_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 5.0
    ) -> str:
        """Add a memory to character's vector store"""
        if metadata is None:
            metadata = {}
        
        # Enhance metadata with standard fields
        enhanced_metadata = {
            "character_id": character_id,
            "memory_type": memory_type,
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "importance": importance,
            **metadata
        }
        
        # Create document
        doc = Document(
            page_content=content,
            metadata=enhanced_metadata
        )
        
        # Get vector store and add document
        vector_store = self.get_vector_store(collection_name)
        doc_ids = vector_store.add_documents([doc])
        
        logger.debug(f"Added memory for {character_id}: {content[:50]}...")
        return doc_ids[0] if doc_ids else None
    
    def search_memories(
        self,
        character_id: str,
        query: str,
        memory_type: str = "general",
        k: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for relevant memories"""
        collection_name = self.get_collection_name("tinyworld-characters-memory")
        vector_store = self.get_vector_store(collection_name)
        
        try:
            # Similarity search with scores
            results = vector_store.similarity_search_with_score(query, k=k)
            
            # Filter by score threshold and format results
            filtered_results = []
            for doc, score in results:
                if score >= score_threshold:
                    filtered_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity_score": score
                    })
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error searching memories for {character_id}: {e}")
            return []
    
    def get_recent_memories(
        self,
        character_id: str,
        memory_type: str = "general",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get most recent memories by timestamp"""
        collection_name = self.get_collection_name("characters", memory_type)
        vector_store = self.get_vector_store(collection_name)
        
        try:
            # Get all memories (Chroma doesn't have native sorting, so we'll filter after)
            collection = self.client.get_collection(
                self.get_collection_name(character_id, memory_type)
            )
            
            # Get all documents
            results = collection.get(include=["documents", "metadatas"])
            
            if not results["documents"]:
                return []
            
            # Combine and sort by timestamp
            memories = []
            for i, doc in enumerate(results["documents"]):
                metadata = results["metadatas"][i] if i < len(results["metadatas"]) else {}
                memories.append({
                    "content": doc,
                    "metadata": metadata,
                    "timestamp": metadata.get("timestamp", 0)
                })
            
            # Sort by timestamp descending and limit
            memories.sort(key=lambda x: x["timestamp"], reverse=True)
            return memories[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recent memories for {character_id}: {e}")
            return []
    
    def delete_memory(self, character_id: str, doc_id: str, memory_type: str = "general") -> bool:
        """Delete a specific memory"""
        try:
            collection = self.client.get_collection(
                self.get_collection_name(character_id, memory_type)
            )
            collection.delete(ids=[doc_id])
            logger.debug(f"Deleted memory {doc_id} for {character_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting memory {doc_id} for {character_id}: {e}")
            return False
    
    def clear_character_memories(self, character_id: str, memory_type: str = "general") -> bool:
        """Clear all memories for a character"""
        try:
            collection_name = self.get_collection_name(character_id, memory_type)
            self.client.delete_collection(collection_name)
            
            # Remove from cache
            if collection_name in self._stores:
                del self._stores[collection_name]
            
            logger.info(f"Cleared all {memory_type} memories for {character_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing memories for {character_id}: {e}")
            return False
    
    def get_memory_stats(self, character_id: str, memory_type: str = "general") -> Dict[str, Any]:
        """Get statistics about character's memories"""
        try:
            collection = self.client.get_collection(
                self.get_collection_name(character_id, memory_type)
            )
            
            count = collection.count()
            
            # Get sample of recent memories for analysis
            recent_memories = self.get_recent_memories(character_id, memory_type, limit=5)
            
            return {
                "total_memories": count,
                "memory_type": memory_type,
                "character_id": character_id,
                "recent_memories_count": len(recent_memories),
                "last_memory_time": recent_memories[0]["metadata"].get("datetime") if recent_memories else None
            }
            
        except Exception as e:
            logger.error(f"Error getting memory stats for {character_id}: {e}")
            return {"error": str(e)}
    
    def list_character_collections(self, character_id: str) -> List[str]:
        """List all memory types (collections) for a character"""
        try:
            collections = self.client.list_collections()
            character_collections = []
            
            prefix = f"{self.collection_prefix}_{character_id}_"
            for collection in collections:
                if collection.name.startswith(prefix):
                    memory_type = collection.name.replace(prefix, "")
                    character_collections.append(memory_type)
            
            return character_collections
            
        except Exception as e:
            logger.error(f"Error listing collections for {character_id}: {e}")
            return []
