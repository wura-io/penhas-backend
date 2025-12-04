from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Body, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api import deps
from app.models.cliente import Cliente
from app.db.session import get_db
from app.helpers import timeline as timeline_helper

router = APIRouter()


class CreateTweetRequest(BaseModel):
    """Create tweet request"""
    content: str
    parent_tweet_id: int | None = None
    media_ids: List[int] | None = None


@router.get("/")
async def get_timeline(
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    limit: int = 20,
    offset: int = 0
) -> Any:
    """
    Get personalized timeline feed
    Matches Perl GET /timeline
    """
    result = await timeline_helper.get_timeline_feed(
        db=db,
        user=current_user,
        limit=limit,
        offset=offset
    )
    return result


@router.post("/")
async def create_tweet(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    tweet_data: CreateTweetRequest
) -> Any:
    """
    Create new tweet
    Matches Perl POST /me/tweets
    """
    result = await timeline_helper.create_tweet(
        db=db,
        user=current_user,
        content=tweet_data.content,
        parent_tweet_id=tweet_data.parent_tweet_id,
        media_ids=tweet_data.media_ids
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    
    return result


@router.delete("/{tweet_id}")
async def delete_tweet(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    tweet_id: int
) -> Any:
    """
    Delete own tweet
    Matches Perl DELETE /me/tweets
    """
    result = await timeline_helper.delete_tweet(
        db=db,
        user=current_user,
        tweet_id=tweet_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result)
    
    return result


@router.post("/{tweet_id}/like")
async def toggle_like(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    tweet_id: int
) -> Any:
    """
    Like or unlike a tweet
    Matches Perl POST /timeline/:id/like
    """
    result = await timeline_helper.toggle_like(
        db=db,
        user=current_user,
        tweet_id=tweet_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result)
    
    return result


@router.post("/{tweet_id}/comment")
async def add_comment(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    tweet_id: int,
    comment_data: CreateTweetRequest
) -> Any:
    """
    Add comment to tweet
    Matches Perl POST /timeline/:id/comment
    """
    result = await timeline_helper.create_tweet(
        db=db,
        user=current_user,
        content=comment_data.content,
        parent_tweet_id=tweet_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    
    return result


@router.get("/{tweet_id}/comments")
async def get_comments(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    tweet_id: int,
    limit: int = 50,
    offset: int = 0
) -> Any:
    """
    Get tweet comments
    Matches Perl GET /timeline/:id/comments
    """
    result = await timeline_helper.get_tweet_comments(
        db=db,
        user=current_user,
        tweet_id=tweet_id,
        limit=limit,
        offset=offset
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result)
    
    return result


@router.post("/{tweet_id}/report")
async def report_tweet(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: Cliente = Depends(deps.get_current_user),
    tweet_id: int,
    reason: str | None = Body(None, embed=True)
) -> Any:
    """
    Report a tweet
    Matches Perl POST /timeline/:id/report
    """
    result = await timeline_helper.report_tweet(
        db=db,
        user=current_user,
        tweet_id=tweet_id,
        reason=reason
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    
    return result
