from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from config import settings
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class MongoDBClient:
    def __init__(self):
        try:
            self.client = MongoClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )
            # Test connection
            self.client.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
            
            self.db = self.client[settings.DATABASE_NAME]
            # Use new collection name for storing chat messages
            self.messages_collection = self.db['AI_Chat_messages']
            self.threads_collection = self.db['AI_threads']
            # Add new collections for enhanced features
            self.user_permissions_collection = self.db['AI_user_permissions']
            self.context_metadata_collection = self.db['AI_context_metadata']
            
            # Create indexes for better performance
            self.messages_collection.create_index([('thread_id', 1)])
            self.messages_collection.create_index([('user_id', 1)])
            self.messages_collection.create_index([('created_at', -1)])
            
            self.threads_collection.create_index([('thread_id', 1)])
            self.threads_collection.create_index([('user_id', 1)])
            
            # Indexes for new collections
            self.user_permissions_collection.create_index([('user_id', 1)], unique=True)
            self.context_metadata_collection.create_index([('thread_id', 1)])
            
            logger.info("Database indexes created successfully")
            
        except ServerSelectionTimeoutError as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self.client = None
            self.db = None
            self.messages_collection = None
            self.threads_collection = None
        except Exception as e:
            logger.error(f"Error initializing MongoDB client: {str(e)}")
            self.client = None
            self.db = None
            self.messages_collection = None
            self.threads_collection = None
    
    def is_connected(self) -> bool:
        """Check if MongoDB is connected"""
        return self.client is not None and self.messages_collection is not None
    
    def save_message(self, thread_id: str, user_id: str, role: str, content: str) -> bool:
        """Save a message to the database"""
        if not self.is_connected():
            logger.error("Messages collection is not available")
            return False
        
        try:
            message = {
                "thread_id": thread_id,
                "user_id": user_id,
                "role": role,
                "content": content,
                "created_at": datetime.utcnow()
            }
            result = self.messages_collection.insert_one(message)
            logger.info(f"Message saved with ID: {result.inserted_id} to thread {thread_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            return False
    
    def get_thread_messages(self, thread_id: str, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Get all messages from a thread (last 'limit' messages in chronological order).
        
        Args:
            thread_id: ID of the thread
            user_id: ID of the user
            limit: Number of messages to fetch (default: 10, max 100)
            
        Returns:
            List of messages with 'role' and 'content' fields
        """
        if not self.is_connected():
            logger.error("Messages collection is not available")
            return []
        
        try:
            # Limit max to 100 for safety
            limit = min(limit, 100)
            
            messages = list(
                self.messages_collection.find(
                    {
                        "thread_id": thread_id,
                        "user_id": user_id
                    }
                )
                .sort("created_at", -1)  # Most recent first
                .limit(limit)
            )
            
            # Reverse to get chronological order (oldest first)
            messages.reverse()
            
            # Format messages - remove MongoDB's _id field
            formatted_messages = [
                {
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                }
                for msg in messages
            ]
            
            logger.info(f"Retrieved {len(formatted_messages)} messages from thread {thread_id} for user {user_id}")
            return formatted_messages
            
        except Exception as e:
            logger.error(f"Error retrieving thread messages: {str(e)}")
            return []
    
    def create_thread(self, thread_id: str, user_id: str, title: str = "") -> bool:
        """Create a new thread"""
        if not self.is_connected():
            logger.error("Threads collection is not available")
            return False
        
        try:
            thread = {
                "thread_id": thread_id,
                "user_id": user_id,
                "title": title,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "message_count": 0
            }
            self.threads_collection.insert_one(thread)
            logger.info(f"Thread {thread_id} created for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating thread: {str(e)}")
            return False
    
    def update_thread_message_count(self, thread_id: str) -> bool:
        """Update the message count for a thread"""
        if not self.is_connected():
            logger.error("Collections are not available")
            return False
        
        try:
            count = self.messages_collection.count_documents({"thread_id": thread_id})
            self.threads_collection.update_one(
                {"thread_id": thread_id},
                {
                    "$set": {
                        "updated_at": datetime.utcnow(),
                        "message_count": count
                    }
                }
            )
            logger.info(f"Updated message count for thread {thread_id}: {count}")
            return True
        except Exception as e:
            logger.error(f"Error updating thread message count: {str(e)}")
            return False
    
    def get_thread_info(self, thread_id: str) -> Optional[Dict]:
        """Get thread information"""
        if not self.is_connected():
            logger.error("Threads collection is not available")
            return None
        
        try:
            thread = self.threads_collection.find_one({"thread_id": thread_id})
            if thread:
                thread.pop("_id", None)  # Remove MongoDB _id
            return thread
        except Exception as e:
            logger.error(f"Error retrieving thread info: {str(e)}")
            return None
    
    def save_thread_summary(self, thread_id: str, summary: str) -> bool:
        """Save or update thread summary in database"""
        if not self.is_connected():
            logger.error("Threads collection is not available")
            return False
        
        try:
            self.threads_collection.update_one(
                {"thread_id": thread_id},
                {
                    "$set": {
                        "summary": summary,
                        "summary_updated_at": datetime.utcnow()
                    }
                }
            )
            logger.info(f"Summary saved for thread {thread_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving thread summary: {str(e)}")
            return False
    
    def get_thread_summary(self, thread_id: str) -> Optional[str]:
        """Get thread summary from database"""
        if not self.is_connected():
            logger.error("Threads collection is not available")
            return None
        
        try:
            thread = self.threads_collection.find_one({"thread_id": thread_id})
            if thread:
                summary = thread.get("summary")
                if summary:
                    logger.info(f"Retrieved summary for thread {thread_id}")
                    return summary
            return None
        except Exception as e:
            logger.error(f"Error retrieving thread summary: {str(e)}")
            return None
    
    def save_context_metadata(self, thread_id: str, user_id: str, metadata: Dict) -> bool:
        """Save context metadata for enhanced tracking"""
        if not self.is_connected():
            logger.error("Context metadata collection is not available")
            return False
        
        try:
            result = self.context_metadata_collection.update_one(
                {"thread_id": thread_id, "user_id": user_id},
                {
                    "$set": {
                        **metadata,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            logger.info(f"Context metadata saved for thread {thread_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving context metadata: {str(e)}")
            return False
    
    def get_context_metadata(self, thread_id: str, user_id: str) -> Optional[Dict]:
        """Get context metadata for a thread"""
        if not self.is_connected():
            return None
        
        try:
            metadata = self.context_metadata_collection.find_one({
                "thread_id": thread_id,
                "user_id": user_id
            })
            return metadata
        except Exception as e:
            logger.error(f"Error retrieving context metadata: {str(e)}")
            return None
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Initialize MongoDB client singleton
try:
    db_client = MongoDBClient()
    if db_client.is_connected():
        logger.info("Database client initialized successfully")
    else:
        logger.warning("Database client initialized but not connected")
except Exception as e:
    logger.error(f"Failed to initialize database client: {str(e)}")
    db_client = None
