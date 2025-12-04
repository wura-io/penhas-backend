from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class QuestionnaireBase(BaseModel):
    name: str
    active: bool

class Questionnaire(QuestionnaireBase):
    id: int
    created_on: Optional[datetime] = None

    class Config:
        from_attributes = True

class QuizSessionBase(BaseModel):
    questionnaire_id: int
    responses: Dict[str, Any] = {}

class QuizSessionCreate(QuizSessionBase):
    pass

class QuizSession(QuizSessionBase):
    id: int
    cliente_id: int
    created_at: datetime
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True

