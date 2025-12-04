"""
AWS S3 file storage service
Port from Perl S3 integration
Handles file upload, download, and signed URL generation
"""
import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime, timedelta
import mimetypes
import os

from app.core.config import settings


class S3StorageService:
    """
    S3 file storage service
    Matches Perl's S3 integration
    """
    
    def __init__(self):
        self.bucket = settings.AWS_S3_BUCKET
        self.region = settings.AWS_S3_REGION
        self.access_key = settings.AWS_ACCESS_KEY_ID
        self.secret_key = settings.AWS_SECRET_ACCESS_KEY
        
        if self.access_key and self.secret_key and self.bucket:
            self.s3_client = boto3.client(
                's3',
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            )
        else:
            self.s3_client = None
    
    async def upload_file(
        self,
        file_content: bytes,
        key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload file to S3
        
        Args:
            file_content: File content as bytes
            key: S3 object key (path)
            content_type: MIME type (auto-detected if None)
            metadata: Optional metadata dict
            
        Returns:
            Dict with upload result:
            - success: bool
            - key: str (S3 object key)
            - url: str (public URL if applicable)
            - error: str (if failed)
        """
        if not self.s3_client:
            return {
                "success": False,
                "error": "S3 storage not configured"
            }
        
        # Auto-detect content type if not provided
        if not content_type:
            content_type, _ = mimetypes.guess_type(key)
            if not content_type:
                content_type = 'application/octet-stream'
        
        try:
            extra_args = {
                'ContentType': content_type
            }
            
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=file_content,
                **extra_args
            )
            
            # Generate public URL (if bucket is public)
            url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"
            
            return {
                "success": True,
                "key": key,
                "url": url
            }
            
        except ClientError as e:
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def download_file(
        self,
        key: str
    ) -> Dict[str, Any]:
        """
        Download file from S3
        
        Args:
            key: S3 object key (path)
            
        Returns:
            Dict with download result:
            - success: bool
            - content: bytes (file content)
            - content_type: str
            - error: str (if failed)
        """
        if not self.s3_client:
            return {
                "success": False,
                "error": "S3 storage not configured"
            }
        
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=key
            )
            
            content = response['Body'].read()
            content_type = response.get('ContentType', 'application/octet-stream')
            
            return {
                "success": True,
                "content": content,
                "content_type": content_type
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                return {
                    "success": False,
                    "error": "File not found"
                }
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
        http_method: str = 'GET'
    ) -> Optional[str]:
        """
        Generate presigned URL for temporary access
        
        Args:
            key: S3 object key
            expiration: URL validity in seconds (default 1 hour)
            http_method: HTTP method (GET for download, PUT for upload)
            
        Returns:
            Presigned URL string or None if error
        """
        if not self.s3_client:
            return None
        
        try:
            if http_method == 'GET':
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.bucket,
                        'Key': key
                    },
                    ExpiresIn=expiration
                )
            elif http_method == 'PUT':
                url = self.s3_client.generate_presigned_url(
                    'put_object',
                    Params={
                        'Bucket': self.bucket,
                        'Key': key
                    },
                    ExpiresIn=expiration
                )
            else:
                return None
            
            return url
            
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None
    
    async def delete_file(
        self,
        key: str
    ) -> Dict[str, Any]:
        """
        Delete file from S3
        
        Args:
            key: S3 object key
            
        Returns:
            Dict with delete result:
            - success: bool
            - error: str (if failed)
        """
        if not self.s3_client:
            return {
                "success": False,
                "error": "S3 storage not configured"
            }
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=key
            )
            
            return {"success": True}
            
        except ClientError as e:
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def build_audio_key(self, cliente_id: int, filename: str) -> str:
        """
        Build S3 key for audio file
        Matches Perl's audio storage path structure
        """
        return f"audios/{cliente_id}/{filename}"
    
    def build_media_key(self, cliente_id: int, filename: str, media_type: str = 'images') -> str:
        """
        Build S3 key for media file (images, etc.)
        Matches Perl's media storage path structure
        """
        return f"{media_type}/{cliente_id}/{filename}"


# Singleton instance
s3_storage_service = S3StorageService()

