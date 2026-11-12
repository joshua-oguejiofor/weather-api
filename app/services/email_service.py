import logging
from email.message import EmailMessage
from pathlib import Path

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings

logger= logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


env= Environment(
    loader= FileSystemLoader(TEMPLATE_DIR),
    autoescape= select_autoescape(["html", "xml"])
)


class EmailService:
    def __init__(self):
        self.smtp_host= settings.SMTP_HOST
        self.smtp_port= settings.SMTP_PORT
        self.smtp_user= settings.SMTP_USER
        self.smtp_password= settings.SMTP_PASSWORD.get_secret_value()
        self.from_email= settings.EMAILS_FROM

    
    
    def _render_template(self, template_name: str, context: dict) -> str:
        logger.info(f"Rendering template: {template_name}")
        template= env.get_template(template_name)
        return template.render(context)
    
    

    async def send_email(self, to_email: str, subject: str, html_body: str) -> bool:
    
        message = EmailMessage()
        message["From"]= self.from_email,
        message["To"]= to_email
        message["Subject"]= subject
        
        message.set_content(html_body, subtype= "html")
        await aiosmtplib.send(
            message,
            hostname= self.smtp_host,
            port= self.smtp_port,
            username= self.smtp_user,
            password= self.smtp_password,
            start_tls= True,
        )
        return True
    
    
    async def verify_email(self, to_email: str, first_name: str, verify_link: str) -> bool:
        
        html_body= self._render_template(
           template_name= "verify_email.html", 
            context= {"first_name": first_name, "verify_link": verify_link})
        
        return await self.send_email(to_email, "Verify Your Email", html_body)
    
    
    async def send_severe_weather_alert(self, to_email: str, city: str, event: str, description: str, first_name: str) -> bool:
        
        html_body= self._render_template(
            template_name= "severe_weather_alert.html",
            context= {"first_name": first_name, "city": city, "event": event, "description": description}
        )
        return await self.send_email(to_email, f"Weather Alert: {event} in {city}", html_body)
    
    
    async def send_otp_email(self, to_email: str, otp: str) -> bool:
        
        html_body= self._render_template(
            template_name= "otp_email.html",
            context= {"otp": otp}
        )
        return await self.send_email(to_email, "Your OTP Code", html_body)


    async def send_login_notification(self, to_email: str, first_name: str, time: str) -> bool:
        
        html_body= self._render_template(
            template_name= "login_notification.html",
            context= {"first_name": first_name, "time": time}
        )
        return await self.send_email(to_email, "Login Notification", html_body)
