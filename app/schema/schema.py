
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import List, Optional

class Message(BaseModel):
    role: str    # "user" or "assistant"
    content: str
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in ["user", "assistant"]:
            raise ValueError('role must be "user" or "assistant"')
        return v
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('content cannot be empty')
        return v

class AIRequest(BaseModel):
    messages: List[Message]
    user_id: str
    
    @field_validator('messages')
    @classmethod
    def validate_messages(cls, v):
        if not v:
            raise ValueError('messages list cannot be empty')
        return v
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not v or not v.strip():
            raise ValueError('user_id cannot be empty')
        return v

class AIResponse(BaseModel):
    response: str
    success: bool = True
    error: Optional[str] = None
    thread_id: Optional[str] = None  # Add thread_id to response

class SummaryRequest(BaseModel):
    thread_id: str
    user_id: str
    
    @field_validator('thread_id')
    @classmethod
    def validate_thread_id(cls, v):
        if not v or not v.strip():
            raise ValueError('thread_id cannot be empty')
        return v
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not v or not v.strip():
            raise ValueError('user_id cannot be empty')
        return v

class SummaryResponse(BaseModel):
    summary: str
    thread_id: str
    success: bool = True
    error: Optional[str] = None

class ThreadInfo(BaseModel):
    thread_id: str
    user_id: str
    title: str = ""
    message_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ThreadListResponse(BaseModel):
    threads: List[ThreadInfo]
    total: int
    success: bool = True

class ThreadDeleteResponse(BaseModel):
    thread_id: str
    success: bool = True
    message: str = "Thread deleted successfully"

class ContextAwareChatRequest(BaseModel):
    """Chat request with optional thread_id for context-aware responses"""
    messages: List[Message]
    user_id: str
    thread_id: Optional[str] = None
    
class ThreadMessagesRequest(BaseModel):
    """Combined request for thread messages (fetch mode) or chat (chat mode)"""
    messages: Optional[List[Message]] = None  # If provided: chat mode, else: fetch mode
 