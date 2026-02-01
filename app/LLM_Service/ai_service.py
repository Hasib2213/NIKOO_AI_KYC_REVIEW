from groq import Groq
from config import settings
from app.prompts.system_prompt import SYSTEM_PROMPT, SUMMARY_PROMPT
from typing import List, Dict, Optional
import logging
import asyncio

# Import enhanced services
from app.services.context_manager import context_manager
from app.services.rag_service import rag_service
from app.services.permission_service import permission_service

# Configure logging
logger = logging.getLogger(__name__)

# Groq client initialization
try:
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in environment")
    client = Groq(api_key=settings.GROQ_API_KEY)
    logger.info("Groq client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Groq client: {str(e)}")
    client = None

class GroqService:
    def __init__(self):
        self.model_name = settings.MODEL
        self.client = client
        
        if not self.client:
            raise RuntimeError("Groq client is not initialized")
        
        if not self.model_name:
            raise ValueError("MODEL is not configured")
        
        logger.info(f"GroqService initialized with model: {self.model_name}")

    async def generate_response(self, messages: List[dict], user_id: str) -> str:
        try:
            if not messages:
                raise ValueError("Messages list cannot be empty")
            
            # system prompt add 
            formatted_messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                }
            ]
            
            # User messages add
            for msg in messages:
                if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                    raise ValueError("Invalid message format")
                formatted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            # Groq API call
            logger.info(f"Calling Groq API with {len(formatted_messages)} messages for user {user_id}")
            # Offload blocking Groq API call to a thread to avoid blocking the event loop
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model_name,
                messages=formatted_messages,
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS
            )
            
            if not response.choices or not response.choices[0].message:
                raise ValueError("Empty response from Groq API")
            
            return response.choices[0].message.content.strip()
        
        except ValueError as e:
            logger.warning(f"Validation error for user {user_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error generating response for user {user_id}: {str(e)}")
            raise

# Singleton instance
try:
    groq_service = GroqService()
    logger.info("GroqService singleton created")
except Exception as e:
    logger.error(f"Failed to create GroqService: {str(e)}")
    groq_service = None

async def generate_groq_response(messages: List[dict], user_id: str) -> str:
    if not groq_service:
        raise RuntimeError("GroqService is not available")
    return await groq_service.generate_response(messages, user_id)

async def get_thread_messages(thread_id: str, user_id: str, limit: int = 10) -> List[Dict]:
    """
    Fetch messages from a thread (last 'limit' messages).
    
    Uses MongoDB database to retrieve thread messages.
    
    Args:
        thread_id: ID of the thread
        user_id: ID of the user
        limit: Number of messages to fetch (default: 10)
        
    Returns:
        List of messages with 'role' and 'content' fields
        
    Raises:
        RuntimeError: If database client is not available
        
    Example return format:
        [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
    """
    try:
        from app.database import db_client
        
        if not db_client or not db_client.is_connected():
            raise RuntimeError(
                "Database client not available. "
                "Please ensure MongoDB is running and configured."
            )
        
        # Fetch messages from database
        messages = db_client.get_thread_messages(thread_id, user_id, limit=limit)
        
        if not messages:
            logger.warning(f"No messages found in thread {thread_id} for user {user_id}")
        
        return messages
        
    except RuntimeError as e:
        logger.error(f"Database runtime error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error fetching thread messages: {str(e)}")
        raise RuntimeError(f"Failed to fetch messages: {str(e)}")

async def generate_summary(thread_id: str, user_id: str) -> str:
    """
    Generate a summary of the last 10 messages in a thread.
    
    Args:
        thread_id: ID of the thread
        user_id: ID of the user
        
    Returns:
        Summary string
    """
    if not groq_service:
        raise RuntimeError("GroqService is not available")
    
    try:
        # Fetch last 10 messages from thread via database
        messages = await get_thread_messages(thread_id, user_id, limit=10)
        
        if not messages:
            raise ValueError(f"No messages found in thread {thread_id}")
        
        logger.info(f"Retrieved {len(messages)} messages from thread {thread_id}")
        
        # Prepare the conversation for summarization
        conversation_text = "\n".join([
            f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}"
            for msg in messages
        ])
        
        # Create summary prompt with structured format
        summary_prompt = f"""Please summarize the following conversation thread.

Conversation:
{conversation_text}

{SUMMARY_PROMPT}"""
        
        # Prepare messages for API
        formatted_messages = [
            {
                "role": "system",
                "content": SUMMARY_PROMPT
            },
            {
                "role": "user",
                "content": summary_prompt
            }
        ]
        
        logger.info(f"Generating summary for thread {thread_id}, user {user_id}")
        
        # Call Groq API for summary
        # Offload blocking Groq API call to a thread
        response = await asyncio.to_thread(
            groq_service.client.chat.completions.create,
            model=groq_service.model_name,
            messages=formatted_messages,
            temperature=0.3,  # Lower temperature for more consistent summaries
            max_tokens=300
        )
        
        if not response.choices or not response.choices[0].message:
            raise ValueError("Empty response from Groq API")
        
        summary = response.choices[0].message.content.strip()
        logger.info(f"Summary generated successfully for thread {thread_id}")
        
        return summary
        
    except NotImplementedError as e:
        logger.error(f"Database not implemented: {str(e)}")
        raise
    except ValueError as e:
        logger.warning(f"Validation error for thread {thread_id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error generating summary for thread {thread_id}: {str(e)}")
        raise

async def generate_context_aware_response(
    messages: List[dict], 
    thread_id: str, 
    user_id: str,
    use_rag: bool = True,
    use_user_context: bool = True
) -> str:
    """
    Generate a response with enhanced context awareness.
    Uses context manager, RAG, and user permissions for better responses.
    
    Args:
        messages: List of messages (dict with 'role' and 'content')
        thread_id: ID of the thread
        user_id: ID of the user
        use_rag: Whether to use RAG for document context
        use_user_context: Whether to include user-specific data
        
    Returns:
        Context-aware response string
    """
    if not groq_service:
        raise RuntimeError("GroqService is not available")
    
    try:
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        # Get current user message
        current_message = messages[-1].get("content", "") if messages else ""
        
        # Get user context data if permitted
        user_data = None
        if use_user_context:
            user_data = await permission_service.get_user_context(user_id)
            if user_data:
                logger.info(f"Retrieved user context for {user_id}: {list(user_data.keys())}")
        
        # Build optimized context using context manager
        optimized_messages = await context_manager.build_context_prompt(
            thread_id=thread_id,
            user_id=user_id,
            current_message=current_message,
            user_data=user_data
        )
        
        # Get relevant documentation if RAG is enabled
        doc_context = ""
        if use_rag and rag_service.is_initialized:
            doc_context = await rag_service.get_relevant_context_string(
                current_message,
                k=2,
                max_length=1500
            )
            if doc_context:
                logger.info(f"Retrieved RAG context for thread {thread_id}")
        
        # Build final messages with system prompt
        formatted_messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT + (f"\n\n{doc_context}" if doc_context else "")
            }
        ]
        
        # Add optimized conversation messages
        formatted_messages.extend(optimized_messages)
        
        logger.info(
            f"Generating enhanced response for thread {thread_id} with "
            f"{len(formatted_messages)} messages (RAG: {bool(doc_context)}, "
            f"User context: {bool(user_data)})"
        )
        
        # Call Groq API
        response = await asyncio.to_thread(
            groq_service.client.chat.completions.create,
            model=groq_service.model_name,
            messages=formatted_messages,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS
        )
        
        if not response.choices or not response.choices[0].message:
            raise ValueError("Empty response from Groq API")
        
        return response.choices[0].message.content.strip()
        
    except ValueError as e:
        logger.warning(f"Validation error for thread {thread_id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error generating context-aware response: {str(e)}")
        # Fallback to basic response
        logger.info("Falling back to basic response generation")
        return await groq_service.generate_response(messages, user_id)