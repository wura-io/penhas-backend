"""
Email sending service with HTML templates
Port from Perl email functionality
Supports SMTP with HTML email templates from public/email-templates/
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from pathlib import Path
from jinja2 import Template

from app.core.config import settings


class EmailService:
    """
    Email sending service
    Matches Perl's email sending functionality
    """
    
    def __init__(self):
        # SMTP Configuration
        self.smtp_host = getattr(settings, 'SMTP_HOST', 'localhost')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_user = getattr(settings, 'SMTP_USER', None)
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', None)
        self.smtp_from = getattr(settings, 'SMTP_FROM', 'noreply@penhas.app.br')
        self.smtp_from_name = getattr(settings, 'SMTP_FROM_NAME', 'PenhaS')
        self.smtp_tls = getattr(settings, 'SMTP_TLS', True)
        
        # Template directory
        self.template_dir = Path(__file__).parent.parent.parent / "api" / "public" / "email-templates"
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email via SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text fallback (optional)
            
        Returns:
            Dict with send result:
            - success: bool
            - error: str (if failed)
        """
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['From'] = f"{self.smtp_from_name} <{self.smtp_from}>"
            message['To'] = to_email
            message['Subject'] = subject
            
            # Add plain text part if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                message.attach(text_part)
            
            # Add HTML part
            html_part = MIMEText(html_content, 'html', 'utf-8')
            message.attach(html_part)
            
            # Send via SMTP
            if self.smtp_tls:
                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_user,
                    password=self.smtp_password,
                    start_tls=True
                )
            else:
                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_user,
                    password=self.smtp_password
                )
            
            return {"success": True}
            
        except Exception as e:
            print(f"Email send error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _load_template(self, template_name: str) -> Optional[str]:
        """
        Load HTML email template from disk
        
        Args:
            template_name: Template filename (e.g., 'forgot_password.html')
            
        Returns:
            Template content as string
        """
        template_path = self.template_dir / template_name
        
        if not template_path.exists():
            print(f"Email template not found: {template_path}")
            return None
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading email template: {e}")
            return None
    
    def _render_template(self, template_content: str, variables: Dict[str, Any]) -> str:
        """
        Render template with Jinja2
        
        Args:
            template_content: HTML template string
            variables: Dict of variables to substitute
            
        Returns:
            Rendered HTML string
        """
        template = Template(template_content)
        return template.render(**variables)
    
    async def send_forgot_password_email(
        self,
        to_email: str,
        nome: str,
        reset_token: str
    ) -> Dict[str, Any]:
        """
        Send password reset email
        Matches Perl's forgot_password.html template
        """
        template_content = self._load_template('forgot_password.html')
        
        if not template_content:
            return {"success": False, "error": "Template not found"}
        
        # Build reset URL
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        html_content = self._render_template(template_content, {
            'nome': nome,
            'reset_url': reset_url,
            'token': reset_token
        })
        
        return await self.send_email(
            to_email=to_email,
            subject="Recuperação de senha - PenhaS",
            html_content=html_content
        )
    
    async def send_account_deletion_email(
        self,
        to_email: str,
        nome: str,
        deletion_date: str
    ) -> Dict[str, Any]:
        """
        Send account deletion confirmation email
        Matches Perl's account_deletion.html template
        """
        template_content = self._load_template('account_deletion.html')
        
        if not template_content:
            return {"success": False, "error": "Template not found"}
        
        html_content = self._render_template(template_content, {
            'nome': nome,
            'deletion_date': deletion_date
        })
        
        return await self.send_email(
            to_email=to_email,
            subject="Confirmação de exclusão de conta - PenhaS",
            html_content=html_content
        )
    
    async def send_account_reactivate_email(
        self,
        to_email: str,
        nome: str
    ) -> Dict[str, Any]:
        """
        Send account reactivation email
        Matches Perl's account_reactivate.html template
        """
        template_content = self._load_template('account_reactivate.html')
        
        if not template_content:
            return {"success": False, "error": "Template not found"}
        
        html_content = self._render_template(template_content, {
            'nome': nome
        })
        
        return await self.send_email(
            to_email=to_email,
            subject="Conta reativada - PenhaS",
            html_content=html_content
        )
    
    async def send_circulo_penhas_invite_email(
        self,
        to_email: str,
        nome: str,
        badge_name: str,
        acceptance_url: str
    ) -> Dict[str, Any]:
        """
        Send Círculo Penhas badge invitation email
        Matches Perl's circulo_penhas_invite.html template
        """
        template_content = self._load_template('circulo_penhas_invite.html')
        
        if not template_content:
            return {"success": False, "error": "Template not found"}
        
        html_content = self._render_template(template_content, {
            'nome': nome,
            'badge_name': badge_name,
            'acceptance_url': acceptance_url
        })
        
        return await self.send_email(
            to_email=to_email,
            subject=f"Convite: {badge_name} - Círculo Penhas",
            html_content=html_content
        )
    
    async def send_ponto_apoio_sugestao_email(
        self,
        to_email: str,
        ponto_apoio_name: str,
        user_nome: str
    ) -> Dict[str, Any]:
        """
        Send support point suggestion notification email
        Matches Perl's ponto_apoio_sugestao.html template
        """
        template_content = self._load_template('ponto_apoio_sugestao.html')
        
        if not template_content:
            return {"success": False, "error": "Template not found"}
        
        html_content = self._render_template(template_content, {
            'ponto_apoio_name': ponto_apoio_name,
            'user_nome': user_nome
        })
        
        return await self.send_email(
            to_email=to_email,
            subject="Nova sugestão de ponto de apoio - PenhaS",
            html_content=html_content
        )


# Singleton instance
email_service = EmailService()

