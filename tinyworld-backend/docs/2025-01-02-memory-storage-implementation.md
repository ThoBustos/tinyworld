# TinyWorld Memory Storage Implementation
**Date**: 2025-01-02  
**Author**: Thomas

## Overview
Implementation of a dual-storage system for TinyWorld character memories using PostgreSQL for recent messages and Chroma vector store for long-term semantic memories.

## Architecture

```
┌─────────────────────────────────────────────────┐
│            ConsciousWorkflow                     │
│                    │                             │
│         ┌──────────┴──────────┐                 │
│         ▼                     ▼                 │
│   MemoryRepository      VectorStore             │
│         │                     │                 │
│         ▼                     ▼                 │
│    PostgreSQL            ChromaDB               │
│  (Recent Messages)    (Semantic Search)         │
└─────────────────────────────────────────────────┘
```

## Database Configuration

### 1. Update Configuration (`src/tinyworld/core/config.py`)

Add database configuration settings:

```python
import os
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

# Existing imports...

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    host: str = "localhost"
    port: int = 5432
    database: str = "tinyworld"
    user: str = "tinyworld_user"
    password: Optional[str] = None
    echo: bool = False  # SQLAlchemy echo mode
    pool_size: int = 5
    max_overflow: int = 10
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create config from environment variables"""
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'tinyworld'),
            user=os.getenv('DB_USER', 'tinyworld_user'),
            password=os.getenv('DB_PASSWORD'),
            echo=os.getenv('DB_ECHO', 'false').lower() == 'true',
            pool_size=int(os.getenv('DB_POOL_SIZE', '5')),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '10'))
        )
    
    @property
    def database_url(self) -> str:
        """Generate PostgreSQL connection URL"""
        if self.password:
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        return f"postgresql://{self.user}@{self.host}:{self.port}/{self.database}"

@dataclass
class MemoryConfig:
    """Memory system configuration"""
    max_recent_messages: int = 10
    max_stored_messages_per_character: int = 1000
    cleanup_interval_hours: int = 24
    vector_store_collection: str = "tinyworld-memories"
    
    @classmethod
    def from_env(cls) -> 'MemoryConfig':
        """Create config from environment variables"""
        return cls(
            max_recent_messages=int(os.getenv('MAX_RECENT_MESSAGES', '10')),
            max_stored_messages_per_character=int(os.getenv('MAX_STORED_MESSAGES', '1000')),
            cleanup_interval_hours=int(os.getenv('CLEANUP_INTERVAL_HOURS', '24')),
            vector_store_collection=os.getenv('VECTOR_STORE_COLLECTION', 'tinyworld-memories')
        )

# Initialize configs
db_config = DatabaseConfig.from_env()
memory_config = MemoryConfig.from_env()
```

### 2. Environment Variables (`.env`)

Add to your `.env` file:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tinyworld
DB_USER=tinyworld_user
DB_PASSWORD=your_secure_password
DB_ECHO=false

# Memory Configuration
MAX_RECENT_MESSAGES=10
MAX_STORED_MESSAGES_PER_CHARACTER=1000
CLEANUP_INTERVAL_HOURS=24
VECTOR_STORE_COLLECTION=tinyworld-memories
```

## Database Models

### 3. Base Model (`src/tinyworld/models/base.py`)

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from tinyworld.core.config import db_config

Base = declarative_base()

# Create engine
engine = create_engine(
    db_config.database_url,
    pool_size=db_config.pool_size,
    max_overflow=db_config.max_overflow,
    echo=db_config.echo
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Provide a transactional scope for database operations"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

### 4. Message Model (`src/tinyworld/models/message.py`)

```python
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, Index
from sqlalchemy.sql import func
from datetime import datetime

from tinyworld.models.base import Base

class Message(Base):
    """Character message model for recent memory storage"""
    __tablename__ = "messages"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core fields
    character_id = Column(String(100), nullable=False)
    character_name = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    
    # Timing fields
    tick_count = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Metadata
    message_type = Column(String(50), default="reflection")  # reflection, action, dialogue
    importance = Column(Float, default=5.0)
    metadata = Column(JSON, default={})
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_character_timestamp', 'character_id', 'timestamp'),
        Index('idx_character_tick', 'character_id', 'tick_count'),
        Index('idx_message_type', 'message_type'),
    )
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'character_id': self.character_id,
            'character_name': self.character_name,
            'content': self.content,
            'tick_count': self.tick_count,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'message_type': self.message_type,
            'importance': self.importance,
            'metadata': self.metadata
        }
```

### 5. Character State Model (`src/tinyworld/models/character_state.py`)

```python
from sqlalchemy import Column, Integer, String, Float, JSON, DateTime
from sqlalchemy.sql import func

from tinyworld.models.base import Base

class CharacterState(Base):
    """Persistent character state tracking"""
    __tablename__ = "character_states"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Character identification
    character_id = Column(String(100), unique=True, nullable=False)
    character_name = Column(String(100), nullable=False)
    
    # State tracking
    current_tick = Column(Integer, default=0)
    last_decision_time = Column(Float, default=0.0)
    
    # Character configuration
    personality = Column(JSON, default={})
    beliefs = Column(JSON, default={})
    goals = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            'character_id': self.character_id,
            'character_name': self.character_name,
            'current_tick': self.current_tick,
            'last_decision_time': self.last_decision_time,
            'personality': self.personality,
            'beliefs': self.beliefs,
            'goals': self.goals
        }
```

## Repository Layer

### 6. Memory Repository (`src/tinyworld/repositories/memory_repository.py`)

```python
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import desc, and_
from sqlalchemy.orm import Session
from loguru import logger

from tinyworld.models.base import get_db
from tinyworld.models.message import Message
from tinyworld.models.character_state import CharacterState
from tinyworld.core.config import memory_config

class MemoryRepository:
    """Repository for managing character memories in PostgreSQL"""
    
    def save_message(
        self,
        character_id: str,
        character_name: str,
        content: str,
        tick_count: int,
        message_type: str = "reflection",
        importance: float = 5.0,
        metadata: Dict[str, Any] = None
    ) -> int:
        """Save a new message to the database"""
        with get_db() as db:
            message = Message(
                character_id=character_id,
                character_name=character_name,
                content=content,
                tick_count=tick_count,
                message_type=message_type,
                importance=importance,
                metadata=metadata or {}
            )
            db.add(message)
            db.commit()
            db.refresh(message)
            
            # Cleanup old messages if needed
            self._cleanup_old_messages(db, character_id)
            
            logger.info(f"Saved message {message.id} for {character_name}")
            return message.id
    
    def get_recent_messages(
        self,
        character_id: str,
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """Get recent messages for a character"""
        limit = limit or memory_config.max_recent_messages
        
        with get_db() as db:
            messages = db.query(Message).filter(
                Message.character_id == character_id
            ).order_by(
                desc(Message.timestamp)
            ).limit(limit).all()
            
            # Return in chronological order (oldest first)
            return [msg.to_dict() for msg in reversed(messages)]
    
    def get_messages_by_tick_range(
        self,
        character_id: str,
        start_tick: int,
        end_tick: int
    ) -> List[Dict[str, Any]]:
        """Get messages within a tick range"""
        with get_db() as db:
            messages = db.query(Message).filter(
                and_(
                    Message.character_id == character_id,
                    Message.tick_count >= start_tick,
                    Message.tick_count <= end_tick
                )
            ).order_by(Message.tick_count).all()
            
            return [msg.to_dict() for msg in messages]
    
    def get_messages_by_type(
        self,
        character_id: str,
        message_type: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get messages of a specific type"""
        with get_db() as db:
            messages = db.query(Message).filter(
                and_(
                    Message.character_id == character_id,
                    Message.message_type == message_type
                )
            ).order_by(
                desc(Message.timestamp)
            ).limit(limit).all()
            
            return [msg.to_dict() for msg in messages]
    
    def update_character_state(
        self,
        character_id: str,
        character_name: str,
        tick_count: int,
        last_decision_time: float,
        **kwargs
    ) -> None:
        """Update or create character state"""
        with get_db() as db:
            state = db.query(CharacterState).filter(
                CharacterState.character_id == character_id
            ).first()
            
            if state:
                state.current_tick = tick_count
                state.last_decision_time = last_decision_time
                for key, value in kwargs.items():
                    if hasattr(state, key):
                        setattr(state, key, value)
            else:
                state = CharacterState(
                    character_id=character_id,
                    character_name=character_name,
                    current_tick=tick_count,
                    last_decision_time=last_decision_time,
                    **kwargs
                )
                db.add(state)
            
            db.commit()
    
    def get_character_state(self, character_id: str) -> Optional[Dict[str, Any]]:
        """Get character state"""
        with get_db() as db:
            state = db.query(CharacterState).filter(
                CharacterState.character_id == character_id
            ).first()
            
            return state.to_dict() if state else None
    
    def _cleanup_old_messages(self, db: Session, character_id: str) -> None:
        """Remove old messages beyond the retention limit"""
        # Count messages for this character
        count = db.query(Message).filter(
            Message.character_id == character_id
        ).count()
        
        if count > memory_config.max_stored_messages_per_character:
            # Get the ID of the nth message (to keep)
            nth_message = db.query(Message.id).filter(
                Message.character_id == character_id
            ).order_by(
                desc(Message.timestamp)
            ).offset(
                memory_config.max_stored_messages_per_character - 1
            ).first()
            
            if nth_message:
                # Delete messages older than the nth message
                db.query(Message).filter(
                    and_(
                        Message.character_id == character_id,
                        Message.id < nth_message[0]
                    )
                ).delete()
                
                logger.info(f"Cleaned up old messages for {character_id}")
```

## Package Management with UV

### 7. Update pyproject.toml

Add the required dependencies to your `pyproject.toml`:

```toml
[project]
name = "tinyworld-backend"
version = "0.1.0"
description = "TinyWorld character simulation backend"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "websockets>=12.0",
    "python-dotenv>=1.0.0",
    "loguru>=0.7.0",
    "langchain>=0.1.0",
    "langchain-openai>=0.0.5",
    "langchain-chroma>=0.1.0",
    "chromadb>=0.4.0",
    "opik>=0.1.0",
    "sqlalchemy>=2.0.0",
    "psycopg2-binary>=2.9.0",
    "alembic>=1.13.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
```

### 8. Install Dependencies with UV

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or on macOS with Homebrew
brew install uv

# Navigate to backend directory
cd tinyworld-backend

# Install all dependencies
uv sync

# Or install specific packages
uv pip install sqlalchemy psycopg2-binary alembic

# Run with uv
uv run python src/main.py
```

## Alembic Setup with UV

### 9. Initialize Alembic

```bash
# In tinyworld-backend directory
uv run alembic init alembic
```

### 10. Configure Alembic (`alembic.ini`)

Update the sqlalchemy.url line:

```ini
# Remove or comment out the default URL
# sqlalchemy.url = driver://user:pass@localhost/dbname

# We'll set it programmatically in env.py
```

### 11. Alembic Environment (`alembic/env.py`)

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import your models and config
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tinyworld.models.base import Base
from tinyworld.models.message import Message
from tinyworld.models.character_state import CharacterState
from tinyworld.core.config import db_config

# this is the Alembic Config object
config = context.config

# Set the database URL from our config
config.set_main_option('sqlalchemy.url', db_config.database_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 12. Create Initial Migration

```bash
# Create the database first (if not exists)
createdb tinyworld

# Generate initial migration with uv
uv run alembic revision --autogenerate -m "Initial migration: messages and character_states tables"

# Apply migration with uv
uv run alembic upgrade head
```

## Integration with ConsciousWorkflow

### 13. Update ConsciousWorkflow (`src/tinyworld/agents/conscious_workflow.py`)

```python
# Add to imports
from tinyworld.repositories.memory_repository import MemoryRepository

class ConsciousWorkflow:
    def __init__(self, character_id: str = "socrates_001"):
        # Existing initialization...
        
        # Add repository
        self.memory_repo = MemoryRepository()
    
    async def save_memory(self, state: SimpleState) -> SimpleState:
        """Save the character message in PostgreSQL and vector store"""
        try:
            # Save to PostgreSQL for recent access
            message_id = self.memory_repo.save_message(
                character_id=state['character_id'],
                character_name=self.config['name'],
                content=state['character_message'],
                tick_count=state['tick_count'],
                message_type="reflection",
                importance=5.0,
                metadata={
                    "personality": self.config['personality'],
                    "mission": self.config['mission']
                }
            )
            
            # Also save to vector store for semantic search
            self.vector_store.add_memory(
                character_id="characters",
                content=state['character_message'],
                collection_name="tinyworld-characters-memory",
                memory_type="long-term",
                metadata={
                    "message_id": message_id,  # Link to PostgreSQL record
                    "character": self.config['name'],
                    "tick_count": state['tick_count']
                },
                importance=5.0
            )
            
            # Update character state
            self.memory_repo.update_character_state(
                character_id=state['character_id'],
                character_name=self.config['name'],
                tick_count=state['tick_count'],
                last_decision_time=time.time(),
                personality=self.config.get('personality_data', {}),
                beliefs=self.config.get('initial_beliefs_data', {}),
                goals=self.config.get('goals', {})
            )
            
            logger.info(f"💾 Saved message {message_id} for {self.config['name']}")
            
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
        
        return state
    
    def _get_recent_memories(self) -> List[str]:
        """Get recent memories from PostgreSQL"""
        try:
            # Get last 10 messages from PostgreSQL
            recent_messages = self.memory_repo.get_recent_messages(
                character_id=self.character_id,
                limit=10
            )
            
            # Extract just the content
            return [msg['content'] for msg in recent_messages]
            
        except Exception as e:
            logger.error(f"Error getting recent memories: {e}")
            return []
```

## Database Management Commands with UV

### 14. Management Script (`scripts/db_management.py`)

```python
#!/usr/bin/env python3
"""Database management utilities"""

import sys
import argparse
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tinyworld.models.base import engine, Base
from tinyworld.repositories.memory_repository import MemoryRepository
from loguru import logger

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

def drop_tables():
    """Drop all database tables"""
    response = input("Are you sure you want to drop all tables? (yes/no): ")
    if response.lower() == 'yes':
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped")
    else:
        logger.info("Operation cancelled")

def show_recent_messages(character_id: str, limit: int = 10):
    """Show recent messages for a character"""
    repo = MemoryRepository()
    messages = repo.get_recent_messages(character_id, limit)
    
    for msg in messages:
        print(f"[{msg['timestamp']}] {msg['character_name']}: {msg['content']}")

def main():
    parser = argparse.ArgumentParser(description='Database management')
    parser.add_argument('action', choices=['create', 'drop', 'show-messages'])
    parser.add_argument('--character-id', default='socrates_001')
    parser.add_argument('--limit', type=int, default=10)
    
    args = parser.parse_args()
    
    if args.action == 'create':
        create_tables()
    elif args.action == 'drop':
        drop_tables()
    elif args.action == 'show-messages':
        show_recent_messages(args.character_id, args.limit)

if __name__ == '__main__':
    main()
```

Run the management script with uv:
```bash
uv run python scripts/db_management.py create
uv run python scripts/db_management.py show-messages --character-id socrates_001
```

## Usage Example with UV

### 15. Complete Integration Example

```python
from tinyworld.repositories.memory_repository import MemoryRepository
from tinyworld.core.chroma_client import TinyWorldVectorStore

class EnhancedMemoryManager:
    """Manages both recent and long-term memories"""
    
    def __init__(self, character_id: str):
        self.character_id = character_id
        self.memory_repo = MemoryRepository()
        self.vector_store = TinyWorldVectorStore()
    
    def get_context_for_prompt(self, current_situation: str = None) -> Dict[str, Any]:
        """Get both recent and relevant memories for prompt context"""
        
        # Get recent messages (temporal context)
        recent_messages = self.memory_repo.get_recent_messages(
            self.character_id, 
            limit=10
        )
        
        # Get relevant memories (semantic context)
        relevant_memories = []
        if current_situation:
            results = self.vector_store.similarity_search(
                query=current_situation,
                k=5
            )
            relevant_memories = [r['content'] for r in results]
        
        return {
            'recent_context': recent_messages,
            'relevant_memories': relevant_memories,
            'character_state': self.memory_repo.get_character_state(self.character_id)
        }
```

## Deployment Steps with UV

1. **Install PostgreSQL** (if not already installed)
   ```bash
   # macOS
   brew install postgresql
   brew services start postgresql
   
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   sudo systemctl start postgresql
   ```

2. **Create Database and User**
   ```sql
   -- Connect as superuser
   psql -U postgres
   
   -- Create user and database
   CREATE USER tinyworld_user WITH PASSWORD 'your_secure_password';
   CREATE DATABASE tinyworld OWNER tinyworld_user;
   GRANT ALL PRIVILEGES ON DATABASE tinyworld TO tinyworld_user;
   ```

3. **Install Python Dependencies with UV**
   ```bash
   # Install uv
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Navigate to backend
   cd tinyworld-backend
   
   # Sync all dependencies
   uv sync
   ```

4. **Run Migrations**
   ```bash
   cd tinyworld-backend
   uv run alembic upgrade head
   ```

5. **Verify Installation**
   ```bash
   uv run python scripts/db_management.py create
   ```

6. **Run the Application**
   ```bash
   uv run python src/main.py
   ```

## Development Workflow with UV

```bash
# Install new package
uv add package-name

# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run black src/

# Lint code
uv run ruff check src/

# Run specific script
uv run python scripts/script_name.py

# Create virtual environment (uv handles this automatically)
uv venv

# Update all dependencies
uv sync --upgrade
```

## Monitoring and Maintenance

### Database Queries for Monitoring

```sql
-- Check message count per character
SELECT character_id, character_name, COUNT(*) as message_count
FROM messages
GROUP BY character_id, character_name;

-- Get recent messages
SELECT * FROM messages
WHERE character_id = 'socrates_001'
ORDER BY timestamp DESC
LIMIT 10;

-- Check database size
SELECT pg_database_size('tinyworld') / 1024 / 1024 as size_mb;

-- Message distribution by type
SELECT message_type, COUNT(*) as count
FROM messages
GROUP BY message_type;
```

### Backup Strategy

```bash
# Daily backup script
pg_dump -U tinyworld_user -d tinyworld > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -U tinyworld_user -d tinyworld < backup_20250102.sql
```

## Performance Considerations

1. **Indexes**: Already defined on (character_id, timestamp) for fast queries
2. **Connection Pooling**: Configured in SQLAlchemy with pool_size=5
3. **Message Cleanup**: Automatic retention of last 1000 messages per character
4. **Query Optimization**: Use limit clauses and avoid full table scans

## Next Steps

1. Implement message archival system for long-term storage
2. Add message compression for older entries
3. Create admin dashboard for memory management
4. Implement memory importance scoring algorithm
5. Add memory consolidation/summarization for old messages