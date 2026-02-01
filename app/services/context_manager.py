"""
Enhanced Context Manager for AI Chat
Handles conversation memory, summarization, and context optimization
"""
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime
from app.database import db_client
import asyncio
import tiktoken

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages conversation context with memory optimization"""
    
    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
        
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Fallback: rough estimation
            return len(text) // 4
    
    async def get_optimized_context(
        self, 
        thread_id: str, 
        user_id: str,
        current_message: str,
        max_history: int = 20
    ) -> Tuple[List[Dict], Optional[str]]:
        """
        Get optimized conversation context with token management
        
        Returns:
            Tuple of (message_history, thread_summary)
        """
        try:
            # Get thread summary if exists
            thread_info = await asyncio.to_thread(db_client.get_thread_info, thread_id)
            summary = thread_info.get("summary") if thread_info else None
            
            # Get recent messages
            messages = await asyncio.to_thread(
                db_client.get_thread_messages, 
                thread_id, 
                user_id, 
                limit=max_history
            )
            
            # Calculate tokens
            current_tokens = self.count_tokens(current_message)
            summary_tokens = self.count_tokens(summary) if summary else 0
            
            # Build optimized message list
            optimized_messages = []
            total_tokens = current_tokens + summary_tokens
            
            # Add messages from newest to oldest until token limit
            for msg in reversed(messages):
                msg_tokens = self.count_tokens(msg.get("content", ""))
                if total_tokens + msg_tokens > self.max_tokens:
                    break
                optimized_messages.insert(0, msg)
                total_tokens += msg_tokens
            
            logger.info(
                f"Context optimized: {len(optimized_messages)}/{len(messages)} messages, "
                f"{total_tokens}/{self.max_tokens} tokens"
            )
            
            return optimized_messages, summary
            
        except Exception as e:
            logger.error(f"Error getting optimized context: {e}")
            return [], None
    
    async def build_context_prompt(
        self,
        thread_id: str,
        user_id: str,
        current_message: str,
        user_data: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Build complete context with user data and conversation history
        
        Args:
            thread_id: Thread ID
            user_id: User ID
            current_message: Current user message
            user_data: Optional user-specific data (KYC status, wallet, etc.)
        
        Returns:
            List of messages ready for LLM
        """
        try:
            # Get optimized conversation history
            history, summary = await self.get_optimized_context(
                thread_id, user_id, current_message
            )
            
            # Build context messages
            context_messages = []
            
            # Add summary if exists
            if summary:
                context_messages.append({
                    "role": "system",
                    "content": f"Previous conversation summary: {summary}"
                })
            
            # Add user context if provided
            if user_data:
                user_context = self._format_user_context(user_data)
                context_messages.append({
                    "role": "system",
                    "content": user_context
                })
            
            # Add conversation history
            context_messages.extend(history)
            
            # Add current message
            context_messages.append({
                "role": "user",
                "content": current_message
            })
            
            return context_messages
            
        except Exception as e:
            logger.error(f"Error building context prompt: {e}")
            # Fallback to simple context
            return [{"role": "user", "content": current_message}]
    
    def _format_user_context(self, user_data: Dict) -> str:
        """Format user data into context string"""
        context_parts = ["User Context:"]
        
        if "kyc_status" in user_data:
            context_parts.append(f"- KYC Status: {user_data['kyc_status']}")
        
        if "kyc_rejection_reason" in user_data:
            context_parts.append(f"- KYC Rejection Reason: {user_data['kyc_rejection_reason']}")
        
        if "wallet_balance" in user_data:
            context_parts.append(f"- Wallet Balance: ${user_data['wallet_balance']:.2f}")
        
        if "total_posts" in user_data:
            context_parts.append(f"- Total Posts: {user_data['total_posts']}")
        
        if "last_activity" in user_data:
            context_parts.append(f"- Last Activity: {user_data['last_activity']}")
        
        if "pending_orders" in user_data:
            context_parts.append(f"- Pending Orders: {user_data['pending_orders']}")
        
        return "\n".join(context_parts)
    
    async def should_summarize(self, thread_id: str) -> bool:
        """Check if thread should be summarized"""
        try:
            if not db_client or not db_client.is_connected():
                return False
            
            message_count = await asyncio.to_thread(
                db_client.messages_collection.count_documents,
                {"thread_id": thread_id}
            )
            
            thread_info = await asyncio.to_thread(db_client.get_thread_info, thread_id)
            has_summary = thread_info.get("summary") if thread_info else None
            
            # Summarize every 15 messages if no summary exists
            return message_count >= 15 and message_count % 15 == 0 and not has_summary
            
        except Exception as e:
            logger.error(f"Error checking summarization: {e}")
            return False
    
    async def get_recent_context_summary(
        self,
        thread_id: str,
        user_id: str,
        last_n_messages: int = 10
    ) -> str:
        """Get a quick summary of recent context"""
        try:
            messages = await asyncio.to_thread(
                db_client.get_thread_messages,
                thread_id,
                user_id,
                limit=last_n_messages
            )
            
            if not messages:
                return "No previous conversation"
            
            # Create brief summary
            topics = []
            for msg in messages:
                content = msg.get("content", "")
                if msg.get("role") == "user" and content:
                    # Extract key topics (simple approach)
                    topics.append(content[:100])
            
            return f"Recent topics discussed: {', '.join(topics[:3])}"
            
        except Exception as e:
            logger.error(f"Error getting context summary: {e}")
            return ""


# Singleton instance
context_manager = ContextManager()
