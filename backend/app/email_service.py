"""
Email service using Resend for sending emails
"""
import os
import resend
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

# Configure Resend
resend.api_key = os.getenv("RESEND_API_KEY")

# Email configuration from environment
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@localhost")
FROM_NAME = os.getenv("FROM_NAME", "Portfolio KGR33N")

class EmailMessage(BaseModel):
    """Email message structure"""
    to: List[str]
    subject: str
    html: str
    text: Optional[str] = None
    reply_to: Optional[str] = None

class EmailService:
    """Service for sending emails using Resend"""
    
    @staticmethod
    def is_configured() -> bool:
        """Check if email service is properly configured"""
        api_key = os.getenv("RESEND_API_KEY")
        return api_key is not None and api_key != "re_your_api_key_here_change_this"
    
    @staticmethod
    async def send_email(message: EmailMessage) -> dict:
        """Send email using Resend"""
        if not EmailService.is_configured():
            print("⚠️  Email service not configured - email would be sent to:", message.to)
            return {
                "success": False,
                "message": "Email service not configured",
                "id": "dev-mode-no-send"
            }
        
        try:
            params = {
                "from": f"{FROM_NAME} <{FROM_EMAIL}>",
                "to": message.to,
                "subject": message.subject,
                "html": message.html,
            }
            
            # Add optional fields
            if message.text:
                params["text"] = message.text
            if message.reply_to:
                params["reply_to"] = message.reply_to
            
            response = resend.Emails.send(params)
            
            print(f"✅ Email sent successfully to {message.to}: {response}")
            return {
                "success": True,
                "message": "Email sent successfully",
                "id": response.get("id", "unknown")
            }
            
        except Exception as e:
            print(f"❌ Failed to send email to {message.to}: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to send email: {str(e)}",
                "id": None
            }
    
    @staticmethod
    async def send_verification_email(email: str, verification_code: str, username: str) -> dict:
        """Send email verification code"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Weryfikacja adresu email</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2563eb; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .code {{ 
                    font-size: 24px; 
                    font-weight: bold; 
                    background: #e5e7eb; 
                    padding: 15px; 
                    text-align: center; 
                    margin: 20px 0; 
                    border-radius: 5px;
                    letter-spacing: 2px;
                }}
                .footer {{ padding: 20px; text-align: center; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Portfolio KGR33N</h1>
                    <p>Weryfikacja adresu email</p>
                </div>
                <div class="content">
                    <h2>Cześć {username}!</h2>
                    <p>Dziękujemy za rejestrację. Aby zweryfikować swój adres email, użyj poniższego kodu:</p>
                    <div class="code">{verification_code}</div>
                    <p>Kod jest ważny przez 15 minut.</p>
                    <p>Jeśli to nie Ty próbowałeś się zarejestrować, zignoruj tę wiadomość.</p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.now().year} Portfolio KGR33N. Wszystkie prawa zastrzeżone.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Portfolio KGR33N - Weryfikacja adresu email
        
        Cześć {username}!
        
        Dziękujemy za rejestrację. Aby zweryfikować swój adres email, użyj poniższego kodu:
        
        {verification_code}
        
        Kod jest ważny przez 15 minut.
        
        Jeśli to nie Ty próbowałeś się zarejestrować, zignoruj tę wiadomość.
        
        © {datetime.now().year} Portfolio KGR33N. Wszystkie prawa zastrzeżone.
        """
        
        message = EmailMessage(
            to=[email],
            subject="Weryfikacja adresu email - Portfolio KGR33N",
            html=html_content,
            text=text_content
        )
        
        return await EmailService.send_email(message)
    
    @staticmethod
    async def send_password_reset_email(email: str, reset_token: str, username: str) -> dict:
        """Send password reset email"""
        reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:4321')}/auth/reset-password?token={reset_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Reset hasła</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #dc2626; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .button {{ 
                    display: inline-block; 
                    background: #2563eb; 
                    color: white; 
                    padding: 12px 30px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0;
                }}
                .footer {{ padding: 20px; text-align: center; color: #666; }}
                .warning {{ background: #fef3c7; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Portfolio KGR33N</h1>
                    <p>Reset hasła</p>
                </div>
                <div class="content">
                    <h2>Cześć {username}!</h2>
                    <p>Otrzymaliśmy prośbę o zresetowanie hasła do Twojego konta.</p>
                    <p>Aby zresetować hasło, kliknij poniższy przycisk:</p>
                    <p style="text-align: center;">
                        <a href="{reset_url}" class="button">Resetuj hasło</a>
                    </p>
                    <div class="warning">
                        <strong>Uwaga:</strong> Link jest ważny przez 1 godzinę. Jeśli to nie Ty prosiłeś o reset hasła, zignoruj tę wiadomość.
                    </div>
                    <p>Jeśli przycisk nie działa, skopiuj i wklej poniższy link do przeglądarki:</p>
                    <p style="word-break: break-all; color: #666;">{reset_url}</p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.now().year} Portfolio KGR33N. Wszystkie prawa zastrzeżone.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Portfolio KGR33N - Reset hasła
        
        Cześć {username}!
        
        Otrzymaliśmy prośbę o zresetowanie hasła do Twojego konta.
        
        Aby zresetować hasło, odwiedź poniższy link:
        {reset_url}
        
        UWAGA: Link jest ważny przez 1 godzinę. Jeśli to nie Ty prosiłeś o reset hasła, zignoruj tę wiadomość.
        
        © {datetime.now().year} Portfolio KGR33N. Wszystkie prawa zastrzeżone.
        """
        
        message = EmailMessage(
            to=[email],
            subject="Reset hasła - Portfolio KGR33N",
            html=html_content,
            text=text_content
        )
        
        return await EmailService.send_email(message)
    
    @staticmethod
    async def send_contact_form_email(name: str, email: str, subject: str, message: str) -> dict:
        """Send contact form email"""
        admin_email = os.getenv("ADMIN_EMAIL", FROM_EMAIL)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Nowa wiadomość z formularza kontaktowego</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #059669; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .field {{ margin: 15px 0; }}
                .label {{ font-weight: bold; color: #374151; }}
                .value {{ background: white; padding: 10px; border-radius: 3px; margin-top: 5px; }}
                .message-content {{ background: white; padding: 15px; border-radius: 5px; border-left: 4px solid #059669; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Portfolio KGR33N</h1>
                    <p>Nowa wiadomość z formularza kontaktowego</p>
                </div>
                <div class="content">
                    <div class="field">
                        <div class="label">Imię/Nazwa:</div>
                        <div class="value">{name}</div>
                    </div>
                    <div class="field">
                        <div class="label">Email:</div>
                        <div class="value">{email}</div>
                    </div>
                    <div class="field">
                        <div class="label">Temat:</div>
                        <div class="value">{subject}</div>
                    </div>
                    <div class="field">
                        <div class="label">Wiadomość:</div>
                        <div class="message-content">{message.replace(chr(10), '<br>')}</div>
                    </div>
                    <p style="color: #666; font-size: 14px; margin-top: 30px;">
                        Wiadomość wysłana: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        message_obj = EmailMessage(
            to=[admin_email],
            subject=f"Formularz kontaktowy: {subject}",
            html=html_content,
            reply_to=email
        )
        
        return await EmailService.send_email(message_obj)
