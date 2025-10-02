#!/usr/bin/env python3
"""
Simple script to inspect TinyWorld Vector Store contents and configuration.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables first
script_dir = Path(__file__).parent
env_paths = [
    script_dir / '.env',  # Same directory as script
    script_dir.parent / '.env',  # Project root
]

# Try to load .env from multiple locations
env_loaded = False
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        print(f"📄 Loaded environment variables from: {env_path}")
        env_loaded = True
        break

if not env_loaded:
    print("⚠️  No .env file found. Make sure OPENAI_API_KEY is set in environment.")

# Add the src directory to Python path so we can import tinyworld modules
src_path = script_dir / "src"
sys.path.insert(0, str(src_path))

from tinyworld.core.chroma_client import TinyWorldVectorStore


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'=' * 60}")
    print(f"🔍 {title}")
    print('=' * 60)


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n📋 {title}")
    print('-' * 40)


def main():
    print("🚀 TinyWorld Vector Store Inspector")
    
    # Check if OPENAI_API_KEY is available
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("\n❌ OPENAI_API_KEY not found!")
        print("   Create a .env file with:")
        print("   OPENAI_API_KEY=your-api-key-here")
        print(f"   Searched in: {[str(p) for p in env_paths]}")
        return 1
    
    print(f"✅ OPENAI_API_KEY found (length: {len(openai_key)})")
    
    try:
        # Initialize the vector store
        vs = TinyWorldVectorStore()
        
        # 1. Configuration Info
        print_section("Configuration")
        print(f"📁 Persist Directory: {vs.persist_directory}")
        print(f"🤖 Embedding Model: {vs.embedding_model}")
        print(f"🏷️  Collection Prefix: {vs.collection_prefix}")
        print(f"✅ Initialized: {vs._initialized}")
        print(f"🗂️  Cached Stores: {len(vs._stores)}")
        
        if vs._stores:
            print("   Cached collections:")
            for store_name in vs._stores.keys():
                print(f"   • {store_name}")
        
        # 2. All Collections
        print_section("All Collections in Database")
        try:
            all_collections = vs.client.list_collections()
            if all_collections:
                for i, collection in enumerate(all_collections, 1):
                    count = collection.count()
                    print(f"   {i}. {collection.name} ({count} items)")
            else:
                print("   ❌ No collections found")
        except Exception as e:
            print(f"   ❌ Error listing collections: {e}")
        
        # 3. Character Analysis
        print_section("Character Analysis")
        
        # Try to find characters from collection names
        characters = set()
        try:
            for collection in vs.client.list_collections():
                name_parts = collection.name.split('_')
                if len(name_parts) >= 3 and name_parts[0] == vs.collection_prefix:
                    character_id = name_parts[1]
                    characters.add(character_id)
        except Exception as e:
            print(f"   ❌ Error analyzing characters: {e}")
        
        if characters:
            print(f"   Found {len(characters)} character(s):")
            
            for character_id in sorted(characters):
                print(f"\n   🤖 Character: {character_id}")
                
                # Get memory types for this character
                memory_types = vs.list_character_collections(character_id)
                print(f"      Memory Types: {memory_types}")
                
                # Get stats for each memory type
                for memory_type in memory_types:
                    stats = vs.get_memory_stats(character_id, memory_type)
                    if "error" not in stats:
                        print(f"      📊 {memory_type}: {stats['total_memories']} memories")
                        if stats['last_memory_time']:
                            print(f"         Last: {stats['last_memory_time']}")
                        
                        # Show a few recent memories
                        recent = vs.get_recent_memories(character_id, memory_type, limit=3)
                        if recent:
                            print(f"         Recent memories:")
                            for i, memory in enumerate(recent[:3], 1):
                                content = memory['content'][:60] + "..." if len(memory['content']) > 60 else memory['content']
                                importance = memory['metadata'].get('importance', 'N/A')
                                print(f"         {i}. [{importance}] {content}")
                    else:
                        print(f"      ❌ {memory_type}: {stats['error']}")
        else:
            print("   ❌ No characters found")
        
        # 4. Storage Info
        print_section("Storage Information")
        if vs.persist_directory.exists():
            print(f"   📁 Directory exists: {vs.persist_directory}")
            
            # List files in the directory
            try:
                files = list(vs.persist_directory.rglob("*"))
                db_files = [f for f in files if f.is_file()]
                
                print(f"   📄 Files in directory: {len(db_files)}")
                
                # Show some file info
                for file_path in db_files[:5]:  # Show first 5 files
                    size = file_path.stat().st_size
                    size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                    relative_path = file_path.relative_to(vs.persist_directory)
                    print(f"      • {relative_path} ({size_str})")
                    
                if len(db_files) > 5:
                    print(f"      ... and {len(db_files) - 5} more files")
                    
            except Exception as e:
                print(f"   ❌ Error reading directory: {e}")
        else:
            print(f"   ❌ Directory does not exist: {vs.persist_directory}")
        
        # 5. Test Search (if we have data)
        if characters:
            print_section("Sample Search Test")
            test_character = list(characters)[0]
            memory_types = vs.list_character_collections(test_character)
            
            if memory_types:
                test_memory_type = memory_types[0]
                print(f"   Testing search in {test_character}'s {test_memory_type} memories...")
                
                # Try a broad search
                results = vs.search_memories(
                    character_id=test_character,
                    query="thought reality existence",
                    memory_type=test_memory_type,
                    k=3,
                    score_threshold=0.1  # Low threshold for demo
                )
                
                if results:
                    print(f"   🔍 Found {len(results)} matching memories:")
                    for i, result in enumerate(results, 1):
                        content = result['content'][:50] + "..." if len(result['content']) > 50 else result['content']
                        score = result['similarity_score']
                        print(f"      {i}. [{score:.3f}] {content}")
                else:
                    print("   ❌ No matching memories found")
    
    except Exception as e:
        print(f"\n❌ Error initializing vector store: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print(f"\n{'=' * 60}")
    print("✅ Inspection complete!")
    return 0


if __name__ == "__main__":
    exit(main())