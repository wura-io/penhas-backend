from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime

class NoticiaBase(BaseModel):
    title: str
    description: Optional[str] = None
    hyperlink: Optional[str] = None
    info: Dict[str, Any] = {}
    
class Noticia(NoticiaBase):
    id: int
    created_at: datetime
    display_created_time: datetime
    author: Optional[str] = None
    image_hyperlink: Optional[str] = None

    class Config:
        from_attributes = True

