from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ChatMessageBase(BaseModel):
    message: str

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessage(ChatMessageBase):
    id: int
    created_at: Optional[datetime] = None
    last_msg_is_support: bool = False # From parent chat

    class Config:
        from_attributes = True

class ChatSupport(BaseModel):
    id: int
    last_msg_preview: Optional[str] = None
    last_msg_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

