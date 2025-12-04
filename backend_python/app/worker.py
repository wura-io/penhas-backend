"""
Celery background tasks
Port from Perl Penhas::Minion::Tasks::*
"""
from celery import Task
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import asyncio
from typing import Optional, Dict, Any
import feedparser
import httpx

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.cliente import Cliente
from app.models.rss import RssFeed
from app.models.noticia import Noticia
from app.models.audio import ClientesAudio
from app.models.activity import ClientesAppNotification
from app.models.admin import NotificationMessage, NotificationLog
from app.integrations.sms import sms_service
from app.integrations.storage import s3_storage_service
from app.integrations.fcm import fcm_service
from app.integrations.cep import cep_service


class AsyncTask(Task):
    """Base task class that provides async support"""
    
    def __call__(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.run_async(*args, **kwargs))
    
    async def run_async(self, *args, **kwargs):
        raise NotImplementedError


@celery_app.task(name="tasks.cep_updater", bind=True, base=AsyncTask)
async def cep_updater_task(self, cliente_id: int, cep: str):
    """
    Update user address data from CEP
    Port from CepUpdater.pm
    
    Args:
        cliente_id: User ID
        cep: CEP to lookup
    """
    async with SessionLocal() as db:
        # Get user
        result = await db.execute(
            select(Cliente).where(Cliente.id == cliente_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return {"error": "User not found"}
        
        # Lookup CEP
        cep_data = await cep_service.find(cep)
        
        if not cep_data:
            return {"error": "CEP not found"}
        
        # Update user address
        if cep_data.get('city'):
            user.municipio = cep_data['city']
        if cep_data.get('state'):
            user.estado = cep_data['state']
        
        await db.commit()
        
        return {"success": True, "updated_fields": cep_data}


@celery_app.task(name="tasks.delete_audio", bind=True, base=AsyncTask)
async def delete_audio_task(self, audio_id: int):
    """
    Delete audio file from storage
    Port from DeleteAudio.pm
    
    Args:
        audio_id: Audio record ID
    """
    async with SessionLocal() as db:
        # Get audio record
        result = await db.execute(
            select(ClientesAudio).where(ClientesAudio.id == audio_id)
        )
        audio = result.scalar_one_or_none()
        
        if not audio:
            return {"error": "Audio not found"}
        
        # Delete from S3
        if audio.s3_key:
            await s3_storage_service.delete_file(audio.s3_key)
        
        # Delete database record
        await db.delete(audio)
        await db.commit()
        
        return {"success": True, "deleted_audio_id": audio_id}


@celery_app.task(name="tasks.delete_user", bind=True, base=AsyncTask)
async def delete_user_task(self, cliente_id: int):
    """
    Permanent user deletion job
    Port from DeleteUser.pm
    
    Args:
        cliente_id: User ID to delete
    """
    async with SessionLocal() as db:
        # Get user
        result = await db.execute(
            select(Cliente).where(Cliente.id == cliente_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return {"error": "User not found"}
        
        # Mark deletion started
        user.deletion_started_at = datetime.utcnow()
        await db.commit()
        
        # Delete user's audio files
        result = await db.execute(
            select(ClientesAudio).where(ClientesAudio.cliente_id == cliente_id)
        )
        audios = result.scalars().all()
        
        for audio in audios:
            if audio.s3_key:
                await s3_storage_service.delete_file(audio.s3_key)
        
        # Delete user's media uploads
        # TODO: Delete from media_uploads table and S3
        
        # Anonymize or delete user data
        # Instead of hard delete, anonymize
        user.email = f"deleted_{user.id}@deleted.local"
        user.cpf = None
        user.nome_completo = "Usuário Excluído"
        user.apelido = f"user_{user.id}"
        user.avatar = None
        user.deleted_at = datetime.utcnow()
        
        await db.commit()
        
        return {"success": True, "anonymized_user_id": cliente_id}


@celery_app.task(name="tasks.new_notification", bind=True, base=AsyncTask)
async def new_notification_task(self, notification_message_id: int):
    """
    Send push notifications via Firebase
    Port from NewNotification.pm
    
    Args:
        notification_message_id: NotificationMessage ID
    """
    async with SessionLocal() as db:
        # Get notification message
        result = await db.execute(
            select(NotificationMessage).where(NotificationMessage.id == notification_message_id)
        )
        notif_message = result.scalar_one_or_none()
        
        if not notif_message:
            return {"error": "Notification message not found"}
        
        # Get target users (simplified - should use segment logic)
        # TODO: Implement proper segment filtering
        result = await db.execute(
            select(Cliente).where(Cliente.active == True)
        )
        users = result.scalars().all()
        
        sent_count = 0
        failed_count = 0
        
        for user in users:
            # Get user's FCM token (from app_activity or similar)
            # TODO: Implement FCM token retrieval
            fcm_token = None  # user.fcm_token
            
            if not fcm_token:
                continue
            
            # Send push notification
            result = await fcm_service.send_notification(
                device_tokens=[fcm_token],
                title=notif_message.title,
                body=notif_message.content,
                data={
                    "notification_id": str(notif_message.id),
                    "type": notif_message.notification_type or "general"
                }
            )
            
            # Log notification
            log = NotificationLog(
                notification_message_id=notification_message_id,
                cliente_id=user.id,
                status="sent" if result.get("success") else "failed",
                created_at=datetime.utcnow()
            )
            db.add(log)
            
            if result.get("success"):
                sent_count += 1
            else:
                failed_count += 1
        
        await db.commit()
        
        return {
            "success": True,
            "sent_count": sent_count,
            "failed_count": failed_count
        }


@celery_app.task(name="tasks.news_display_indexer", bind=True, base=AsyncTask)
async def news_display_indexer_task(self):
    """
    Update news display index
    Port from NewsDisplayIndexer.pm
    
    Recalculates display order for news articles
    """
    async with SessionLocal() as db:
        # Get all active news
        result = await db.execute(
            select(Noticia)
            .where(Noticia.published_at.isnot(None))
            .order_by(Noticia.published_at.desc())
        )
        news_articles = result.scalars().all()
        
        # Update display index
        for index, article in enumerate(news_articles):
            article.display_index = index
        
        await db.commit()
        
        return {
            "success": True,
            "indexed_count": len(news_articles)
        }


@celery_app.task(name="tasks.news_indexer", bind=True, base=AsyncTask)
async def news_indexer_task(self, noticia_id: int):
    """
    Index news for search
    Port from NewsIndexer.pm
    
    Args:
        noticia_id: News article ID to index
    """
    async with SessionLocal() as db:
        # Get news article
        result = await db.execute(
            select(Noticia).where(Noticia.id == noticia_id)
        )
        article = result.scalar_one_or_none()
        
        if not article:
            return {"error": "Article not found"}
        
        # TODO: Implement full-text search indexing
        # For now, just mark as indexed
        article.indexed_at = datetime.utcnow()
        await db.commit()
        
        return {
            "success": True,
            "indexed_article_id": noticia_id
        }


@celery_app.task(name="tasks.send_sms", bind=True, base=AsyncTask)
async def send_sms_task(
    self,
    phone_number: str,
    message: str,
    sender_id: Optional[str] = "PenhasApp"
):
    """
    Send SMS via AWS SNS
    Port from SendSMS.pm
    
    Args:
        phone_number: E.164 format phone number
        message: SMS text content
        sender_id: Sender ID to display
    """
    async with SessionLocal() as db:
        result = await sms_service.send_sms(
            db=db,
            phone_number=phone_number,
            message=message,
            sender_id=sender_id
        )
        
        return result


@celery_app.task(name="tasks.tick_rss_feeds", bind=True, base=AsyncTask)
async def tick_rss_feeds_task(self):
    """
    Periodic task to fetch RSS feeds
    Port from RSS feed fetching in Perl
    
    Fetches all active RSS feeds and creates news articles
    """
    async with SessionLocal() as db:
        # Get all active RSS feeds
        result = await db.execute(
            select(RssFeed).where(RssFeed.is_active == True)
        )
        feeds = result.scalars().all()
        
        new_articles_count = 0
        
        for feed in feeds:
            try:
                # Fetch RSS feed
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(feed.rss_url)
                    response.raise_for_status()
                    
                    # Parse RSS
                    parsed_feed = feedparser.parse(response.text)
                    
                    # Process entries
                    for entry in parsed_feed.entries[:10]:  # Limit to 10 per feed
                        # Check if article already exists
                        result = await db.execute(
                            select(Noticia).where(Noticia.rss_guid == entry.get('id', entry.link))
                        )
                        existing = result.scalar_one_or_none()
                        
                        if existing:
                            continue
                        
                        # Create new article
                        article = Noticia(
                            rss_feed_id=feed.id,
                            rss_guid=entry.get('id', entry.link),
                            titulo=entry.title,
                            resumo=entry.get('summary', '')[:500],
                            link_externo=entry.link,
                            published_at=datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.utcnow(),
                            created_at=datetime.utcnow()
                        )
                        db.add(article)
                        new_articles_count += 1
                
                # Update feed last fetch
                feed.last_fetched_at = datetime.utcnow()
                
            except Exception as e:
                print(f"Error fetching RSS feed {feed.id}: {e}")
                feed.error_message = str(e)
        
        await db.commit()
        
        return {
            "success": True,
            "feeds_processed": len(feeds),
            "new_articles": new_articles_count
        }


# Periodic task schedules (to be configured in Celery beat)
celery_app.conf.beat_schedule = {
    'tick-rss-feeds-every-hour': {
        'task': 'tasks.tick_rss_feeds',
        'schedule': 3600.0,  # Every hour
    },
    'news-display-indexer-daily': {
        'task': 'tasks.news_display_indexer',
        'schedule': 86400.0,  # Every day
    },
}
