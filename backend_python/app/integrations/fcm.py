"""
Firebase Cloud Messaging (FCM) push notification service
Port from Perl FCM integration
Sends push notifications to mobile devices
"""
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.config import settings


class FCMService:
    """
    Firebase Cloud Messaging service for push notifications
    Matches Perl's FCM/Firebase integration
    """
    
    def __init__(self):
        self.server_key = settings.FIREBASE_SERVER_KEY
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"
        self.timeout = 30
    
    async def send_notification(
        self,
        device_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        badge: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send push notification to one or more devices
        
        Args:
            device_tokens: List of FCM device tokens
            title: Notification title
            body: Notification body text
            data: Additional data payload (optional)
            badge: Badge count for iOS (optional)
            
        Returns:
            Dict with send result:
            - success: bool
            - success_count: int
            - failure_count: int
            - results: List of individual results
        """
        if not self.server_key:
            return {
                "success": False,
                "error": "FCM not configured (missing server key)"
            }
        
        if not device_tokens:
            return {
                "success": False,
                "error": "No device tokens provided"
            }
        
        # Build notification payload
        notification_payload = {
            "title": title,
            "body": body,
            "sound": "default"
        }
        
        if badge is not None:
            notification_payload["badge"] = str(badge)
        
        # Build complete payload
        payload = {
            "registration_ids": device_tokens,
            "notification": notification_payload,
            "priority": "high"
        }
        
        # Add custom data if provided
        if data:
            payload["data"] = data
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.fcm_url,
                    json=payload,
                    headers={
                        "Authorization": f"key={self.server_key}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                success_count = result.get("success", 0)
                failure_count = result.get("failure", 0)
                results = result.get("results", [])
                
                return {
                    "success": success_count > 0,
                    "success_count": success_count,
                    "failure_count": failure_count,
                    "results": results
                }
                
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code}"
            }
        except httpx.RequestError as e:
            return {
                "success": False,
                "error": f"Request error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def send_notification_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send push notification to a topic (all subscribed devices)
        
        Args:
            topic: FCM topic name
            title: Notification title
            body: Notification body text
            data: Additional data payload (optional)
            
        Returns:
            Dict with send result
        """
        if not self.server_key:
            return {
                "success": False,
                "error": "FCM not configured"
            }
        
        # Build notification payload
        notification_payload = {
            "title": title,
            "body": body,
            "sound": "default"
        }
        
        # Build complete payload
        payload = {
            "to": f"/topics/{topic}",
            "notification": notification_payload,
            "priority": "high"
        }
        
        if data:
            payload["data"] = data
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.fcm_url,
                    json=payload,
                    headers={
                        "Authorization": f"key={self.server_key}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                return {
                    "success": True,
                    "message_id": result.get("message_id")
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_data_message(
        self,
        device_tokens: List[str],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send data-only message (no notification UI)
        Used for silent updates
        
        Args:
            device_tokens: List of FCM device tokens
            data: Data payload
            
        Returns:
            Dict with send result
        """
        if not self.server_key:
            return {
                "success": False,
                "error": "FCM not configured"
            }
        
        payload = {
            "registration_ids": device_tokens,
            "data": data,
            "priority": "high",
            "content_available": True  # For iOS background processing
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.fcm_url,
                    json=payload,
                    headers={
                        "Authorization": f"key={self.server_key}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                return {
                    "success": result.get("success", 0) > 0,
                    "success_count": result.get("success", 0),
                    "failure_count": result.get("failure", 0)
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
fcm_service = FCMService()

