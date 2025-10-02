import os
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv
from opik import configure 
from opik.integrations.langchain import OpikTracer

# Load environment variables FIRST
# Look for .env file at project root level
project_root = Path(__file__).parent.parent.parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)

logger.info(f"Loading environment variables from: {env_path}")

# Verify critical environment variables are loaded
openai_key = os.getenv('OPENAI_API_KEY')
opik_key = os.getenv('OPIK_API_KEY')
opik_workspace = os.getenv('OPIK_WORKSPACE')

if not openai_key:
    logger.error("OPENAI_API_KEY not found in environment variables!")
    logger.error(f"Looking for .env file at: {env_path}")
    raise ValueError("OPENAI_API_KEY is required but not found in environment variables")

if not opik_key:
    logger.warning("OPIK_API_KEY not found in environment variables. Opik features will be limited.")
if not opik_workspace:
    logger.warning("OPIK_WORKSPACE not found in environment variables. Opik features will be limited.")

logger.info("Environment variables loaded successfully")

def configure_opik():
    """Configure Opik for the application"""
    if not opik_key:
        logger.warning("Skipping Opik configuration - no API key available")
        return False
    
    try:
        configure() 
        logger.info("Opik configured successfully")
        return True
    except Exception as e:
        logger.warning(f"Failed to configure Opik: {e}")
        return False

# Configure on import
configure_opik()