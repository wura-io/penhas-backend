"""
Anonymous Questionnaire helper module
Port from Perl Penhas::Helpers::AnonQuiz
Business logic for anonymous quiz sessions
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
import secrets

from app.models.quiz import AnonymousQuizSession, Questionnaire


async def verify_anon_token(
    db: AsyncSession,
    token: str
) -> Optional[AnonymousQuizSession]:
    """
    Verify anonymous quiz token
    Matches Perl's verify_anon_token
    """
    result = await db.execute(
        select(AnonymousQuizSession).where(AnonymousQuizSession.token == token)
    )
    return result.scalar_one_or_none()


async def create_anon_session(
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Create new anonymous quiz session
    Matches Perl's anonymous quiz session creation
    """
    token = secrets.token_urlsafe(32)
    
    session = AnonymousQuizSession(
        token=token,
        created_at=datetime.utcnow()
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return {
        "success": True,
        "token": token,
        "session_id": session.id
    }


async def get_anon_quiz_config(
    db: AsyncSession,
    session: AnonymousQuizSession
) -> Dict[str, Any]:
    """
    Get quiz configuration for anonymous user
    Matches Perl's aq_config_get
    """
    # Get quiz questionnaire
    result = await db.execute(
        select(Questionnaire)
        .where(Questionnaire.is_active == True)
        .where(Questionnaire.is_anonymous == True)
        .order_by(Questionnaire.created_at.desc())
    )
    questionnaire = result.scalar_one_or_none()
    
    if not questionnaire:
        return {"error": "No active anonymous questionnaire"}
    
    return {
        "questionnaire_id": questionnaire.id,
        "name": questionnaire.name,
        "description": questionnaire.description
    }


async def list_anon_quiz_questions(
    db: AsyncSession,
    session: AnonymousQuizSession
) -> Dict[str, Any]:
    """
    List quiz questions for anonymous user
    Matches Perl's aq_list_get
    """
    # Get active questionnaire
    result = await db.execute(
        select(Questionnaire)
        .where(Questionnaire.is_active == True)
        .where(Questionnaire.is_anonymous == True)
        .order_by(Questionnaire.created_at.desc())
    )
    questionnaire = result.scalar_one_or_none()
    
    if not questionnaire:
        return {"error": "No active questionnaire"}
    
    # TODO: Get questions from QuestionnaireQuestion model
    # For now, return empty list
    return {
        "questionnaire_id": questionnaire.id,
        "questions": []
    }


async def process_anon_quiz_answers(
    db: AsyncSession,
    session: AnonymousQuizSession,
    answers: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Process anonymous quiz answers
    Matches Perl's aq_process_post
    """
    # Update session with answers
    session.completed_at = datetime.utcnow()
    
    # TODO: Store answers and calculate violence detection
    # For now, just mark as completed
    
    await db.commit()
    
    return {
        "success": True,
        "session_id": session.id,
        "completed": True,
        "violence_detected": False  # TODO: Implement detection logic
    }

