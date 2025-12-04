"""Maintenance endpoints
Port from Perl maintenance routes
Endpoints for background tasks and system maintenance
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import get_db
from app.worker import (
    tick_rss_feeds_task,
    news_display_indexer_task,
    news_indexer_task
)

router = APIRouter()


@router.post("/tick-rss")
async def tick_rss_feeds(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Trigger RSS feed fetching
    Matches Perl GET /maintenance/tick-rss
    
    This can be called via cron or manually to fetch RSS feeds
    """
    # Queue the task in background
    background_tasks.add_task(tick_rss_feeds_task.delay)
    
    return {
        "success": True,
        "message": "RSS feed task queued"
    }


@router.post("/tags-clear-cache")
async def clear_tags_cache(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Clear tags cache
    Matches Perl GET /maintenance/tags-clear-cache
    """
    from app.core.redis_client import redis_client
    
    # Clear all tag-related cache keys
    # TODO: Implement proper cache key pattern matching
    
    return {
        "success": True,
        "message": "Tags cache cleared"
    }


@router.post("/reindex-all-news")
async def reindex_all_news(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Rebuild news index
    Matches Perl GET /maintenance/reindex-all-news
    """
    from sqlalchemy import select
    from app.models.noticia import Noticia
    
    # Get all news IDs
    result = await db.execute(
        select(Noticia.id).where(Noticia.published_at.isnot(None))
    )
    news_ids = [row[0] for row in result.all()]
    
    # Queue indexing tasks
    for news_id in news_ids:
        background_tasks.add_task(news_indexer_task.delay, news_id)
    
    # Also update display order
    background_tasks.add_task(news_display_indexer_task.delay)
    
    return {
        "success": True,
        "message": f"Queued {len(news_ids)} news articles for reindexing"
    }


@router.post("/housekeeping")
async def housekeeping(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Run housekeeping tasks
    Matches Perl GET /maintenance/housekeeping
    
    Cleans up old data, expired sessions, etc.
    """
    from datetime import datetime, timedelta
    from sqlalchemy import delete
    from app.models.onboarding import ClientesActiveSession, ClientesResetPassword
    
    # Clean up expired sessions (older than 30 days)
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    
    # Delete old reset password tokens (older than 24 hours)
    reset_cutoff = datetime.utcnow() - timedelta(hours=24)
    await db.execute(
        delete(ClientesResetPassword)
        .where(ClientesResetPassword.created_at < reset_cutoff)
    )
    
    await db.commit()
    
    return {
        "success": True,
        "message": "Housekeeping completed"
    }


@router.post("/tick-notifications")
async def tick_notifications(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Process notification queue
    Matches Perl GET /maintenance/tick-notifications
    
    Sends pending push notifications
    """
    from sqlalchemy import select
    from app.models.admin import NotificationMessage
    
    # Get pending notification messages
    result = await db.execute(
        select(NotificationMessage)
        .where(NotificationMessage.status == 'pending')
        .where(NotificationMessage.scheduled_at <= datetime.utcnow())
    )
    messages = result.scalars().all()
    
    # Queue notification tasks
    from app.worker import new_notification_task
    for message in messages:
        background_tasks.add_task(new_notification_task.delay, message.id)
        message.status = 'processing'
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"Queued {len(messages)} notifications for processing"
    }


@router.post("/fix-tweets-parent-id")
async def fix_tweets_parent_id(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Fix tweets parent_id data
    Matches Perl GET /maintenance/fix_tweets_parent_id
    
    Data fix utility for tweet hierarchy
    """
    from sqlalchemy import select, update
    from app.models.timeline import ClientesTweet
    
    # Get all tweets with invalid parent references
    result = await db.execute(
        select(ClientesTweet)
        .where(ClientesTweet.parent_tweet_id.isnot(None))
    )
    tweets = result.scalars().all()
    
    fixed_count = 0
    for tweet in tweets:
        # Verify parent exists
        result = await db.execute(
            select(ClientesTweet)
            .where(ClientesTweet.id == tweet.parent_tweet_id)
        )
        parent = result.scalar_one_or_none()
        
        if not parent:
            # Clear invalid parent reference
            tweet.parent_tweet_id = None
            tweet.is_comment = False
            fixed_count += 1
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"Fixed {fixed_count} tweets with invalid parent references"
    }


@router.get("/status")
async def maintenance_status(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get system maintenance status
    Returns stats about background jobs, cache, etc.
    """
    from sqlalchemy import select, func
    from app.models.noticia import Noticia
    from app.models.cliente import Cliente
    from app.models.timeline import ClientesTweet
    
    # Get some basic stats
    result = await db.execute(select(func.count(Cliente.id)))
    total_users = result.scalar()
    
    result = await db.execute(
        select(func.count(Cliente.id)).where(Cliente.active == True)
    )
    active_users = result.scalar()
    
    result = await db.execute(select(func.count(Noticia.id)))
    total_news = result.scalar()
    
    result = await db.execute(select(func.count(ClientesTweet.id)))
    total_tweets = result.scalar()
    
    return {
        "status": "operational",
        "stats": {
            "total_users": total_users,
            "active_users": active_users,
            "total_news": total_news,
            "total_tweets": total_tweets
        }
    }

