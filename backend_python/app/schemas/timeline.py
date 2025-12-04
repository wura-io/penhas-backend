from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TweetBase(BaseModel):
    content: str
    media_ids: Optional[str] = None
    
class TweetCreate(TweetBase):
    pass

class Tweet(TweetBase):
    id: str
    created_at: datetime
    cliente_id: int
    qtde_likes: int
    qtde_comentarios: int
    liked_by_me: bool = False # Computed field

    class Config:
        from_attributes = True

class TweetLikeRequest(BaseModel):
    remove: Optional[str] = None # "1" to remove

