from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.api import deps
from app.models.quiz import Questionnaire, ClientesQuizSession
from app.models.cliente import Cliente
from app.schemas.quiz import Questionnaire as QuestionnaireSchema, QuizSession, QuizSessionCreate
from app.db.session import get_db

router = APIRouter()

@router.get("/questionnaires", response_model=List[QuestionnaireSchema])
async def read_questionnaires(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve questionnaires.
    """
    result = await db.execute(select(Questionnaire).where(Questionnaire.active == True).offset(skip).limit(limit))
    return result.scalars().all()

@router.post("/session", response_model=QuizSession)
async def create_quiz_session(
    *,
    db: AsyncSession = Depends(get_db),
    session_in: QuizSessionCreate,
    current_user: Cliente = Depends(deps.get_current_user),
) -> Any:
    """
    Submit quiz responses.
    """
    quiz_session = ClientesQuizSession(
        cliente_id=current_user.id,
        questionnaire_id=session_in.questionnaire_id,
        responses=session_in.responses,
        finished_at=datetime.utcnow()
    )
    db.add(quiz_session)
    await db.commit()
    await db.refresh(quiz_session)
    return quiz_session
