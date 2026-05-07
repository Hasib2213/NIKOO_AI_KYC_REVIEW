from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
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

# Gemini client initialization
try:
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in environment")
    model_name = settings.GEMINI_MODEL or settings.MODEL
    client = ChatGoogleGenerativeAI(
        api_key=settings.GEMINI_API_KEY,
        model=model_name,
        temperature=settings.TEMPERATURE,
        max_output_tokens=settings.MAX_TOKENS,
    )
    logger.info("Gemini client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini client: {str(e)}")
    client = None

class GeminiService:
    def __init__(self):
        self.model_name = settings.GEMINI_MODEL or settings.MODEL
        self.client = client
        
        if not self.client:
            raise RuntimeError("Gemini client is not initialized")
        
        logger.info(f"GeminiService initialized with model: {self.model_name}")

    @staticmethod
    def _to_lc_messages(messages: List[dict]):
        lc_messages = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            else:
                lc_messages.append(HumanMessage(content=content))
        return lc_messages

    @staticmethod
    def _normalize_content(content) -> str:
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    parts.append(item["text"])
                else:
                    parts.append(str(item))
            return "".join(parts)
        return str(content)

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

            # Gemini API call
            logger.info(f"Calling Gemini API with {len(formatted_messages)} messages for user {user_id}")
            # Offload blocking Gemini API call to a thread to avoid blocking the event loop
            response = await asyncio.to_thread(
                self.client.invoke,
                self._to_lc_messages(formatted_messages),
            )
            
            if not response or response.content is None:
                raise ValueError("Empty response from Gemini API")
            
            return self._normalize_content(response.content).strip()
        
        except ValueError as e:
            logger.warning(f"Validation error for user {user_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error generating response for user {user_id}: {str(e)}")
            raise

# Singleton instance
try:
    gemini_service = GeminiService()
    logger.info("GeminiService singleton created")
except Exception as e:
    logger.error(f"Failed to create GeminiService: {str(e)}")
    gemini_service = None

# Backward compatibility alias
groq_service = gemini_service

async def generate_groq_response(messages: List[dict], user_id: str) -> str:
    if not gemini_service:
        raise RuntimeError("GeminiService is not available")
    return await gemini_service.generate_response(messages, user_id)

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
    if not gemini_service:
        raise RuntimeError("GeminiService is not available")
    
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
        
        # Call Gemini API for summary
        # Offload blocking Gemini API call to a thread
        response = await asyncio.to_thread(
            gemini_service.client.invoke,
            GeminiService._to_lc_messages(formatted_messages)
        )
        
        if not response or response.content is None:
            raise ValueError("Empty response from Gemini API")
        
        summary = GeminiService._normalize_content(response.content).strip()
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
    if not gemini_service:
        raise RuntimeError("GeminiService is not available")
    
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
        
        # Call Gemini API
        response = await asyncio.to_thread(
            gemini_service.client.invoke,
            GeminiService._to_lc_messages(formatted_messages)
        )
        
        if not response or response.content is None:
            raise ValueError("Empty response from Gemini API")
        
        return GeminiService._normalize_content(response.content).strip()
        
    except ValueError as e:
        logger.warning(f"Validation error for thread {thread_id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error generating context-aware response: {str(e)}")
        # Fallback to basic response
        logger.info("Falling back to basic response generation")
        return await gemini_service.generate_response(messages, user_id)