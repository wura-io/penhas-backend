"""
Anonymous quiz endpoints
Port from Perl AnonQuestionnaire controller
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.helpers import anon_quiz as anon_quiz_helper
from app.models.quiz import AnonymousQuizSession

router = APIRouter()


class AnswerRequest(BaseModel):
    """Quiz answer request"""
    question_id: int
    answer: str | int | List[str]


class ProcessAnswersRequest(BaseModel):
    """Process quiz answers request"""
    answers: List[AnswerRequest]


async def verify_anon_token_dependency(
    anon_token: str = Header(...),
    db: AsyncSession = Depends(get_db)
) -> AnonymousQuizSession:
    """Verify anonymous quiz token from header"""
    session = await anon_quiz_helper.verify_anon_token(db=db, token=anon_token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return session


@router.post("/new")
async def create_anon_session(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create new anonymous quiz session
    Matches Perl POST /anon-questionnaires/new
    """
    result = await anon_quiz_helper.create_anon_session(db=db)
    return result


@router.get("/config")
async def get_quiz_config(
    db: AsyncSession = Depends(get_db),
    session: AnonymousQuizSession = Depends(verify_anon_token_dependency)
) -> Any:
    """
    Get quiz configuration
    Matches Perl GET /anon-questionnaires/config
    """
    result = await anon_quiz_helper.get_anon_quiz_config(db=db, session=session)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result)
    
    return result


@router.get("/")
async def list_questions(
    db: AsyncSession = Depends(get_db),
    session: AnonymousQuizSession = Depends(verify_anon_token_dependency)
) -> Any:
    """
    List quiz questions
    Matches Perl GET /anon-questionnaires
    """
    result = await anon_quiz_helper.list_anon_quiz_questions(db=db, session=session)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result)
    
    return result


@router.get("/history")
async def get_history(
    db: AsyncSession = Depends(get_db),
    session: AnonymousQuizSession = Depends(verify_anon_token_dependency)
) -> Any:
    """
    Get quiz history for session
    Matches Perl GET /anon-questionnaires/history
    """
    return {
        "session_id": session.id,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "completed": bool(session.completed_at)
    }


@router.post("/process")
async def process_answers(
    *,
    db: AsyncSession = Depends(get_db),
    session: AnonymousQuizSession = Depends(verify_anon_token_dependency),
    answer_data: ProcessAnswersRequest
) -> Any:
    """
    Process quiz answers
    Matches Perl POST /anon-questionnaires/process
    """
    result = await anon_quiz_helper.process_anon_quiz_answers(
        db=db,
        session=session,
        answers=[a.dict() for a in answer_data.answers]
    )
    
    return result

