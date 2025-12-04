"""
AWS SNS SMS sending service
Port from Perl Penhas::Minion::Tasks::SendSMS
Integrates with AWS SNS for SMS delivery
"""
import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.config import settings
from app.models.sms import SentSmsLog


class SMSService:
    """
    SMS sending service using AWS SNS
    Matches Perl's SendSMS Minion task
    """
    
    def __init__(self):
        self.region = settings.AWS_SNS_REGION
        self.access_key = settings.AWS_SNS_KEY or settings.AWS_ACCESS_KEY_ID
        self.secret_key = settings.AWS_SNS_SECRET or settings.AWS_SECRET_ACCESS_KEY
        
        if self.access_key and self.secret_key:
            self.sns_client = boto3.client(
                'sns',
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            )
        else:
            self.sns_client = None
    
    async def send_sms(
        self,
        db: AsyncSession,
        phone_number: str,
        message: str,
        sender_id: Optional[str] = "PenhasApp"
    ) -> Dict[str, Any]:
        """
        Send SMS via AWS SNS
        
        Args:
            db: Database session
            phone_number: E.164 format phone number (e.g., +5511999998888)
            message: SMS text content
            sender_id: Sender ID to display (up to 11 chars)
            
        Returns:
            Dict with send result:
            - success: bool
            - message_id: str (if successful)
            - error: str (if failed)
        """
        if not self.sns_client:
            return {
                "success": False,
                "error": "SMS service not configured (missing AWS credentials)"
            }
        
        # Ensure phone is in E.164 format
        if not phone_number.startswith('+'):
            phone_number = f"+{phone_number}"
        
        try:
            response = self.sns_client.publish(
                PhoneNumber=phone_number,
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String',
                        'StringValue': sender_id[:11]  # Max 11 chars for sender ID
                    },
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'  # For OTP and important messages
                    }
                }
            )
            
            message_id = response.get('MessageId')
            
            # Log successful send
            await self._log_sms(
                db=db,
                phone_number=phone_number,
                message=message,
                status='sent',
                message_id=message_id
            )
            
            return {
                "success": True,
                "message_id": message_id
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            # Log failed send
            await self._log_sms(
                db=db,
                phone_number=phone_number,
                message=message,
                status='failed',
                error_message=f"{error_code}: {error_message}"
            )
            
            return {
                "success": False,
                "error": error_message
            }
            
        except Exception as e:
            # Log failed send
            await self._log_sms(
                db=db,
                phone_number=phone_number,
                message=message,
                status='error',
                error_message=str(e)
            )
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _log_sms(
        self,
        db: AsyncSession,
        phone_number: str,
        message: str,
        status: str,
        message_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log SMS send attempt to database
        Matches Perl's sent_sms_log table
        """
        sms_log = SentSmsLog(
            phone_number=phone_number,
            message=message,
            status=status,
            message_id=message_id,
            error_message=error_message,
            created_at=datetime.utcnow()
        )
        db.add(sms_log)
        try:
            await db.commit()
        except Exception as e:
            print(f"Error logging SMS: {e}")
            await db.rollback()
    
    async def send_guardian_invitation_sms(
        self,
        db: AsyncSession,
        phone_number: str,
        guardian_name: str,
        inviter_name: str,
        invitation_link: str
    ) -> Dict[str, Any]:
        """
        Send guardian invitation SMS
        Matches Perl's guardian invitation SMS template
        """
        message = (
            f"Olá {guardian_name}! {inviter_name} te convidou para ser "
            f"guardião(ã) no aplicativo PenhaS. Aceite o convite em: {invitation_link}"
        )
        
        return await self.send_sms(
            db=db,
            phone_number=phone_number,
            message=message
        )
    
    async def send_guardian_alert_sms(
        self,
        db: AsyncSession,
        phone_number: str,
        user_name: str,
        latitude: Optional[str] = None,
        longitude: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send panic alert SMS to guardian
        Matches Perl's panic alert SMS template
        """
        message = f"ALERTA! {user_name} acionou o botão de pânico no PenhaS."
        
        if latitude and longitude:
            maps_url = f"https://maps.google.com/?q={latitude},{longitude}"
            message += f" Localização: {maps_url}"
        
        return await self.send_sms(
            db=db,
            phone_number=phone_number,
            message=message
        )


# Singleton instance
sms_service = SMSService()

