"""
Email service using Resend for sending emails with multi-language support
"""
import os
import resend
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timezone

# Configure Resend
resend.api_key = os.getenv("RESEND_API_KEY")

# Email configuration from environment
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@auth.kgr33n.com")

# Email translations
EMAIL_TRANSLATIONS = {
    "pl": {
        "verification": {
            "subject": "Weryfikacja adresu email - Portfolio KGR33N",
            "header": "Weryfikacja adresu email",
            "greeting": "Cześć {username}!",
            "message": "Dziękujemy za rejestrację. Aby zweryfikować swój adres email, użyj poniższego kodu:",
            "code_validity": "Kod jest ważny przez 15 minut.",
            "verification_link": "Możesz także kliknąć poniższy link, aby przejść bezpośrednio do strony weryfikacji:",
            "button_text": "Weryfikuj Email",
            "manual_link": "Jeśli przycisk nie działa, skopiuj i wklej poniższy link do przeglądarki:",
            "ignore_message": "Jeśli to nie Ty próbowałeś się zarejestrować, zignoruj tę wiadomość.",
            "footer": "© {year} Portfolio KGR33N. Wszystkie prawa zastrzeżone."
        },
        "password_reset": {
            "subject": "Reset hasła - Portfolio KGR33N",
            "header": "Reset hasła",
            "greeting": "Cześć {username}!",
            "message": "Otrzymaliśmy prośbę o zresetowanie hasła do Twojego konta.",
            "instructions": "Aby zresetować hasło, kliknij poniższy przycisk:",
            "button_text": "Resetuj hasło",
            "warning_title": "Uwaga",
            "link_validity": "Link jest ważny przez 30 minut.",
            "ignore_message": "Jeśli to nie Ty prosiłeś o reset hasła, zignoruj tę wiadomość.",
            "manual_copy": "Jeśli przycisk nie działa, skopiuj i wklej poniższy link do przeglądarki",
            "footer": "© {year} Portfolio KGR33N. Wszystkie prawa zastrzeżone."
        },
        "contact_form": {
            "subject": "Formularz kontaktowy: {subject}",
            "header": "Nowa wiadomość z formularza kontaktowego",
            "field_name": "Imię/Nazwa:",
            "field_email": "Email:",
            "field_subject": "Temat:",
            "field_message": "Wiadomość:",
            "sent_at": "Wiadomość wysłana"
        }
    },
    "en": {
        "verification": {
            "subject": "Email Verification - Portfolio KGR33N",
            "header": "Email Verification",
            "greeting": "Hello {username}!",
            "message": "Thank you for registering. To verify your email address, use the code below:",
            "code_validity": "The code is valid for 15 minutes.",
            "verification_link": "You can also click the link below to go directly to the verification page:",
            "button_text": "Verify Email",
            "manual_link": "If the button doesn't work, copy and paste the following link into your browser:",
            "ignore_message": "If you didn't try to register, please ignore this message.",
            "footer": "© {year} Portfolio KGR33N. All rights reserved."
        },
        "password_reset": {
            "subject": "Password Reset - Portfolio KGR33N",
            "header": "Password Reset",
            "greeting": "Hello {username}!",
            "message": "We received a request to reset your account password.",
            "instructions": "To reset your password, click the button below:",
            "button_text": "Reset Password",
            "warning_title": "Warning",
            "link_validity": "This link is valid for 30 minutes.",
            "ignore_message": "If you didn't request a password reset, please ignore this message.",
            "manual_copy": "If the button doesn't work, copy and paste the following link into your browser",
            "footer": "&copy; {year} Portfolio KGR33N. All rights reserved."
        },
        "contact_form": {
            "subject": "Contact Form: {subject}",
            "header": "New message from contact form",
            "field_name": "Name:",
            "field_email": "Email:",
            "field_subject": "Subject:",
            "field_message": "Message:",
            "sent_at": "Message sent"
        }
    }
}

def get_translation(language: str, email_type: str, key: str) -> str:
    """Get translation for a specific key"""
    lang = language if language in EMAIL_TRANSLATIONS else "en"  # Default to English
    return EMAIL_TRANSLATIONS.get(lang, {}).get(email_type, {}).get(key, "")

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
    def get_user_language_from_request(request=None, user=None) -> str:
        """Determine user's preferred language from request headers or user preferences"""
        # Priority: 1. User preference (if user is logged in), 2. Accept-Language header, 3. Default
        
        # Check if user has a preferred language (future feature)
        if user and hasattr(user, 'preferred_language') and user.preferred_language:
            return user.preferred_language
        
        # Check Accept-Language header
        if request and hasattr(request, 'headers'):
            accept_language = request.headers.get('Accept-Language', '')
            if 'pl' in accept_language.lower():
                return 'pl'
            elif 'en' in accept_language.lower():
                return 'en'
        
        # Default to Polish (since it's a Polish portfolio)
        return 'pl'
    
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
            # Implementacja zgodna z działającym endpointem
            params: resend.Emails.SendParams = {
                "from": f"KGR33N <{FROM_EMAIL}>",
                "to": message.to,
                "subject": message.subject,
                "html": message.html,
            }
            
            print(f"🚀 Sending email to {message.to} from {FROM_EMAIL}")
            
            # Wyślij email - dokładnie jak w działającym endpoincie
            email: resend.Email = resend.Emails.send(params)
            
            print(f"✅ Email sent successfully to {message.to}: {email}")
            return {
                "success": True,
                "message": "Email sent successfully",
                "id": str(email) if email else "unknown"
            }
            
        except Exception as e:
            print(f"❌ Failed to send email to {message.to}: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to send email: {str(e)}",
                "id": None
            }
    
    @staticmethod
    async def send_verification_email(
        email: str, 
        verification_code: str, 
        username: str, 
        language: str = "pl"
    ) -> dict:
        """Send email verification code in specified language"""
        
        print(f"🔄 Starting send_verification_email for {email}")
        
        # Get translations
        t = EMAIL_TRANSLATIONS.get(language, EMAIL_TRANSLATIONS["en"])["verification"]
        
        print(f"📝 Got translations for language: {language}")
        
        # Create verification link
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:4321")
        verification_link = f"{frontend_url}/{language}/verify-email?email={email}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{t["subject"]}</title>
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
                .button {{
                    display: inline-block;
                    background: #2563eb;
                    color: white !important;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                    font-weight: bold;
                    text-shadow: none;
                    font-size: 16px;
                    border: 2px solid #2563eb;
                }}
                .button:hover {{
                    background: #1d4ed8;
                    color: white !important;
                    border-color: #1d4ed8;
                }}
                .link {{
                    color: #2563eb;
                    word-break: break-all;
                    font-size: 14px;
                    background: #f3f4f6;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
                .footer {{ padding: 20px; text-align: center; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Portfolio KGR33N</h1>
                    <p>{t["header"]}</p>
                </div>
                <div class="content">
                    <h2>{t["greeting"].format(username=username)}</h2>
                    <p>{t["message"]}</p>
                    <div class="code">{verification_code}</div>
                    <p>{t["code_validity"]}</p>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                    
                    <p>{t["verification_link"]}</p>
                    <div style="text-align: center;">
                        <a href="{verification_link}" class="button">{t["button_text"]}</a>
                    </div>
                    
                    <p>{t["manual_link"]}</p>
                    <div class="link">{verification_link}</div>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                    
                    <p>{t["ignore_message"]}</p>
                </div>
                <div class="footer">{t["footer"].format(year=datetime.now(timezone.utc).year)}</div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Portfolio KGR33N - {t["header"]}
        
        {t["greeting"].format(username=username)}
        
        {t["message"]}
        
        {verification_code}
        
        {t["code_validity"]}
        
        {t["verification_link"]}
        {verification_link}
        
        {t["ignore_message"]}
        
        {t["footer"].format(year=datetime.now(timezone.utc).year)}
        """
        
        print(f"📧 Creating EmailMessage for {email}")
        
        message = EmailMessage(
            to=[email],
            subject=t["subject"],
            html=html_content,
            text=text_content
        )
        
        print(f"📤 Calling send_email...")
        result = await EmailService.send_email(message)
        print(f"📬 send_email returned: {result}")
        
        return result
    
    @staticmethod
    async def send_password_reset_email(
        email: str, 
        reset_token: str, 
        username: str, 
        language: str = "pl"
    ) -> dict:
        """Send password reset email in specified language"""
        
        # Get translations
        t = EMAIL_TRANSLATIONS.get(language, EMAIL_TRANSLATIONS["en"])["password_reset"]
        print(f"🔄 Starting send_password_reset_email for {email} in {language}")
        # Include language in URL path (consistent with verification)
        reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:4321')}/{language}/reset-password?token={reset_token}&email={email}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{t["subject"]}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #dc2626; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .button {{ 
                    display: inline-block; 
                    background: #2563eb; 
                    color: white !important; 
                    padding: 12px 30px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0;
                    font-weight: bold;
                    text-shadow: none;
                    font-size: 16px;
                    border: 2px solid #2563eb;
                }}
                .button:hover {{ 
                    background: #1d4ed8; 
                    color: white !important;
                    border-color: #1d4ed8;
                }}
                .footer {{ padding: 20px; text-align: center; color: #666; }}
                .warning {{ background: #fef3c7; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Portfolio KGR33N</h1>
                    <p>{t["header"]}</p>
                </div>
                <div class="content">
                    <h2>{t["greeting"].format(username=username)}</h2>
                    <p>{t["message"]}</p>
                    <p>{t["instructions"]}</p>
                    <p style="text-align: center;">
                        <a href="{reset_url}" class="button">{t["button_text"]}</a>
                    </p>
                    <div class="warning">
                        <strong>{t["warning_title"]}:</strong> {t["link_validity"]} {t["ignore_message"]}
                    </div>
                    <p>{t["manual_copy"]}:</p>
                    <p style="word-break: break-all; color: #666;">{reset_url}</p>
                </div>
                <div class="footer">
                    <p>{t["footer"].format(year=datetime.now(timezone.utc).year)}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Portfolio KGR33N - {t["header"]}
        
        {t["greeting"].format(username=username)}
        
        {t["message"]}
        
        {t["instructions"]}
        {reset_url}
        
        {t["warning_title"]}: {t["link_validity"]} {t["ignore_message"]}
        
        {t["footer"].format(year=datetime.now(timezone.utc).year)}
        """
        
        message = EmailMessage(
            to=[email],
            subject=t["subject"],
            html=html_content,
            text=text_content
        )
        
        return await EmailService.send_email(message)
    
    @staticmethod
    async def send_contact_form_email(
        name: str, 
        email: str, 
        subject: str, 
        message: str, 
        language: str = "pl"
    ) -> dict:
        """Send contact form email in specified language"""
        
        # Get translations
        t = EMAIL_TRANSLATIONS.get(language, EMAIL_TRANSLATIONS["en"])["contact_form"]
        
        admin_email = os.getenv("ADMIN_EMAIL", FROM_EMAIL)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{t["header"]}</title>
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
                    <p>{t["header"]}</p>
                </div>
                <div class="content">
                    <div class="field">
                        <div class="label">{t["field_name"]}</div>
                        <div class="value">{name}</div>
                    </div>
                    <div class="field">
                        <div class="label">{t["field_email"]}</div>
                        <div class="value">{email}</div>
                    </div>
                    <div class="field">
                        <div class="label">{t["field_subject"]}</div>
                        <div class="value">{subject}</div>
                    </div>
                    <div class="field">
                        <div class="label">{t["field_message"]}</div>
                        <div class="message-content">{message.replace(chr(10), '<br>')}</div>
                    </div>
                    <p style="color: #666; font-size: 14px; margin-top: 30px;">
                        {t["sent_at"]}: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        message_obj = EmailMessage(
            to=[admin_email],
            subject=t["subject"].format(subject=subject),
            html=html_content,
            reply_to=email
        )
        
        return await EmailService.send_email(message_obj)


