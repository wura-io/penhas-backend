"""
Timeline helper module
Port from Perl Penhas::Helpers::Timeline
Business logic for tweets, comments, likes, and feed generation
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from datetime import datetime

from app.models.cliente import Cliente
from app.models.timeline import ClientesTweet, ClientesTweetLike, ClientesTweetReport
from app.models.blocking import ClienteBloqueio


async def create_tweet(
    db: AsyncSession,
    user: Cliente,
    content: str,
    parent_tweet_id: Optional[int] = None,
    media_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Create new tweet or comment
    Matches Perl's tweet creation logic
    """
    # Validate content
    if not content or len(content.strip()) == 0:
        return {"error": "Content is required"}
    
    if len(content) > 2000:
        return {"error": "Content too long (max 2000 characters)"}
    
    # If this is a comment, verify parent tweet exists
    if parent_tweet_id:
        result = await db.execute(
            select(ClientesTweet).where(ClientesTweet.id == parent_tweet_id)
        )
        parent_tweet = result.scalar_one_or_none()
        
        if not parent_tweet:
            return {"error": "Parent tweet not found"}
        
        # Cannot comment on deleted tweets
        if parent_tweet.deleted_at:
            return {"error": "Cannot comment on deleted tweet"}
    
    # Create tweet
    tweet = ClientesTweet(
        cliente_id=user.id,
        content=content,
        parent_tweet_id=parent_tweet_id,
        is_comment=bool(parent_tweet_id),
        created_at=datetime.utcnow()
    )
    db.add(tweet)
    await db.commit()
    await db.refresh(tweet)
    
    # TODO: Link media if media_ids provided
    
    # Update parent tweet comment count
    if parent_tweet_id:
        await db.execute(
            update(ClientesTweet)
            .where(ClientesTweet.id == parent_tweet_id)
            .values(comment_count=ClientesTweet.comment_count + 1)
        )
        await db.commit()
    
    return {
        "success": True,
        "tweet_id": tweet.id,
        "created_at": tweet.created_at.isoformat()
    }


async def delete_tweet(
    db: AsyncSession,
    user: Cliente,
    tweet_id: int
) -> Dict[str, Any]:
    """
    Delete own tweet (soft delete)
    Matches Perl's tweet deletion logic
    """
    result = await db.execute(
        select(ClientesTweet)
        .where(ClientesTweet.id == tweet_id)
        .where(ClientesTweet.cliente_id == user.id)
    )
    tweet = result.scalar_one_or_none()
    
    if not tweet:
        return {"error": "Tweet not found"}
    
    if tweet.deleted_at:
        return {"error": "Tweet already deleted"}
    
    # Soft delete
    tweet.deleted_at = datetime.utcnow()
    await db.commit()
    
    # Update parent comment count if this was a comment
    if tweet.parent_tweet_id:
        await db.execute(
            update(ClientesTweet)
            .where(ClientesTweet.id == tweet.parent_tweet_id)
            .values(comment_count=func.greatest(ClientesTweet.comment_count - 1, 0))
        )
        await db.commit()
    
    return {"success": True}


async def toggle_like(
    db: AsyncSession,
    user: Cliente,
    tweet_id: int
) -> Dict[str, Any]:
    """
    Like or unlike a tweet
    Matches Perl's like toggle logic
    """
    # Check if tweet exists
    result = await db.execute(
        select(ClientesTweet).where(ClientesTweet.id == tweet_id)
    )
    tweet = result.scalar_one_or_none()
    
    if not tweet or tweet.deleted_at:
        return {"error": "Tweet not found"}
    
    # Check if already liked
    result = await db.execute(
        select(ClientesTweetLike)
        .where(ClientesTweetLike.tweet_id == tweet_id)
        .where(ClientesTweetLike.cliente_id == user.id)
    )
    existing_like = result.scalar_one_or_none()
    
    if existing_like:
        # Unlike
        await db.delete(existing_like)
        
        # Decrement like count
        tweet.like_count = max(0, (tweet.like_count or 0) - 1)
        
        await db.commit()
        
        return {
            "success": True,
            "liked": False,
            "like_count": tweet.like_count
        }
    else:
        # Like
        like = ClientesTweetLike(
            tweet_id=tweet_id,
            cliente_id=user.id,
            created_at=datetime.utcnow()
        )
        db.add(like)
        
        # Increment like count
        tweet.like_count = (tweet.like_count or 0) + 1
        
        await db.commit()
        
        return {
            "success": True,
            "liked": True,
            "like_count": tweet.like_count
        }


async def report_tweet(
    db: AsyncSession,
    user: Cliente,
    tweet_id: int,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Report a tweet
    Matches Perl's tweet report logic
    """
    # Check if tweet exists
    result = await db.execute(
        select(ClientesTweet).where(ClientesTweet.id == tweet_id)
    )
    tweet = result.scalar_one_or_none()
    
    if not tweet or tweet.deleted_at:
        return {"error": "Tweet not found"}
    
    # Check if already reported
    result = await db.execute(
        select(ClientesTweetReport)
        .where(ClientesTweetReport.tweet_id == tweet_id)
        .where(ClientesTweetReport.reporter_cliente_id == user.id)
    )
    existing_report = result.scalar_one_or_none()
    
    if existing_report:
        return {"error": "You already reported this tweet"}
    
    # Create report
    report = ClientesTweetReport(
        tweet_id=tweet_id,
        reporter_cliente_id=user.id,
        reason=reason,
        created_at=datetime.utcnow()
    )
    db.add(report)
    await db.commit()
    
    return {"success": True}


async def get_timeline_feed(
    db: AsyncSession,
    user: Cliente,
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Get personalized timeline feed
    Matches Perl's timeline feed generation
    """
    # Get list of blocked user IDs
    result = await db.execute(
        select(ClienteBloqueio.blocked_cliente_id)
        .where(ClienteBloqueio.cliente_id == user.id)
    )
    blocked_ids = [row[0] for row in result.all()]
    
    # Get tweets (exclude blocked users and deleted tweets)
    query = (
        select(ClientesTweet)
        .where(ClientesTweet.deleted_at.is_(None))
        .where(ClientesTweet.is_comment == False)  # Only top-level tweets
    )
    
    if blocked_ids:
        query = query.where(~ClientesTweet.cliente_id.in_(blocked_ids))
    
    query = query.order_by(ClientesTweet.created_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    tweets = result.scalars().all()
    
    # Build response
    rows = []
    for tweet in tweets:
        # Get author info
        result = await db.execute(
            select(Cliente).where(Cliente.id == tweet.cliente_id)
        )
        author = result.scalar_one_or_none()
        
        if not author:
            continue
        
        # Check if current user liked this tweet
        result = await db.execute(
            select(ClientesTweetLike)
            .where(ClientesTweetLike.tweet_id == tweet.id)
            .where(ClientesTweetLike.cliente_id == user.id)
        )
        user_liked = result.scalar_one_or_none() is not None
        
        rows.append({
            "id": tweet.id,
            "content": tweet.content,
            "author": {
                "id": author.id,
                "apelido": author.apelido,
                "avatar_url": author.avatar_url_or_default()
            },
            "like_count": tweet.like_count or 0,
            "comment_count": tweet.comment_count or 0,
            "user_liked": user_liked,
            "created_at": tweet.created_at.isoformat() if tweet.created_at else None
        })
    
    return {"rows": rows}


async def get_tweet_comments(
    db: AsyncSession,
    user: Cliente,
    tweet_id: int,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Get comments for a tweet
    Matches Perl's comment listing logic
    """
    # Verify tweet exists
    result = await db.execute(
        select(ClientesTweet).where(ClientesTweet.id == tweet_id)
    )
    tweet = result.scalar_one_or_none()
    
    if not tweet or tweet.deleted_at:
        return {"error": "Tweet not found"}
    
    # Get blocked user IDs
    result = await db.execute(
        select(ClienteBloqueio.blocked_cliente_id)
        .where(ClienteBloqueio.cliente_id == user.id)
    )
    blocked_ids = [row[0] for row in result.all()]
    
    # Get comments
    query = (
        select(ClientesTweet)
        .where(ClientesTweet.parent_tweet_id == tweet_id)
        .where(ClientesTweet.deleted_at.is_(None))
    )
    
    if blocked_ids:
        query = query.where(~ClientesTweet.cliente_id.in_(blocked_ids))
    
    query = query.order_by(ClientesTweet.created_at.asc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    comments = result.scalars().all()
    
    # Build response
    rows = []
    for comment in comments:
        # Get author info
        result = await db.execute(
            select(Cliente).where(Cliente.id == comment.cliente_id)
        )
        author = result.scalar_one_or_none()
        
        if not author:
            continue
        
        rows.append({
            "id": comment.id,
            "content": comment.content,
            "author": {
                "id": author.id,
                "apelido": author.apelido,
                "avatar_url": author.avatar_url_or_default()
            },
            "like_count": comment.like_count or 0,
            "created_at": comment.created_at.isoformat() if comment.created_at else None
        })
    
    return {"rows": rows}

